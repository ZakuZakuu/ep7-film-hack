"""Smooth, explicitly approximate developed-sRGB model (not the Olympus ISP)."""
import numpy as np
from skimage.color import hsv2rgb, rgb2hsv


def image_array(rgb):
    a = np.asarray(rgb, dtype=np.float64)
    if a.ndim < 2 or a.shape[-1] != 3 or not np.isfinite(a).all() or a.min() < 0 or a.max() > 1:
        raise ValueError("图像必须是有限的 0…1 RGB 三通道数组")
    return a


def weights(hue, cal):
    distance = np.abs((np.asarray(hue)[..., None] * 360 -
                       np.array(cal["sector_centers_degrees"]) + 180) % 360 - 180)
    u = np.minimum(distance / cal["sector_width_degrees"], 1)
    w = (0.5 + 0.5 * np.cos(np.pi * u)) ** 2
    total = w.sum(axis=-1, keepdims=True)
    if np.any(total < 1e-12):
        raise ValueError("校准色区存在空隙；增大 sector_width_degrees")
    return w / total


def coordinates(shape):
    """Pixel centers normalized independently by the two half-axis lengths."""
    h, w = shape[:2]
    y, x = np.mgrid[:h, :w]
    return np.stack(((x + 0.5) * 2 / w - 1, (y + 0.5) * 2 / h - 1), axis=-1)


def raw_baseline(rgb, cal):
    return np.clip(image_array(rgb) * cal["raw_rgb_gain"], 0, 1) ** cal["raw_gamma"]


class Model:
    def __init__(self, rgb, cal, xy=None):
        self.rgb = image_array(rgb)
        self.cal = cal
        self.hsv = rgb2hsv(self.rgb)
        self.w = weights(self.hsv[..., 0], cal)
        self.chroma = np.minimum(self.hsv[..., 1] / cal["neutral_chroma_threshold"], 1)
        self.chroma = self.chroma ** 2 * (3 - 2 * self.chroma)
        if xy is None:
            if self.rgb.ndim != 3:
                raise ValueError("采样点必须提供原图 xy 坐标")
            xy = coordinates(self.rgb.shape)
        self.r2 = np.sum(np.asarray(xy, dtype=float) ** 2, axis=-1)
        if self.r2.shape != self.rgb.shape[:-1] or not np.isfinite(self.r2).all():
            raise ValueError("xy 坐标形状或数值错误")

    def apply(self, values):
        v = np.asarray(values, dtype=float)
        if v.shape != (40,) or not np.isfinite(v).all():
            raise ValueError("模型需要 40 个有限参数")
        if not np.any(v):
            return self.rgb.copy()
        c, hsv = self.cal, self.hsv.copy()
        hue = self.w @ v[:12]
        sat = self.w @ v[12:24]
        native_l = np.interp(v[24:36], np.arange(-7, 8), c["lightness_native"])
        light = self.w @ native_l
        hsv[..., 0] = (hsv[..., 0] + self.chroma * hue * c["hue_degrees_per_step"] / 360) % 1
        hsv[..., 1] = np.clip(hsv[..., 1] * np.exp(sat * c["saturation_log_gain_per_step"]), 0, 1)
        hsv[..., 2] = np.clip(hsv[..., 2] + self.chroma * light * c["lightness_gain"] / 1000, 0, 1)
        out = hsv2rgb(hsv)
        y = out @ np.array([0.2126, 0.7152, 0.0722])
        # Smooth Bernstein bumps vanish at black and white; original approximation.
        basis = np.stack((4 * y * (1 - y) ** 3,
                          6 * y ** 2 * (1 - y) ** 2,
                          4 * y ** 3 * (1 - y)), axis=-1)
        out = np.clip(out + (basis @ v[36:39] * c["tone_gain_per_step"])[..., None], 0, 1)
        if v[39]:
            # Interpolate continuously while fitting, quantize only the exported recipe.
            scale = np.interp(abs(v[39]), np.arange(6),
                              [c["shading_coordinate_words"][1]] + c["shading_coordinate_words"][1:]) / 1024
            u = np.clip((self.r2 * scale ** 2 - c["shading_start"]) / c["shading_extent"], 0, 1)
            mask = u * u * (3 - 2 * u) * c["shading_gain"] * min(abs(v[39]), 1)
            if v[39] < 0:
                out *= 1 - mask[..., None]
            else:
                out += (1 - out) * mask[..., None]
        return np.clip(out, 0, 1)
