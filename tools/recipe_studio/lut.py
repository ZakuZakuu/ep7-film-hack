"""Bounded standard 3D .cube / square Hald CLUT readers and trilinear sampling."""
import itertools
import shlex
import numpy as np
from PIL import Image
from .model import image_array


def read_cube(text):
    if len(text) > 32_000_000:
        raise ValueError("LUT 文件过大")
    size, rows, low, high = None, [], [0., 0., 0.], [1., 1., 1.]
    seen = set()
    for line in text.splitlines():
        parts = shlex.split(line, comments=True)
        if not parts:
            continue
        if parts[0] in ("TITLE", "LUT_3D_SIZE", "DOMAIN_MIN", "DOMAIN_MAX"):
            key = parts[0]
            if key in seen or rows:
                raise ValueError("LUT 重复/迟到的头字段")
            seen.add(key)
            if key == "TITLE":
                if len(parts) != 2:
                    raise ValueError("TITLE 格式错误")
            elif key == "LUT_3D_SIZE":
                if len(parts) != 2:
                    raise ValueError("LUT_3D_SIZE 格式错误")
                size = int(parts[1])
                if not 2 <= size <= 65:
                    raise ValueError("3D LUT 边长必须在 2…65")
            else:
                if len(parts) != 4:
                    raise ValueError("DOMAIN 必须有三个值")
                if key == "DOMAIN_MIN":
                    low = [float(x) for x in parts[1:]]
                else:
                    high = [float(x) for x in parts[1:]]
        else:
            if len(parts) != 3 or size is None:
                raise ValueError("只支持标准 3D .cube；不支持 1D/shaper/混合 LUT")
            rows.append([float(x) for x in parts])
            if len(rows) > size ** 3:
                raise ValueError("LUT 数据过多")
    if size is None or len(rows) != size ** 3:
        raise ValueError("LUT 数据长度不符")
    a, lo, hi = np.array(rows), np.array(low), np.array(high)
    if (not np.isfinite(a).all() or not np.isfinite(lo).all() or
            not np.isfinite(hi).all() or np.any(hi <= lo)):
        raise ValueError("LUT DOMAIN/数据必须有限且范围递增")
    # .cube convention: R changes fastest, then G, then B.
    return {"grid": a.reshape(size, size, size, 3).transpose(2, 1, 0, 3),
            "low": lo, "high": hi, "clipped_values": bool(np.any((a < 0) | (a > 1)))}


def read_hald(source):
    with Image.open(source) as image:
        w, h = image.size
        level = round(w ** (1 / 3))
        if w != h or level ** 3 != w or not 2 <= level <= 8:
            raise ValueError("需要无损正方形 Hald CLUT，边长 level³，level 为 2…8")
        if image.format not in ("PNG", "TIFF") or image.mode not in ("RGB", "RGBA"):
            raise ValueError("Hald 仅支持 8 位 RGB/RGBA PNG/TIFF（LUT 数值不做 ICC 转换）")
        if (image.format == "TIFF" and max(image.tag_v2.get(258, (8,))) != 8) or any(
                "16" in str(tile[3]) for tile in image.tile):
            raise ValueError("请先将 Hald 明确导出为 8 位 RGB，避免静默量化")
        a = np.asarray(image.convert("RGB"), dtype=float) / 255
    size = level ** 2
    return {"grid": a.reshape(size, size, size, 3).transpose(2, 1, 0, 3),
            "low": np.zeros(3), "high": np.ones(3), "clipped_values": False}


def apply_lut(rgb, lut):
    a = image_array(rgb)
    n = lut["grid"].shape[0]
    x = np.clip((a - lut["low"]) / (lut["high"] - lut["low"]), 0, 1) * (n - 1)
    low = np.minimum(x.astype(int), n - 2)
    frac = x - low
    out = np.zeros_like(a)
    for bits in itertools.product((0, 1), repeat=3):
        idx = low + bits
        factor = np.prod(np.where(bits, frac, 1 - frac), axis=-1)
        out += lut["grid"][idx[..., 0], idx[..., 1], idx[..., 2]] * factor[..., None]
    return np.clip(out, 0, 1)
