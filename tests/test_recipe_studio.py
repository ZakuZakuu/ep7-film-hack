"""Only generated numerical images; no photos, firmware, network or camera."""
import copy
import io
import json
from pathlib import Path
import tempfile
import time
import unittest

try:
    import numpy as np
    import scipy
    import flask
    from PIL import Image
    from skimage.color import hsv2rgb
except ImportError as e:
    raise unittest.SkipTest("Recipe Studio 可选依赖未安装；专用 Python 3.12 CI 安装并完整验证") from e

from tools.recipe_studio.recipe import (calibration, neutral, validate, vector,
                                         from_vector, load_json)
from tools.recipe_studio.model import Model, weights, coordinates, raw_baseline
from tools.recipe_studio.fit import fit_pair, fit_reference
from tools.recipe_studio.lut import read_cube, read_hald, apply_lut
from tools.recipe_studio.images import read_image, png_bytes, private_output
from tools.recipe_studio.calibrate import fit_calibration_cases
from tools.recipe_studio.server import create_app


def chart(h=48, w=72):
    y, x = np.mgrid[:h, :w]
    return hsv2rgb(np.stack((x / w, .25 + .65 * (y % 12) / 11,
                            .2 + .7 * y / (h - 1)), axis=-1))


def known_recipe():
    r = neutral("合成回收测试")
    r["settings"]["hue"][0] = 3
    r["settings"]["saturation"][2] = 2
    r["settings"]["lightness"][6] = -5
    r["settings"]["tone"]["shadows"] = 1
    r["settings"]["shading"] = -2
    return r


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.c = calibration()

    def test_json_roundtrip_and_units(self):
        r = known_recipe()
        self.assertEqual(validate(load_json(json.dumps(r)), self.c), r)
        self.assertEqual(from_vector(vector(r), r), r)
        self.assertEqual(self.c["lightness_native"][2], -200)
        self.assertEqual(self.c["hue_degrees_per_step"], -4.6666666667)

    def test_reject_ambiguous_or_out_of_range_recipes(self):
        for value in (True, 0.5, 8, -8, None, "0"):
            r = neutral()
            r["settings"]["hue"][0] = value
            with self.assertRaises(ValueError):
                validate(r, self.c)
        for mutate in (lambda r: r.update(extra=1),
                       lambda r: r["settings"].pop("shading"),
                       lambda r: r["settings"]["saturation"].append(0),
                       lambda r: r["recommendations"].update(wb_shift=3)):
            r = neutral()
            mutate(r)
            with self.assertRaises(ValueError):
                validate(r, self.c)
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                load_json(text)

    def test_calibration_validation_and_configurable_saturation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cal.json"
            c = copy.deepcopy(self.c)
            c["limits"]["saturation"] = 7
            p.write_text(json.dumps(c))
            c = calibration(p)
            r = neutral()
            r["settings"]["saturation"][0] = 7
            validate(r, c)
            with self.assertRaises(ValueError):
                validate(r, self.c)
            c["raw_gamma"] = 0
            p.write_text(json.dumps(c))
            with self.assertRaises(ValueError):
                calibration(p)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.c, self.a = calibration(), chart()

    def test_neutral_exact_and_achromatic_hue(self):
        np.testing.assert_array_equal(Model(self.a, self.c).apply([0] * 40), self.a)
        gray = np.repeat(np.linspace(0, 1, 32)[None, :, None], 3, axis=-1)
        v = [7] * 12 + [0] * 28
        np.testing.assert_allclose(Model(gray, self.c).apply(v), gray, atol=1e-14)

    def test_circular_partition_and_continuity(self):
        h = np.linspace(-0.01, 1.01, 20001)
        w = weights(h, self.c)
        np.testing.assert_allclose(w.sum(axis=-1), 1, atol=1e-14)
        np.testing.assert_allclose(weights([0], self.c), weights([1], self.c), atol=1e-14)
        self.assertLess(np.max(np.abs(np.diff(w, axis=0))), .002)
        r = known_recipe()
        v = vector(r)
        rgb = hsv2rgb(np.stack((h % 1, np.full_like(h, .6), np.full_like(h, .5)), axis=-1))
        out = Model(rgb, self.c, np.zeros((len(h), 2))).apply(v)
        self.assertLess(float(np.max(np.abs(np.diff(out, axis=0)))), .002)

    def test_shading_sign_and_non_square_geometry(self):
        a = np.full((60, 100, 3), .5)
        v = [0] * 39 + [-5]
        dark = Model(a, self.c).apply(v)
        bright = Model(a, self.c).apply([0] * 39 + [5])
        self.assertLess(dark[0, 0, 0], dark[29, 49, 0])
        np.testing.assert_allclose(dark + bright, 1, atol=1e-14)
        # Same normalized radius, regardless of frame aspect ratio.
        xy = np.array([[.6, 0], [0, .6]])
        q = Model(np.full((2, 3), .5), self.c, xy).apply(v)
        np.testing.assert_allclose(q[0], q[1])

    def test_fit_recovers_deployable_known_parameters(self):
        r = known_recipe()
        target = Model(self.a, self.c).apply(vector(r))
        fitted, report = fit_pair(self.a, target, self.c)
        self.assertEqual(vector(fitted), vector(r))
        self.assertEqual(report["quality"], "好")
        self.assertLess(report["validation_pixels"]["mean_delta_e_2000"], 1e-8)
        self.assertEqual(len(report["per_sector"]), 12)

    def test_fit_reports_unrepresentable_target_and_missing_coverage(self):
        a = np.full((24, 24, 3), [.4, .2, .1])
        target = a.copy()
        target[::2] = [0, 1, 0]
        _, report = fit_pair(a, target, self.c, max_nfev=30, sample_count=128)
        self.assertEqual(report["quality"], "差")
        self.assertGreater(len(report["unobserved_sectors"]), 8)
        with self.assertRaises(ValueError):
            fit_pair(self.a, self.a[:20], self.c)

    def test_distribution_mode_does_not_claim_pixel_match(self):
        ref = np.flip(self.a, axis=0).copy()
        _, report = fit_reference(self.a, ref, self.c, max_nfev=10)
        self.assertNotEqual(report["quality"], "好")
        self.assertNotIn("validation_pixels", report)
        self.assertIn("distribution_swatches_only", report)


class LUTTests(unittest.TestCase):
    def setUp(self):
        rows = [f"{r} {g} {b}" for b in (0, 1) for g in (0, 1) for r in (0, 1)]
        self.text = 'TITLE "own identity"\nLUT_3D_SIZE 2\n' + "\n".join(rows)

    def test_cube_identity_axis_order_domain_and_clamp(self):
        a = chart()
        np.testing.assert_allclose(apply_lut(a, read_cube(self.text)), a, atol=1e-14)
        lut = read_cube(self.text.replace("LUT_3D_SIZE 2", "LUT_3D_SIZE 2\nDOMAIN_MIN .2 .2 .2\nDOMAIN_MAX .8 .8 .8"))
        np.testing.assert_allclose(apply_lut(np.array([[.1, .5, .9]]), lut), [[0, .5, 1]])

    def test_hald_identity_and_reject_lossy_or_invalid(self):
        rows = np.array([[r, g, b] for b in range(4) for g in range(4) for r in range(4)], dtype=float) / 3
        stream = io.BytesIO(png_bytes(rows.reshape(8, 8, 3)))
        np.testing.assert_allclose(apply_lut(chart(), read_hald(stream)), chart(), atol=1e-14)
        stream = io.BytesIO()
        Image.new("RGB", (8, 8)).save(stream, format="JPEG")
        stream.seek(0)
        with self.assertRaises(ValueError):
            read_hald(stream)
        for text in (self.text + "\n0 0 0", "LUT_1D_SIZE 2\n0 0 0", self.text.replace("1 1 1", "NaN 1 1")):
            with self.assertRaises(ValueError):
                read_cube(text)


class CalibrationTests(unittest.TestCase):
    def test_known_baseline_and_effect_gains_with_held_out_scene(self):
        c = calibration()
        truth = copy.deepcopy(c)
        truth.update(raw_rgb_gain=[1.04, .96, 1.02], raw_gamma=1.08,
                     hue_degrees_per_step=-3.9, lightness_gain=.75)
        a = chart()
        xy = coordinates(a.shape).reshape(-1, 2)
        b = a.reshape(-1, 3)[::5]
        xy = xy[::5]
        cases = []
        for r, split in ((neutral(), "train"), (known_recipe(), "train"), (known_recipe(), "validation")):
            v = np.array(vector(r))
            src = b if split == "train" else b * .9
            target = Model(raw_baseline(src, truth), truth, xy).apply(v)
            cases.append((src, target, xy, v, split))
        new, report = fit_calibration_cases(cases, c)
        np.testing.assert_allclose(new["raw_rgb_gain"], truth["raw_rgb_gain"], atol=.001)
        self.assertAlmostEqual(new["raw_gamma"], truth["raw_gamma"], places=3)
        self.assertAlmostEqual(new["hue_degrees_per_step"], truth["hue_degrees_per_step"], places=2)
        self.assertEqual(report["independent_validation_pairs"], 1)
        self.assertLess(report["pairs"][-1]["after"]["mean_delta_e_2000"], .01)

    def test_neutral_pairs_do_not_claim_effect_calibration(self):
        c = calibration()
        b = chart().reshape(-1, 3)[::10]
        xy = np.zeros((len(b), 2))
        new, report = fit_calibration_cases([(b, b, xy, np.zeros(40), "train")], c)
        self.assertEqual(report["trained_effect_gains"], [])
        self.assertEqual(len(report["unobserved_effect_gains"]), 5)
        self.assertEqual(new["hue_degrees_per_step"], c["hue_degrees_per_step"])


class LocalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.header = {"X-Studio-Token": self.app.config["STUDIO_TOKEN"]}

    def upload(self, role="base", image=None):
        return self.client.post("/api/upload/" + role, headers=self.header,
                                data={"file": (io.BytesIO(png_bytes(chart() if image is None else image)), "generated.png")})

    def test_loopback_csrf_and_private_cache_headers(self):
        self.assertEqual(self.client.get("/", headers={"Host": "attacker.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/validate", json=neutral()).status_code, 403)
        self.assertEqual(self.client.post("/api/validate", json=neutral(), headers={**self.header, "Origin": "https://attacker.example"}).status_code, 403)
        duplicate = json.dumps(neutral()).replace('"name":', '"name":"duplicate","name":', 1)
        self.assertEqual(self.client.post("/api/validate", data=duplicate, content_type="application/json", headers=self.header).status_code, 400)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", res.headers["Content-Security-Policy"])
        res.close()

    def test_browser_upload_preview_recipe_and_background_fit(self):
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(self.client.post("/api/preview", headers=self.header, json=known_recipe()).mimetype, "image/png")
        a = chart()
        target = Model(a, calibration()).apply(vector(known_recipe()))
        self.assertEqual(self.upload("target", target).status_code, 200)
        self.assertEqual(self.client.post("/api/fit", headers=self.header, json={"mode": "target", "recipe": neutral()}).status_code, 200)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            data = self.client.get("/api/fit").get_json()
            if data["status"] != "running":
                break
            time.sleep(.03)
        self.assertEqual(data["status"], "done", data)
        self.assertEqual(vector(data["recipe"]), vector(known_recipe()))
        self.assertFalse(data["stale_input"])

    def test_reject_mismatched_pairs_and_no_image_output_in_repo(self):
        self.upload()
        self.upload("target", np.zeros((12, 24, 3)))
        res = self.client.post("/api/fit", headers=self.header, json={"mode": "target", "recipe": neutral()})
        self.assertEqual(res.status_code, 400)
        with self.assertRaises(ValueError):
            private_output(Path(__file__).resolve().parents[1] / "preview.png")

    def test_explicit_crop_and_decoder_metadata(self):
        data = png_bytes(chart())
        a, info = read_image(data, name="generated.png", crop=[2, 3, 20, 30])
        self.assertEqual(a.shape, (30, 20, 3))
        self.assertEqual(info["original_shape"], [48, 72])
        self.assertEqual(info["aligned_shape"], [30, 20])
        self.assertNotIn("exif", info)
        with self.assertRaises(ValueError):
            read_image(data, name="generated.png", crop=[0, 0, 1000, 20])


if __name__ == "__main__":
    unittest.main()
