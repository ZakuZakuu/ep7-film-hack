"""Deterministic photo-independent display-sRGB fitting."""
import numpy as np
from skimage.color import rgb2lab, lab2rgb
from .lut import apply_lut
from .fit import fit_pair, NAMES, error_summary, sector_report, limits, metric
from .backend import Model
from .recipe import neutral, vector, from_vector


def representative_colors(photo=None):
    rng = np.random.default_rng(751)
    axis = np.linspace(0, 1, 17)
    grid = np.stack(np.meshgrid(axis, axis, axis, indexing="ij"), -1).reshape(-1, 3)
    gray = np.repeat(np.linspace(.02, .98, 256)[:, None], 3, axis=1)
    # Original layout using public CSS named colors plus six neutral patches.
    chart = np.concatenate((np.repeat(np.linspace(.1,.9,6)[:,None],3,1),
                            np.array([[255,0,0],[0,128,0],[0,0,255],[255,255,0],[0,255,255],
                                      [255,0,255],[255,165,0],[128,0,128],[255,192,203],
                                      [165,42,42],[0,128,128],[128,128,0],[0,0,128],
                                      [250,128,114],[240,230,140],[135,206,235],
                                      [255,215,0],[238,130,238]])/255))
    centers = np.array([[.72,.49,.37],[.9,.7,.56],[.35,.6,.85],[.22,.48,.19],[.82,.57,.25]])
    semantic = np.clip(centers[rng.integers(0,5,4096)] + rng.normal(0,.08,(4096,3)),0,1)
    samples = [pool[rng.integers(0,len(pool),n)] for pool,n in
               zip([grid,gray,chart,semantic],[4096,1536,1536,3072])]
    samples.append(grid)
    if photo is not None:
        p = np.asarray(photo).reshape(-1,3)
        samples.append(p[rng.integers(0,len(p),len(np.concatenate(samples))//3)])
    return np.concatenate(samples).reshape(1,-1,3)


def wb_estimate(lut):
    gray = np.repeat(np.linspace(.15,.85,65)[:,None],3,1)
    ab = np.mean((rgb2lab(apply_lut(gray,lut))-rgb2lab(gray))[:,1:],axis=0)
    steps = np.clip(np.rint([ab[1]/2,-ab[0]/2]),-7,7).astype(int)
    return {"A_B":int(steps[0]),"G_M":int(steps[1]),"mean_delta_ab":ab.tolist(),
            "approximate":True,"lab_units_per_step":2.0,
            "note":"正 A 偏暖、正 G 偏绿；每档 2 Lab 单位为工程近似，未经相机标定"}


def wb_apply(rgb, wb, inverse=False):
    if wb["A_B"] == 0 and wb["G_M"] == 0: return np.asarray(rgb).copy()
    lab = rgb2lab(np.clip(rgb,0,1))
    shift = np.array([0,-2*wb["G_M"],2*wb["A_B"]])
    return np.clip(lab2rgb(lab + (-shift if inverse else shift)),0,1)


def diagnostics(lut, base, target):
    warnings = ["仅支持已显影 sRGB；不能自动证明输入域，请确认不是 Log/RAW/ACES",
                "无法表达局部对比、空间蒙版、颗粒；暗角固定为 0",
                "影调仍为近似模型；白平衡档位未经相机标定"]
    if not np.allclose(lut["low"],0) or not np.allclose(lut["high"],1):
        warnings.append("非标准输入域，疑似 Log/RAW 或 shaper，建议先转换到 sRGB")
    if any(k in lut.get("title","").lower() for k in ("log","aces","raw","shaper")):
        warnings.append("LUT 标题含 Log/RAW/ACES/shaper 标记，疑似输入域不适合")
    grid = lut["grid"]
    if all(np.max(np.ptp(np.moveaxis(grid[...,c],c,0).reshape(len(grid),-1),axis=1)) < 1e-5 for c in range(3)):
        warnings.append("通道独立变换：可能为 1D shaper，也可能是合法曲线；请确认输入域")
    clipped = np.mean(np.any(((target<=.001)|(target>=.999)) & ((base>.01)&(base<.99)),axis=-1))
    if clipped > .05 or lut["clipped_values"]:
        warnings.append(f"明显截断：内域采样触边比例 {clipped:.1%}")
    gray = np.repeat(np.linspace(.1,.9,33)[:,None],3,1)
    if np.max(np.ptp(rgb2lab(apply_lut(gray,lut))[:,1:],axis=0)) > 6:
        warnings.append("灰阶偏色随亮度变化，疑似分离色调；单一白平衡无法完整表达")
    return warnings



def integer_refine(base, target, recipe, cal, count, progress=None):
    """Search deployable integers directly; no approximate derivatives for final choice."""
    rng = np.random.default_rng(752)
    idx = rng.choice(base.shape[1],min(count,base.shape[1]),replace=False)
    b,t = base[0,idx],target[0,idx]
    model = Model(b,cal,np.zeros((len(b),2)))
    def score(v):
        return float(np.mean(metric(model.apply(v),t)))
    proposed = np.array(vector(recipe),dtype=float)
    bounds = limits(cal).astype(int)
    finalists = []
    # Separate neutral and surrogate starts prevent approximate-model tone errors
    # from trapping HSL in compensating local minima.
    for start in (np.zeros(40), proposed):
        v = start.copy()
        best = score(v)
        for sweep in range(6):
            changed = False
            for i in range(39):
                chosen = v[i]
                for value in range(-bounds[i],bounds[i]+1):
                    if value == v[i]: continue
                    trial = v.copy()
                    trial[i] = value
                    loss = score(trial)
                    if loss < best - 1e-8:
                        best,chosen = loss,value
                if chosen != v[i]: changed = True
                v[i] = chosen
            if progress: progress({"integer_sweep":sweep+1})
            if not changed: break
        finalists.append((best,v))
    return from_vector(min(finalists,key=lambda x:x[0])[1],recipe)


def fit_lut(lut, cal, photo=None, initial=None, max_nfev=100, sample_count=768, progress=None):
    base = representative_colors(photo)
    target = apply_lut(base,lut)
    wb = wb_estimate(lut)
    initial = initial or neutral("LUT 自动配方")
    initial = {**initial,"settings":{**initial["settings"],"shading":0}}
    raw, raw_report = fit_pair(base,target,cal,initial,max_nfev,sample_count,progress,NAMES[:39])
    raw = integer_refine(base,target,raw,cal,sample_count,progress)
    raw_pred = Model(base,cal).apply(vector(raw))
    raw_report["validation_pixels"] = error_summary(raw_pred,target)
    raw_report["per_sector"] = sector_report(base,raw_pred,target,cal)
    raw_report["solver"]["integer_refinement"] = "neutral + surrogate starts; up to 6 full-range sweeps each"
    raw_report["solver"]["train_mean_delta_e_2000"] = None
    raw_report["validation_scope"] = "Full weighted synthetic distribution, includes training samples"
    raw_report["quality"] = "差"
    stats = raw_report["validation_pixels"]
    for i,label in ((1,"近似"),(0,"好")):
        if stats["mean_delta_e_2000"] <= cal["quality_mean_delta_e"][i] and stats["p95_delta_e_2000"] <= cal["quality_p95_delta_e"][i]:
            raw_report["quality"] = label
    corrected = wb_apply(target,wb,inverse=True)
    if wb["A_B"] == 0 and wb["G_M"] == 0:
        import copy
        recipe,report = copy.deepcopy(raw),copy.deepcopy(raw_report)
    else:
        recipe, report = fit_pair(base,corrected,cal,initial,max_nfev,sample_count,progress,NAMES[:39])
        recipe = integer_refine(base,corrected,recipe,cal,sample_count,progress)
    recipe["recommendations"]["wb_shift"] = f"A/B {wb['A_B']:+d}, G/M {wb['G_M']:+d}（近似建议；手动设置）"
    predicted = wb_apply(Model(base,cal).apply(vector(recipe)),wb)
    report.update(mode="lut-only" if photo is None else "lut-with-photo-colors",
                  wb_shift=wb,unsplit={"recipe":raw,"report":raw_report},
                  combined_validation=error_summary(predicted,target),
                  combined_per_sector=sector_report(base,predicted,target,cal),
                  validation_scope="Synthetic sRGB distribution; not camera validation",
                  weighting="grid floor + 40/15/15/30 mixture; photo adds 25% final mass")
    combined = report["combined_validation"]
    mean, p95 = combined["mean_delta_e_2000"], combined["p95_delta_e_2000"]
    report["quality"] = "差"
    for i,label in ((1,"近似"),(0,"好")):
        if mean <= cal["quality_mean_delta_e"][i] and p95 <= cal["quality_p95_delta_e"][i]:
            report["quality"] = label
    report["validation_pixels"] = combined
    report["per_sector"] = report["combined_per_sector"]
    report["solver"]["integer_refinement"] = "neutral + surrogate starts; up to 6 full-range sweeps each"
    report["solver"]["train_mean_delta_e_2000"] = None
    report["warnings"] = diagnostics(lut,base,target) + report["warnings"][:1]
    return recipe,report
