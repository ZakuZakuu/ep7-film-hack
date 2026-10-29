"""Display-domain diagnostics; recommendations are not calibrated camera controls."""
import numpy as np
from skimage.color import rgb2lab, lab2rgb, hsv2rgb
from .fit import error_summary, metric


def linear(rgb):
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def encoded(rgb):
    rgb = np.maximum(rgb,0)
    return np.clip(np.where(rgb <= .0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055),0,1)


def exposure_apply(rgb, ev):
    return encoded(linear(np.asarray(rgb))*2**ev)


def exposure_estimate(lut):
    from .lut import apply_lut
    gray=np.repeat(np.linspace(.15,.85,101)[:,None],3,axis=1)
    before=linear(gray)@np.array([.2126,.7152,.0722])
    after=linear(apply_lut(gray,lut))@np.array([.2126,.7152,.0722])
    shifts=np.log2(np.maximum(after,1e-6)/before)
    ev=float(np.clip(np.round(np.median(shifts)*3)/3,-3,3))
    return {"ev":ev,"gray_ev_p10_p90":np.percentile(shifts,[10,90]).tolist(),
            "approximate":True,"note":"encoded sRGB decoded to linear luminance; median neutral shift, rounded to 1/3 EV; not camera calibrated"}


def recommendations_apply(rgb, wb, ev=0, inverse=False):
    from .lut_fit import wb_apply
    if inverse:
        return exposure_apply(wb_apply(rgb,wb,inverse=True),-ev)
    return wb_apply(exposure_apply(rgb,ev),wb)


def regularization(v, smoothness=.08, magnitude=.01):
    a=np.asarray(v)[:36].reshape(3,12)
    return float(smoothness*np.mean((a-np.roll(a,1,axis=1))**2)
                 +magnitude*np.mean(np.asarray(v)[:39]**2))


def smooth_gradient():
    # Horizontal hue ramps at four saturation/brightness levels; separate gray row.
    h=np.linspace(0,1,1024,endpoint=False)
    rows=[hsv2rgb(np.stack((h,np.full_like(h,s),np.full_like(h,v)),axis=-1))
          for s,v in ((.2,.5),(.5,.6),(.8,.8),(1.,1.))]
    rows.append(np.repeat(np.linspace(0,1,1024)[:,None],3,axis=1))
    return np.stack(rows)


def gradient_report(rgb, target=None):
    d=metric(rgb[:,:-1],rgb[:,1:])
    out={"hue_seam_delta_e":metric(rgb[:4,-1],rgb[:4,0]).tolist(),
         "max_adjacent_delta_e":float(d.max()),"p99_adjacent_delta_e":float(np.percentile(d,99)),
         "adjacent_over_2":int((d>2).sum())}
    if target is not None:
        td=metric(target[:,:-1],target[:,1:])
        out["target_max_adjacent_delta_e"]=float(td.max())
        out["excess_over_target_max"]=float(np.max(d-td))
    return out


def luminance_report(base, prediction, target):
    lab=rgb2lab(base); p=rgb2lab(prediction);t=rgb2lab(target)
    result={}
    for name,lo,hi in (("shadows",0,33),("midtones",33,67),("highlights",67,101)):
        mask=(lab[...,0]>=lo)&(lab[...,0]<hi)
        if not mask.any():
            result[name]={"count":0};continue
        delta=p[mask]-t[mask]
        result[name]={**error_summary(prediction[mask],target[mask]),
                      "pred_minus_target_mean_delta_Lab":delta.mean(axis=0).tolist(),
                      "note":"+a red / -a green; +b yellow / -b blue; +L prediction too bright"}
    return result


def representability(lut):
    from .lut import apply_lut
    gray=np.repeat(np.linspace(.05,.95,91)[:,None],3,1)
    delta=rgb2lab(apply_lut(gray,lut))-rgb2lab(gray)
    sat=[]
    for value in (.35,.65,.95):
        h=np.linspace(0,1,120,endpoint=False)
        rgb=hsv2rgb(np.stack((h,np.full_like(h,.45),np.full_like(h,value)),axis=-1))
        before=rgb2lab(rgb);after=rgb2lab(apply_lut(rgb,lut))
        sat.append(float(np.mean(np.linalg.norm(after[:,1:],axis=1)-np.linalg.norm(before[:,1:],axis=1))))
    span=np.ptp(delta[:,1:],axis=0)
    reasons=[]
    if np.max(span)>6:
        reasons.append("Neutral chroma varies with luminance: a single WB translation cannot reproduce the measured shadow/highlight difference")
    if sat[2]-sat[1]<-2:
        reasons.append("Highlight chroma falls relative to midtones: arbitrary brightness-dependent desaturation has no independent recipe control")
    if not reasons:
        reasons.append("No strong split-tone signature in these probes; remaining limitations include fixed HSL gates, quantization and approximate tone response")
    return {"identified_constraints":reasons,"neutral_ab_range":span.tolist(),
            "neutral_ab_shadows_mid_high":[x[:,1:].mean(axis=0).tolist() for x in np.array_split(delta,3)],
            "mean_chroma_change_at_V_035_065_095":sat,
            "highlight_minus_mid_chroma_change":sat[2]-sat[1],
            "limits":["Brightness-dependent neutral chroma cannot be reproduced by a single WB translation",
                      "12 HSL sectors have fixed luminance/chroma gates; arbitrary hue x luminance saturation is not independently controllable",
                      "Tone stage remains approximate; observed error is not a proven mathematical lower bound"]}

