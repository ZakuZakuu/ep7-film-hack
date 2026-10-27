"""Registered regional camera-photo observations, not exact model validation.

No exposure/WB correction is applied. Local outputs must stay under system temp.
Inputs/ROIs belong in a private manifest; no photographic fixtures are shipped.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .workspace_probe import private_report_path


def align_photo(reference, moving):
    import cv2
    a, b = np.asarray(reference), np.asarray(moving)
    if (a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3 or
            a.dtype != np.uint8 or b.dtype != np.uint8):
        raise ValueError("alignment requires equal-size RGB uint8 images")
    detector = cv2.ORB_create(nfeatures=5000)
    ka, da = detector.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), None)
    kb, db = detector.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_RGB2GRAY), None)
    if da is None or db is None:
        raise ValueError("insufficient image structure for alignment")
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(db, da, k=2)
    good = [m for pair in matches if len(pair) == 2 for m, n in [pair] if m.distance < .7 * n.distance]
    if len(good) < 30:
        raise ValueError("fewer than 30 reliable feature matches")
    src = np.float32([kb[m.queryIdx].pt for m in good])
    dst = np.float32([ka[m.trainIdx].pt for m in good])
    cv2.setRNGSeed(71)
    matrix, inliers = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                                ransacReprojThreshold=2, maxIters=5000)
    if matrix is None or inliers is None:
        raise ValueError("alignment estimation failed")
    selected = inliers.ravel().astype(bool)
    scale = float(np.hypot(matrix[0, 0], matrix[1, 0]))
    angle = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))
    h, w = a.shape[:2]
    if (selected.sum() < 25 or selected.mean() < .3 or abs(scale - 1) > .03 or
            abs(angle) > 3 or abs(matrix[0, 2]) > .05 * w or abs(matrix[1, 2]) > .05 * h):
        raise ValueError(f"small-pose limits: inliers={int(selected.sum())}/{len(good)}, scale={scale:.6f}, rotation={angle:.3f}, translation={matrix[:, 2].tolist()}")
    projected = cv2.transform(src[None], matrix)[0]
    residual = np.linalg.norm(projected - dst, axis=1)[selected]
    aligned = cv2.warpAffine(b, matrix, (w, h), flags=cv2.INTER_LINEAR)
    valid = cv2.warpAffine(np.ones((h, w), np.uint8), matrix, (w, h),
                           flags=cv2.INTER_NEAREST).astype(bool)
    # Exclude interpolation footprints at the transformed image boundary.
    valid = cv2.erode(valid.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    return aligned, valid, {"method": "ORB-small-pose", "moving_to_reference": matrix.tolist(), "scale": scale,
                            "rotation_degrees": angle, "matches": len(good),
                            "inliers": int(selected.sum()),
                            "median_reprojection_px": float(np.median(residual)),
                            "p95_reprojection_px": float(np.percentile(residual, 95))}


def align_planar_photo(reference, moving, box):
    """Second registration method for a declared flat surface such as a screen.

    Observations outside box are invalidated. This is not a whole-scene warp.
    """
    import cv2
    a, b = np.asarray(reference), np.asarray(moving)
    if a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8 or b.dtype != np.uint8:
        raise ValueError("planar alignment requires equal-size RGB uint8 images")
    h, w = a.shape[:2]
    box = np.asarray(box, float)
    if box.shape != (4,) or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
        raise ValueError("invalid declared planar region")
    x0, y0, x1, y1 = np.rint(box * [w, h, w, h]).astype(int)
    domain = np.zeros((h, w), np.uint8)
    domain[y0:y1, x0:x1] = 1
    detector = cv2.SIFT_create(nfeatures=6000)
    ka, da = detector.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), domain)
    kb, db = detector.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_RGB2GRAY), domain)
    if da is None or db is None:
        raise ValueError("insufficient planar features")
    pairs = cv2.BFMatcher().knnMatch(db, da, k=2)
    good = [m for pair in pairs if len(pair) == 2 for m, n in [pair] if m.distance < .65 * n.distance]
    if len(good) < 40:
        raise ValueError("fewer than 40 planar matches")
    src = np.float32([kb[m.queryIdx].pt for m in good])
    dst = np.float32([ka[m.trainIdx].pt for m in good])
    cv2.setRNGSeed(71)
    matrix, inliers = cv2.findHomography(src, dst, cv2.RANSAC, 2, maxIters=5000)
    if matrix is None or inliers is None:
        raise ValueError("planar registration failed")
    keep = inliers.ravel().astype(bool)
    residual = np.linalg.norm(cv2.perspectiveTransform(src[None], matrix)[0] - dst, axis=-1)[keep]
    corners = np.float32([[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]])
    mapped = cv2.perspectiveTransform(corners, matrix)[0]
    ratio = abs(cv2.contourArea(mapped)) / ((x1 - x0) * (y1 - y0))
    if (keep.sum() < 40 or keep.mean() < .4 or np.percentile(residual, 95) > 2 or
            not np.isfinite(mapped).all() or not cv2.isContourConvex(mapped) or not .7 < ratio < 1.4):
        raise ValueError(f"unreliable planar alignment: inliers={int(keep.sum())}/{len(good)}, area ratio={ratio:.3f}")
    aligned = cv2.warpPerspective(b, matrix, (w, h), flags=cv2.INTER_LINEAR)
    valid = cv2.warpPerspective(domain, matrix, (w, h), flags=cv2.INTER_NEAREST) & domain
    valid = cv2.erode(valid, np.ones((3, 3), np.uint8)).astype(bool)
    return aligned, valid, {"method": "SIFT-homography-declared-plane", "moving_to_reference": matrix.tolist(),
                            "matches": len(good), "inliers": int(keep.sum()),
                            "median_reprojection_px": float(np.median(residual)),
                            "p95_reprojection_px": float(np.percentile(residual, 95))}


def regional_observations(reference, aligned, valid, regions):
    import cv2
    from skimage.color import rgb2hsv, rgb2lab
    if (reference.shape != aligned.shape or reference.ndim != 3 or reference.shape[2] != 3 or
            reference.dtype != np.uint8 or aligned.dtype != np.uint8 or valid.shape != reference.shape[:2]):
        raise ValueError("regional observations require matched RGB uint8 images and a validity mask")
    a, b = reference.astype(float) / 255, aligned.astype(float) / 255
    ha, hb = rgb2hsv(a), rgb2hsv(b)
    la, lb = rgb2lab(a), rgb2lab(b)
    h, w = a.shape[:2]
    result = {}
    for name, spec in regions.items():
        box = np.asarray(spec["box"], dtype=float)
        if (box.shape != (4,) or not np.isfinite(box).all() or
                not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1)):
            raise ValueError("region box requires normalized [left, top, right, bottom]")
        x0, y0, x1, y1 = np.rint(box * [w, h, w, h]).astype(int)
        mask = np.zeros((h, w), bool)
        mask[y0:y1, x0:x1] = True
        mask &= valid
        mask &= ha[..., 1] >= spec.get("min_saturation", 0)
        mask &= ha[..., 1] <= spec.get("max_saturation", 1)
        if "hue_degrees" in spec:
            lo, hi = spec["hue_degrees"]
            hue = ha[..., 0] * 360
            mask &= ((hue >= lo) & (hue <= hi)) if lo <= hi else ((hue >= lo) | (hue <= hi))
        # Choose on reference only. A zero R channel in deep blue is not a
        # black pixel; filtering on output would bias the measured effect.
        mask &= (a.max(axis=-1) > 2 / 255) & (a.min(axis=-1) < 253 / 255)
        mask = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        count = int(mask.sum())
        if count < 32:
            result[name] = {"pixels": count, "status": "insufficient-unclipped-region"}
            continue
        hue_mask = mask & (np.ptp(a, axis=-1) > .03) & (np.ptp(b, axis=-1) > .03)
        def measure(rgb, hsv, lab):
            v = rgb[mask]
            hue = hsv[..., 0][hue_mask] * 2 * np.pi
            return {"hsv_hue_degrees": (float(np.degrees(np.arctan2(np.sin(hue).mean(), np.cos(hue).mean())) % 360)
                                         if len(hue) >= 32 else None),
                    "median_hsv_saturation": float(np.median(hsv[..., 1][mask])),
                    "median_hsl_lightness": float(np.median((v.max(axis=-1) + v.min(axis=-1)) / 2)),
                    "median_lab_L": float(np.median(lab[..., 0][mask])),
                    "median_lab_chroma": float(np.median(np.hypot(lab[..., 1][mask], lab[..., 2][mask])))}
        result[name] = {"pixels": count, "status": "observed", "reference": measure(a, ha, la),
                        "moving": measure(b, hb, lb),
                        "hue_pixels": int(hue_mask.sum()),
                        "reference_channel_limit_fraction": float(np.any((a[mask] <= 2/255) | (a[mask] >= 253/255), axis=-1).mean()),
                        "moving_channel_limit_fraction": float(np.any((b[mask] <= 2/255) | (b[mask] >= 253/255), axis=-1).mean()),
                        "median_delta_hue_degrees": (float(np.median((hb[..., 0][hue_mask] - ha[..., 0][hue_mask] + .5) % 1 - .5) * 360)
                                                     if hue_mask.sum() >= 32 else None),
                        "median_delta_lab_L": float(np.median(lb[..., 0][mask] - la[..., 0][mask])),
                        "median_delta_lab_chroma": float(np.median(np.hypot(lb[..., 1][mask], lb[..., 2][mask]) -
                                                                  np.hypot(la[..., 1][mask], la[..., 2][mask])))}
    return result


def run_manifest(path):
    from .images import read_image
    path = Path(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("format") != "ep7-photo-observations-v1":
        raise ValueError("expected ep7-photo-observations-v1")
    def read(filename):
        if Path(filename).suffix.lower() not in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
            raise ValueError("regional camera observations require a developed RGB image")
        a, _ = read_image(path.parent / filename, max_side=1296)
        return np.rint(a * 255).astype(np.uint8)
    cases = []
    for pair in manifest["pairs"]:
        a, b = read(pair["reference"]), read(pair["moving"])
        try:
            if pair.get("registration") == "planar":
                aligned, valid, registration = align_planar_photo(a, b, pair["plane_box"])
            elif pair.get("registration", "small-pose") == "small-pose":
                aligned, valid, registration = align_photo(a, b)
            else:
                raise ValueError("unknown registration method")
        except ValueError as error:
            cases.append({"id": pair["id"], "status": "rejected-alignment", "reason": str(error)})
            continue
        cases.append({"id": pair["id"], "status": "observed", "shape": list(a.shape), "registration": registration,
                      "regions": regional_observations(a, aligned, valid, pair["regions"])})
    return {"format": "ep7-photo-observations-report-v1", "cases": cases,
            "limitations": ["regional camera observations at max side 1296, not Workspace model error",
                            "no exposure or white-balance normalization; no inference of exact pixel algorithm",
                            "RANSAC reprojection residuals use fitted inliers, not independent registration validation"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        output = private_report_path(args.report)
        result = run_manifest(args.manifest)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f"error: {error}\n")
    print("Private regional camera-photo observations saved.")


if __name__ == "__main__":
    main()
