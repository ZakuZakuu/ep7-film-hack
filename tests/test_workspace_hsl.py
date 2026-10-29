"""Owned synthetic geometry/curves only; no camera, DLL or vendor fixtures."""

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
    import skimage
except ImportError as error:
    raise unittest.SkipTest("optional numerical dependencies absent") from error
from tools.recipe_studio.workspace_hsl import WorkspaceHSL, truncdiv, signed7
from tools.recipe_studio.workspace_polar import PolarKernel
from tools.recipe_studio import backend
from tools.recipe_studio.recipe import calibration


def owned_stage():
    stage = WorkspaceHSL.__new__(WorkspaceHSL)
    records = []
    for _ in range(12):
        row = bytearray(28)
        struct.pack_into("<6H3h", row, 0, 0, 32767, 0, 1023, 0, 1023, 0, 100, 0)
        row[20:26] = bytes([1, 7, 1, 0, 1, 0])
        records.append(bytes(row))
    stage.records = records
    stage.mask = 0xFFF
    stage.polar = PolarKernel([0] * 64, [0] * 64, [0] * 32)
    stage.trig = [512 | (256 << 17)] * 16
    stage.hue = [-10 * i for i in range(-7, 8)]
    stage.light = [i * 2 for i in range(-7, 8)]
    stage.curves = [([32] * 96, [0] * 96) for _ in range(14)]
    return stage


class StageTests(unittest.TestCase):
    def test_scalar_and_vectorized_fixed_point_agree_on_owned_data(self):
        stage = owned_stage()
        rng = np.random.default_rng(8)
        pixels = rng.integers(0, 256, (128, 3), dtype=np.uint8)
        for values in [[0] * 36, [int(v) for v in rng.integers(-7, 8, 36)]]:
            coefficients = stage.coefficients(values)
            scalar = np.array(
                [stage.yuv(tuple(map(int, p)), coefficients) for p in pixels],
                dtype=np.uint8,
            )
            np.testing.assert_array_equal(
                stage.pixels8(pixels, values, rgb=False), scalar
            )

    def test_signed_packing_and_truncation(self):
        self.assertEqual(
            [signed7(x) for x in [0, 63, 64, 127, 255]], [0, 63, -64, -1, -1]
        )
        self.assertEqual(truncdiv(-257, 256), -1)
        self.assertEqual(truncdiv(257, 256), 1)
        stage = owned_stage()
        self.assertEqual(stage.curve(1, 0, 256), 32)
        self.assertEqual(stage.curve(1, 0, 257), 63)
        self.assertEqual(stage.curve(1, 14, 0), 0)

    def test_reject_noninteger_steps_and_wrong_fingerprint(self):
        for values in [[0] * 35, [8] + [0] * 35, [0.5] + [0] * 35, [True] + [0] * 35]:
            with self.assertRaises(ValueError):
                owned_stage().coefficients(values)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "owned.dat"
            p.write_bytes(b"owned")
            with self.assertRaises(ValueError):
                WorkspaceHSL(p, "0" * 64)

    def test_default_adapter_uses_only_exact_hsl_for_neutral_tail(self):
        stage = owned_stage()
        rng = np.random.default_rng(71)
        source = rng.random((8, 9, 3))
        v = [0] * 40
        v[0] = 3
        with patch.object(backend, "selected_stage", return_value=stage):
            expected = stage.pixels8(
                np.rint(source * 255).astype(np.uint8), v[:36], rgb=False
            )
            # Stub RGB wrapper: its contract must receive integer byte input.
            with patch.object(
                stage, "pixels8", return_value=expected.reshape(-1, 3)
            ) as call:
                got = backend.Model(source, calibration()).apply(v)
                np.testing.assert_array_equal(got, expected.astype(float) / 255)
                self.assertEqual(call.call_args.args[0].dtype, np.uint8)
            v[0] = 0.5
            with self.assertRaises(ValueError):
                backend.Model(source, calibration()).apply(v)

    def test_missing_assets_fallback_and_explicit_configuration_errors(self):
        with patch.dict("os.environ", {"EP7_RECIPE_MODEL": "approximate"}):
            self.assertIsNone(backend.selected_stage())
            self.assertFalse(backend.backend_status()["exact_hsl"])
        with patch.dict(
            "os.environ",
            {
                "EP7_RECIPE_MODEL": "workspace",
                "EP7_WORKSPACE_QUALIFICATION": "/does/not/exist",
            },
        ):
            with self.assertRaises(ValueError):
                backend.selected_stage()

    def test_stale_native_qualification_cannot_silently_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "qualification.json"
            p.write_text(json.dumps({"passed": True}))
            with patch.dict(
                "os.environ",
                {
                    "EP7_RECIPE_MODEL": "workspace",
                    "EP7_WORKSPACE_QUALIFICATION": str(p),
                },
            ):
                with self.assertRaises(ValueError):
                    backend.selected_stage()


class HTTPRoutingTests(unittest.TestCase):
    def test_selected_stage_status_and_preview_are_consistent(self):
        import io
        from PIL import Image
        from tools.recipe_studio.server import create_app
        from tools.recipe_studio.recipe import neutral

        stage = owned_stage()
        raw = io.BytesIO()
        Image.new("RGB", (16, 16), (100, 120, 140)).save(raw, format="PNG")
        raw.seek(0)
        with patch.object(backend, "selected_stage", return_value=stage):
            client = create_app().test_client()
            config = client.get("/api/config").get_json()
            self.assertTrue(config["model"]["exact_hsl"])
            headers = {"X-Studio-Token": config["token"], "Origin": "http://localhost"}
            response = client.post(
                "/api/upload/base", data={"file": (raw, "owned.png")}, headers=headers
            )
            self.assertEqual(response.status_code, 200)
            # Owned stage stub returns a distinctive byte image, independent
            # of the approximate fallback, so API routing is observable.
            with patch.object(
                stage,
                "pixels8",
                side_effect=lambda pixels, values: np.full_like(pixels, 77),
            ):
                response = client.post("/api/preview", json=neutral(), headers=headers)
            self.assertEqual(response.status_code, 200)
            actual = np.asarray(Image.open(io.BytesIO(response.data)))
            self.assertTrue(np.all(actual == 77))


class QualificationTests(unittest.TestCase):
    def test_valid_qualification_selects_backend_and_hash_mismatch_fails(self):
        implementation = Path(backend.__file__).with_name("workspace_hsl.py")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "owned-qualification.json"
            report = {
                "format": "ep7-workspace-hsl-qualification-v1",
                "passed": True,
                "implementation_sha256": hashlib.sha256(
                    implementation.read_bytes()
                ).hexdigest(),
                "sha256": "owned-fingerprint",
                "dll": "owned.dll",
                "cases": [{"mismatches": 0} for _ in range(350)],
            }
            path.write_text(json.dumps(report))
            with patch.dict(
                "os.environ",
                {
                    "EP7_RECIPE_MODEL": "workspace",
                    "EP7_WORKSPACE_QUALIFICATION": str(path),
                },
            ):
                with patch.object(
                    backend, "WorkspaceHSL", return_value=owned_stage()
                ) as factory:
                    self.assertIsNotNone(backend.selected_stage())
                    factory.assert_called_once_with("owned.dll", "owned-fingerprint")
                backend._qualified.cache_clear()
                with patch.object(
                    backend,
                    "WorkspaceHSL",
                    side_effect=ValueError("fingerprint mismatch"),
                ):
                    with self.assertRaises(ValueError):
                        backend.selected_stage()
