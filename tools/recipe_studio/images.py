"""Local decoding only; EXIF orientation and embedded RGB ICC handled by Pillow."""
import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms, ImageOps

MAX_PIXELS = 60_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
REPO = Path(__file__).resolve().parents[2]


def private_output(path):
    p = Path(path).expanduser().resolve()
    if p == REPO or REPO in p.parents:
        raise ValueError("照片/预览输出必须放在仓库之外；Cloud 请使用私有 /tmp")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_image(source, name=None, max_side=None, crop=None):
    """Return RGB in encoded sRGB and non-sensitive decode notes."""
    filename = name or str(source)
    if filename.lower().endswith(".orf"):
        import rawpy
        raw_source = io.BytesIO(source) if isinstance(source, bytes) else str(source)
        with rawpy.imread(raw_source) as raw:
            if raw.sizes.width * raw.sizes.height > MAX_PIXELS:
                raise ValueError("RAW 图像过大")
            rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True,
                                  output_color=rawpy.ColorSpace.sRGB, output_bps=16,
                                  gamma=(2.4, 12.92), user_flip=None)
        a = rgb.astype(np.float64) / 65535
        notes = {"kind": "raw", "decoder": "LibRaw/rawpy, camera WB, sRGB, no auto brightness",
                 "warning": "RAW 显影不是相机 Natural/COLOR；未经校准时只可近似预览"}
    else:
        source = io.BytesIO(source) if isinstance(source, bytes) else source
        with Image.open(source) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("图像过大")
            image = ImageOps.exif_transpose(image)
            icc = image.info.get("icc_profile")
            if icc:
                profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                image = ImageCms.profileToProfile(image, profile, ImageCms.createProfile("sRGB"), outputMode="RGB")
                color_note = "embedded ICC converted to sRGB"
            else:
                exif = image.getexif()
                color_space = exif.get_ifd(34665).get(40961) if 34665 in exif else exif.get(40961)
                if color_space == 2:
                    raise ValueError("Adobe RGB 照片缺少 ICC；请先转换为 sRGB")
                image = image.convert("RGB")
                color_note = "untagged image assumed sRGB"
            a = np.asarray(image, dtype=np.float64) / 255
        notes = {"kind": "jpeg-or-rgb", "decoder": color_note,
                 "warning": "请使用 Natural 或原厂默认 COLOR 基准；既有效果无法自动消除"}
    notes["original_shape"] = list(a.shape[:2])
    if crop is not None:
        if (not isinstance(crop, list) or len(crop) != 4 or any(type(x) is not int for x in crop) or
                min(crop[:2]) < 0 or min(crop[2:]) < 1 or
                crop[0] + crop[2] > a.shape[1] or crop[1] + crop[3] > a.shape[0]):
            raise ValueError("crop 需为有效的 [left, top, width, height] 像素整数")
        x, y, w, h = crop
        a = a[y:y+h, x:x+w]
        notes["explicit_crop"] = crop
    notes["aligned_shape"] = list(a.shape[:2])
    if max_side and max(a.shape[:2]) > max_side:
        a = resize(a, max_side)
    return a, notes


def resize(rgb, max_side):
    h, w = rgb.shape[:2]
    scale = min(1, max_side / max(h, w))
    # Floating-channel resampling avoids quantizing a RAW down to 8 bit here.
    channels = [np.asarray(Image.fromarray(rgb[..., i].astype(np.float32)).resize(
        (max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.LANCZOS))
        for i in range(3)]
    return np.clip(np.stack(channels, axis=-1).astype(float), 0, 1)


def png_bytes(rgb):
    image = Image.fromarray(np.rint(np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    out = io.BytesIO()
    # No EXIF, file names or input ICC copied to exports.
    image.save(out, format="PNG", icc_profile=ImageCms.ImageCmsProfile(
        ImageCms.createProfile("sRGB")).tobytes())
    return out.getvalue()
