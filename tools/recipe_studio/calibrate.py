"""Fit a declared RAW-to-JPEG baseline and observable effect gains locally."""
import copy
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from skimage.color import rgb2lab
from .fit import _residual, error_summary, sample_indices, sector_report
from .images import read_image
from .model import Model, coordinates, raw_baseline
from .recipe import calibration, load_json, neutral, validate, vector

GAINS = ("hue_degrees_per_step", "saturation_log_gain_per_step", "lightness_gain",
         "tone_gain_per_step", "shading_gain")


def calibrate(manifest_path, current=None, max_nfev=80):
    path = Path(manifest_path).resolve()
    manifest = load_json(path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or set(manifest) != {"format", "pairs"} or
            manifest["format"] != "ep7-calibration-pairs-v1" or
            not isinstance(manifest["pairs"], list) or not manifest["pairs"]):
        raise ValueError("需要 ep7-calibration-pairs-v1 和非空 pairs")
    if len(manifest["pairs"]) > 30:
        raise ValueError("一次最多 30 对；请挑选有代表性的校准与验证场景")
    cal = copy.deepcopy(current or calibration())
    cases = []
    for pair in manifest["pairs"]:
        if (not isinstance(pair, dict) or set(pair) - {"raw", "jpeg", "recipe", "split", "raw_crop", "jpeg_crop"} or
                not {"raw", "jpeg"} <= set(pair) or pair.get("split", "train") not in ("train", "validation")):
            raise ValueError("pair 需要 raw/jpeg，允许 recipe 和 train/validation split")
        if any(not isinstance(pair[k], str) or not pair[k].strip()
               for k in ("raw", "jpeg", "recipe") if k in pair):
            raise ValueError("raw/jpeg/recipe 必须是非空本地文件路径")
        source_path, target_path = path.parent / pair["raw"], path.parent / pair["jpeg"]
        if source_path.suffix.lower() != ".orf":
            raise ValueError("校准源必须为 ORF；不能把已显影 JPEG 冒充 RAW")
        base, info = read_image(source_path, max_side=640, crop=pair.get("raw_crop"))
        target, target_info = read_image(target_path, max_side=640, crop=pair.get("jpeg_crop"))
        if info["aligned_shape"] != target_info["aligned_shape"] or base.shape != target.shape:
            raise ValueError("RAW/JPEG 必须同尺寸、方向与裁切；需事先在本地配准，不能缩放掩盖差异")
        r = neutral()
        if pair.get("recipe"):
            r = validate(load_json((path.parent / pair["recipe"]).read_text(encoding="utf-8")), cal)
        idx = sample_indices(base.shape[0] * base.shape[1], 512, 39)
        cases.append((base.reshape(-1, 3)[idx], target.reshape(-1, 3)[idx],
                      coordinates(base.shape).reshape(-1, 2)[idx], np.array(vector(r)),
                      pair.get("split", "train")))
    return fit_calibration_cases(cases, cal, max_nfev)


def fit_calibration_cases(cases, cal, max_nfev=80):
    """Numerical kernel also tested with owned synthetic RAW-development data."""
    if not 5 <= max_nfev <= 300:
        raise ValueError("校准预算必须为 5…300 次")
    train = [c for c in cases if c[4] == "train"]
    holdout = [c for c in cases if c[4] == "validation"]
    if not train or not any(not np.any(c[3]) for c in train):
        raise ValueError("至少需要一对已知中性配方的 train 数据，才能把基线和效果分开")
    allv = np.stack([c[3] for c in train])
    observed = [bool(np.any(allv[:, sl])) for sl in
                (slice(0, 12), slice(12, 24), slice(24, 36), slice(36, 39), slice(39, 40))]
    active = [i for i, yes in enumerate(observed) if yes]
    x0 = np.array(cal["raw_rgb_gain"] + [cal["raw_gamma"]] + [cal[GAINS[i]] for i in active])
    lo = [0.5, 0.5, 0.5, 0.5] + [[-12, 0.01, 0.1, 0.002, 0.05][i] for i in active]
    hi = [2, 2, 2, 2] + [[-0.1, 0.4, 2, 0.08, 1][i] for i in active]

    def unpack(x):
        c = copy.deepcopy(cal)
        c["raw_rgb_gain"], c["raw_gamma"] = x[:3].tolist(), float(x[3])
        for j, i in enumerate(active):
            c[GAINS[i]] = float(x[4 + j])
        return c

    def predict(case, c):
        b, _, xy, v, _ = case
        return Model(raw_baseline(b, c), c, xy).apply(v)

    def objective(x):
        c = unpack(x)
        return np.concatenate([_residual(predict(case, c), rgb2lab(case[1])) for case in train])

    result = least_squares(objective, x0, bounds=(lo, hi), max_nfev=max_nfev,
                           loss="soft_l1", f_scale=2, x_scale="jac")
    rank = int(np.linalg.matrix_rank(result.jac))
    if rank < len(x0):
        raise ValueError("校准数据不能独立约束所选增益；请增加颜色/亮度/位置覆盖或独立已知配方")
    updated = unpack(result.x)
    updated["status"] = "locally-fitted"
    # Stable ID records model content; no personal file names or EXIF included.
    import hashlib
    import json
    updated["id"] = "local-" + hashlib.sha256(json.dumps(
        {k: updated[k] for k in ("raw_rgb_gain", "raw_gamma", *GAINS)}, sort_keys=True).encode()).hexdigest()[:16]
    before, after = [], []
    for case in cases:
        before.append(error_summary(predict(case, cal), case[1]))
        after.append(error_summary(predict(case, updated), case[1]))
    report = {"format": "ep7-calibration-report-v1", "converged": bool(result.success),
              "function_evaluations": result.nfev, "calibration_id": updated["id"],
              "trained_effect_gains": [GAINS[i] for i in active],
              "unobserved_effect_gains": [GAINS[i] for i in range(5) if i not in active],
              "pairs": [{"split": case[4], "before": b, "after": a,
                         "per_sector_after": sector_report(raw_baseline(case[0], updated),
                                                            predict(case, updated), case[1], updated)}
                        for case, b, a in zip(cases, before, after)],
              "jacobian_rank": rank, "fitted_parameters": len(x0),
              "independent_validation_pairs": len(holdout),
              "warnings": ["只拟合 RAW 显影的 RGB 增益/gamma 与有已知非零配方的全局效果增益",
                           "无非零配方时不会声称校准 H/S/L、影调或暗角；不自动学习色区边界或真实 ISP",
                           "必须同 WB、曝光、镜头、裁切与配方；Natural 与 COLOR 默认差异需分别建模"]}
    if not holdout:
        report["warnings"].append("没有独立 validation 场景，只有训练误差，不能证明泛化")
    if not result.success:
        raise ValueError("校准达到预算而未收敛；未发布更新。请增加预算或改善配对数据")
    return updated, report
