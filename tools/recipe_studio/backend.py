"""Default HSL backend selection with an explicitly labelled approximate fallback."""

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from .model import Model as ApproximateModel, image_array
from .workspace_hsl import WorkspaceHSL


@lru_cache(maxsize=2)
def _qualified(path, modified, size):
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    implementation = Path(__file__).with_name("workspace_hsl.py")
    cases = report.get("cases") if isinstance(report, dict) else None
    if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
        raise ValueError("Workspace HSL qualification cases are malformed")
    if not isinstance(report.get("dll"), str) or not isinstance(
        report.get("sha256"), str
    ):
        raise ValueError("Workspace HSL qualification identity is missing")
    if (
        report.get("format") != "ep7-workspace-hsl-qualification-v1"
        or report.get("passed") is not True
        or report.get("implementation_sha256")
        != hashlib.sha256(implementation.read_bytes()).hexdigest()
        or len(report.get("cases", [])) < 350
        or any(c.get("mismatches") != 0 for c in report["cases"])
    ):
        raise ValueError(
            "Workspace HSL qualification is invalid or stale; rerun native verification"
        )
    dll = os.environ.get("EP7_WORKSPACE_DLL", report["dll"])
    if os.name != "nt" and len(dll) > 2 and dll[1:3] == ":\\":
        dll = "/mnt/" + dll[0].lower() + "/" + dll[3:].replace("\\", "/")
    return WorkspaceHSL(dll, report["sha256"])


def selected_stage():
    preference = os.environ.get("EP7_RECIPE_MODEL", "workspace")
    if preference not in ("workspace", "approximate"):
        raise ValueError("EP7_RECIPE_MODEL must be workspace or approximate")
    if preference == "approximate":
        return None
    default = (
        r"\\wsl.localhost\Ubuntu\tmp\ep7-workspace-research\hsl-qualified.json"
        if os.name == "nt"
        else "/tmp/ep7-workspace-research/hsl-qualified.json"
    )
    path = Path(os.environ.get("EP7_WORKSPACE_QUALIFICATION", default))
    if not path.exists():
        if "EP7_WORKSPACE_QUALIFICATION" in os.environ:
            raise ValueError("configured Workspace qualification file is missing")
        return None
    info = path.stat()
    return _qualified(str(path), info.st_mtime_ns, info.st_size)


def backend_status():
    stage = selected_stage()
    return {
        "id": "workspace-hsl" if stage else "approximate-fallback",
        "exact_hsl": stage is not None,
        "approximate_tone_shading": True,
        "label": (
            "Workspace HSL 已通过原生一致性验证；影调、暗角仍为近似；不等同完整相机显影"
            if stage
            else "近似后备模型；未载入已验证的本机 Workspace 数据"
        ),
    }


class Model:
    def __init__(self, rgb, cal, xy=None):
        self.rgb = image_array(rgb)
        self.cal = cal
        self.xy = xy
        self.stage = selected_stage()
        self.fallback = ApproximateModel(rgb, cal, xy) if self.stage is None else None

    def apply(self, values):
        v = np.asarray(values, dtype=float)
        if v.shape != (40,) or not np.isfinite(v).all():
            raise ValueError("model requires 40 finite values")
        if self.fallback is not None:
            return self.fallback.apply(v)
        if np.any(v[:36] != np.rint(v[:36])) or np.any(np.abs(v[:36]) > 7):
            raise ValueError("Workspace HSL requires integer steps in -7..7")
        pixels = np.rint(self.rgb * 255).astype(np.uint8)
        # Bound temporary arrays for full-resolution inputs.
        flattened = pixels.reshape(-1, 3)
        out = np.empty_like(flattened)
        for start in range(0, len(flattened), 65536):
            out[start : start + 65536] = self.stage.pixels8(
                flattened[start : start + 65536], v[:36].astype(int).tolist()
            )
        result = out.reshape(pixels.shape).astype(float) / 255
        if np.any(v[36:]):
            # Preserve the legacy tail only, never apply its approximate HSL.
            tail = np.zeros(40)
            tail[36:] = v[36:]
            result = ApproximateModel(result, self.cal, self.xy).apply(tail)
        return result
