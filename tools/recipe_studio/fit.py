"""Bounded SciPy fitting, CIEDE2000 reporting, explicit unsupported coverage."""
import numpy as np
from scipy.optimize import least_squares
from skimage.color import rgb2lab, deltaE_ciede2000, rgb2hsv, hsv2rgb
from .model import Model, coordinates, weights
from .recipe import SECTORS, neutral, validate, vector, from_vector

NAMES = ([f"hue.{s}" for s in SECTORS] + [f"saturation.{s}" for s in SECTORS] +
         [f"lightness.{s}" for s in SECTORS] +
         ["tone.shadows", "tone.midtones", "tone.highlights", "shading"])


def limits(cal):
    return np.array([cal["limits"][k] for k in ("hue", "saturation", "lightness")
                     for _ in range(12)] + [cal["limits"]["tone"]] * 3 + [cal["limits"]["shading"]])


def metric(a, b):
    return deltaE_ciede2000(rgb2lab(np.clip(a, 0, 1)), rgb2lab(np.clip(b, 0, 1)))


def error_summary(a, b):
    d = metric(a, b)
    return {"mean_delta_e_2000": float(np.mean(d)), "p95_delta_e_2000": float(np.percentile(d, 95)),
            "count": int(d.size)}


def sector_report(base, a, b, cal):
    hsv = rgb2hsv(base)
    w = weights(hsv[..., 0], cal)
    labels = w.argmax(axis=-1)
    d = metric(a, b)
    result = {}
    for i, name in enumerate(SECTORS):
        use = (labels == i) & (hsv[..., 1] >= cal["neutral_chroma_threshold"])
        n = int(use.sum())
        result[name] = {"count": n, "mean_delta_e_2000": float(d[use].mean()) if n else None,
                        "p95_delta_e_2000": float(np.percentile(d[use], 95)) if n else None,
                        "coverage": "sampled" if n >= 8 else "insufficient"}
    return result


def sample_indices(size, count, seed):
    rng = np.random.default_rng(seed)
    return rng.choice(size, size=min(count, size), replace=False)


def _residual(a, target_lab):
    lab = rgb2lab(a)
    diff = lab - target_lab
    de = deltaE_ciede2000(lab, target_lab)
    # Three signed residuals whose squared sum is exactly deltaE00 squared.
    scale = de / np.maximum(np.linalg.norm(diff, axis=-1), 1e-12)
    return (diff * scale[..., None]).ravel()


def _solve(base, target, xy, cal, initial, active, max_nfev, progress=None):
    model = Model(base, cal, xy)
    x0 = np.array(vector(initial), float)
    bound = limits(cal)
    target_lab = rgb2lab(target)
    calls = 0

    def objective(x):
        nonlocal calls
        calls += 1
        v = x0.copy()
        v[active] = x
        if progress and calls % 50 == 0:
            progress({"evaluations": calls})
        return _residual(model.apply(v), target_lab)

    result = least_squares(objective, x0[active], bounds=(-bound[active], bound[active]),
                           max_nfev=max_nfev, loss="soft_l1", f_scale=2, x_scale="jac",
                           ftol=1e-6, xtol=1e-6, gtol=1e-6)
    continuous = x0.copy()
    continuous[active] = result.x
    rounded = np.rint(continuous)
    # Integer coordinate polish scores the actual deployable recipe, not floats.
    def score(v):
        return float(np.mean(metric(model.apply(v), target)))
    best = score(rounded)
    for _ in range(2):
        improved = False
        for idx in active:
            chosen = rounded[idx]
            for delta in (-1, 1):
                trial = rounded.copy()
                trial[idx] += delta
                if abs(trial[idx]) > bound[idx]:
                    continue
                value = score(trial)
                if value + 1e-9 < best:
                    best, chosen, improved = value, trial[idx], True
            rounded[idx] = chosen
        if not improved:
            break
    return rounded, {"converged": bool(result.success), "solver_message": result.message,
                     "residual_calls": calls, "function_evaluations": result.nfev,
                     "train_mean_delta_e_2000": best}


def fit_pair(base, target, cal, initial=None, max_nfev=100, sample_count=768,
             progress=None, active_names=None):
    if base.shape != target.shape or base.ndim != 3:
        raise ValueError("成对照片必须同尺寸、同方向、同裁切且已对齐；本工具不自动配准")
    if not 5 <= max_nfev <= 300 or not 64 <= sample_count <= 4096:
        raise ValueError("拟合预算需为 5…300 次、64…4096 个采样点")
    initial = validate(initial or neutral("自动拟合起点"), cal)
    size = base.shape[0] * base.shape[1]
    if size < 64:
        raise ValueError("图像太小，至少需要 64 个像素")
    ix = sample_indices(size, sample_count * 2, 26)
    train, holdout = ix[::2], ix[1::2]
    b, t, xy = base.reshape(-1, 3), target.reshape(-1, 3), coordinates(base.shape).reshape(-1, 2)
    w = weights(rgb2hsv(b[train])[..., 0], cal)
    chromatic = rgb2hsv(b[train])[..., 1] >= cal["neutral_chroma_threshold"]
    covered = ((w > 0.5) & chromatic[:, None]).sum(axis=0) >= 3
    active = [i for i in range(40) if i >= 36 or covered[i % 12]]
    if active_names is not None:
        if not active_names or set(active_names) - set(NAMES):
            raise ValueError("未知或空的拟合参数名")
        active = [i for i in active if NAMES[i] in active_names]
    if not active:
        raise ValueError("源图未覆盖所选色区，不能拟合")
    v, solver = _solve(b[train], t[train], xy[train], cal, initial, active, max_nfev, progress)
    recipe = validate(from_vector(v, initial), cal)
    pred = Model(b[holdout], cal, xy[holdout]).apply(v)
    summary = error_summary(pred, t[holdout])
    mean, p95 = summary["mean_delta_e_2000"], summary["p95_delta_e_2000"]
    quality = "差"
    for i, label in ((1, "近似"), (0, "好")):
        if mean <= cal["quality_mean_delta_e"][i] and p95 <= cal["quality_p95_delta_e"][i]:
            quality = label
    regions = sector_report(b[holdout], pred, t[holdout], cal)
    warnings = ["质量仅衡量此近似模型对目标的拟合，不保证相机 JPEG 一致",
                "同尺寸不能证明照片对齐；请手动确认机位、裁切、曝光与场景一致",
                "不支持单一色区内部任意变化、局部蒙版、颗粒、模糊、锐化或空间位移"]
    if not all(covered):
        warnings.append("部分色区样本不足，保留初值；未观测参数不是已验证的中性值")
    if not solver["converged"]:
        warnings.append("达到拟合预算或未收敛；当前结果只作起点")
        if quality == "好":
            quality = "近似"
    hit = [NAMES[i] for i, x in enumerate(v) if abs(x) == limits(cal)[i]]
    if hit:
        warnings.append("部分参数达到边界；目标可能超出可表达范围")
    return recipe, {"format": "ep7-fit-report-v1", "mode": "aligned-pair-or-lut",
                    "quality": quality, "calibration_id": cal["id"], "solver": solver,
                    "validation_pixels": summary, "per_sector": regions,
                    "unobserved_sectors": [SECTORS[i] for i, x in enumerate(covered) if not x],
                    "at_bounds": hit, "warnings": warnings,
                    "validation_scope": "Held-out pixels in this image; not an independent scene or camera validation"}


def distribution_swatches(rgb, cal):
    """Per-hue circular mean H and S/V quantiles; scene content remains a confound."""
    a = rgb.reshape(-1, 3)
    a = a[sample_indices(len(a), 50000, 27)]
    hsv = rgb2hsv(a)
    labels = weights(hsv[:, 0], cal).argmax(axis=-1)
    result = {}
    for i in range(12):
        use = (labels == i) & (hsv[:, 1] > cal["neutral_chroma_threshold"])
        if use.sum() < 16:
            continue
        h = np.angle(np.exp(2j * np.pi * hsv[use, 0]).mean()) / (2 * np.pi) % 1
        quantiles = np.quantile(hsv[use, 1:], [0.1, 0.5, 0.9], axis=0)
        result[i] = hsv2rgb(np.column_stack((np.full(3, h), quantiles)))
    return result


def fit_reference(base, reference, cal, initial=None, max_nfev=80, progress=None):
    if not 5 <= max_nfev <= 300:
        raise ValueError("拟合预算必须为 5…300 次")
    source, target = distribution_swatches(base, cal), distribution_swatches(reference, cal)
    common = sorted(set(source) & set(target))
    if not common:
        raise ValueError("参考图与基准图没有足够的共同色区；请换参考图")
    b, t = np.concatenate([source[i] for i in common]), np.concatenate([target[i] for i in common])
    active = [j * 12 + i for j in range(3) for i in common] + [36, 37, 38]
    initial = validate(initial or neutral("异场景粗略起点"), cal)
    # Spatial shading is not identifiable across scenes; leave its initial value untouched.
    xy = np.zeros((len(b), 2))
    v, solver = _solve(b, t, xy, cal, initial, active, max_nfev, progress)
    pred = Model(b, cal, xy).apply(v)
    summary = error_summary(pred, t)
    return validate(from_vector(v, initial), cal), {
        "format": "ep7-fit-report-v1", "mode": "different-scene-distribution",
        "quality": "近似" if summary["mean_delta_e_2000"] < cal["quality_mean_delta_e"][1] else "差",
        "distribution_swatches_only": summary, "per_sector": sector_report(b, pred, t, cal),
        "common_sectors": [SECTORS[i] for i in common], "solver": solver,
        "calibration_id": cal["id"],
        "warnings": ["仅按共同色区的 H 圆均值及 S/V 10/50/90 分位分布匹配，无法分离场景内容与风格",
                     "此 ΔE 是统计色块误差，不是成对照片误差；无独立验证，不评为好",
                     "暗角不可从不同场景辨识，保持初值；未覆盖色区保持初值",
                     "空间效果、局部变化、颗粒和不同照明不能由这套参数完整表达"]}
