"""Strict full-resolution RGB TIFF comparison; no resizing or color conversion."""
import argparse
import json
from pathlib import Path
import numpy as np
from .workspace_probe import private_report_path


def pixel_error(candidate, reference):
    a, b = np.asarray(candidate), np.asarray(reference)
    if (a.shape != b.shape or a.ndim != 3 or a.shape[-1] != 3 or
            min(a.shape[:2]) < 1 or a.dtype != b.dtype or
            a.dtype.kind != "u" or a.dtype.itemsize not in (1, 2)):
        raise ValueError("expected equal-size RGB uint8/uint16 arrays with identical dtype")
    delta = a.astype(np.float64) - b.astype(np.float64)
    maximum = np.iinfo(a.dtype).max
    # Work in original code values; never quantize 16-bit data to 8 bits.
    return {"format": "ep7-workspace-pixel-error-v1", "shape": list(a.shape),
            "bit_depth": a.dtype.itemsize * 8, "pixels": a.shape[0] * a.shape[1],
            "mae_lsb": float(np.abs(delta).mean()),
            "rmse_lsb": float(np.sqrt(np.mean(delta ** 2))),
            "max_abs_lsb": int(np.abs(delta).max()),
            "mae_normalized": float(np.abs(delta).mean() / maximum),
            "per_channel_mae_lsb": np.abs(delta).mean(axis=(0, 1)).tolist(),
            "per_channel_bias_lsb": delta.mean(axis=(0, 1)).tolist(),
            "identical_pixel_fraction": float(np.all(delta == 0, axis=-1).mean())}


def read_tiff(path):
    import tifffile
    # Explicit restrictions avoid silently comparing thumbnails, masks or CMYK.
    with tifffile.TiffFile(path) as image:
        if len(image.pages) != 1:
            raise ValueError("expected a single-page RGB TIFF")
        page = image.pages[0]
        orientation = page.tags.get("Orientation")
        if page.photometric != 2 or page.samplesperpixel != 3 or (orientation and orientation.value != 1):
            raise ValueError("expected top-left RGB TIFF without alpha")
        icc = page.tags.get(34675)
        return page.asarray(), bytes(icc.value) if icc else None


def compare_files(candidate, reference):
    a, ai = read_tiff(candidate)
    b, bi = read_tiff(reference)
    if not ai or ai != bi:
        raise ValueError("both TIFFs must carry the same nonempty ICC profile; no implicit conversion")
    return pixel_error(a, b)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate")
    parser.add_argument("reference")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        output = private_report_path(args.report)
        result = compare_files(args.candidate, args.reference)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f"error: {error}\n")
    print("Private full-resolution pixel error report saved.")


if __name__ == "__main__":
    main()
