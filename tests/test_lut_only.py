import unittest
import os
from unittest.mock import patch
try:
    import numpy as np
    import scipy
    import flask
    from PIL import Image
    from skimage.color import rgb2lab
except ImportError as e:
    raise unittest.SkipTest("Recipe Studio optional dependencies absent; dedicated CI installs and runs this suite") from e
from tools.recipe_studio.recipe import calibration, neutral, vector
from tools.recipe_studio.backend import Model
from tools.recipe_studio.lut_fit import representative_colors, wb_estimate, wb_apply, fit_lut, diagnostics
from tools.recipe_studio.lut import apply_lut, read_hald
from PIL import Image
import io

def grid_lut(transform, n=33):
    a=np.linspace(0,1,n)
    g=np.stack(np.meshgrid(a,a,a,indexing="ij"),-1)
    return dict(grid=transform(g),low=np.zeros(3),high=np.ones(3),clipped_values=False)

class LutOnlyTests(unittest.TestCase):
    def test_distribution(self):
        a=representative_colors()
        self.assertEqual(a.shape,(1,28465,3))
        self.assertTrue(np.array_equal(a,representative_colors()))
        self.assertEqual(len(np.unique(a.reshape(-1,3),axis=0))>4913,True)

    def test_hald_level12(self):
        # Own synthetic table; exercise higher resolution ordering.
        n=144
        v=np.arange(n**3,dtype=np.uint32)
        pixels=np.stack((v%n,(v//n)%n,v//(n*n)),axis=-1)*255//(n-1)
        out=io.BytesIO()
        Image.fromarray(pixels.astype("uint8").reshape(1728,1728,3)).save(out,format="PNG")
        out.seek(0)
        lut=read_hald(out)
        np.testing.assert_allclose(apply_lut(np.array([[.2,.4,.6]]),lut),[[.2,.4,.6]],atol=1/255)

    def test_pure_cast(self):
        wb={"A_B":2,"G_M":-1}
        lut=grid_lut(lambda x:wb_apply(x,wb))
        estimate=wb_estimate(lut)
        self.assertEqual((estimate["A_B"],estimate["G_M"]),(2,-1))
        with patch.dict(os.environ,{"EP7_RECIPE_MODEL":"approximate"}):
            r,report=fit_lut(lut,calibration(),max_nfev=10,sample_count=128)
        self.assertLessEqual(max(abs(x) for x in vector(r)[:36]),1)
        self.assertIn("unsplit",report)
        candidates=report["regularization"]["candidates"]
        self.assertEqual(len(candidates),4)
        selected=min(candidates,key=lambda c:c["validation_mean_delta_e"])["values"]
        self.assertEqual(vector(r),selected)

    def test_known_recipe(self):
        with patch.dict(os.environ,{"EP7_RECIPE_MODEL":"approximate"}):
            cal=calibration()
            recipe=neutral()
            recipe["settings"]["hue"][0]=2
            recipe["settings"]["saturation"][6]=-2
            lut=grid_lut(lambda x:Model(x.reshape(-1,3),cal,np.zeros((x.size//3,2))).apply(vector(recipe)).reshape(x.shape))
            r,report=fit_lut(lut,cal,max_nfev=60,sample_count=512,smoothness=0,magnitude=0,starts=2,split_exposure=False)
        self.assertEqual(r["settings"]["hue"][0],2)
        self.assertEqual(r["settings"]["saturation"][6],-2)
        self.assertLess(report["combined_validation"]["mean_delta_e_2000"],.3)

    def test_workspace_recipe_when_qualified(self):
        from tools.recipe_studio.backend import backend_status
        if not backend_status()["exact_hsl"]:
            self.skipTest("Private local Workspace qualification absent")
        cal=calibration()
        known=neutral()
        known["settings"]["hue"][0]=3
        known["settings"]["saturation"][6]=-2
        known["settings"]["lightness"][2]=2
        lut=grid_lut(lambda x:Model(x.reshape(-1,3),cal,np.zeros((x.size//3,2))).apply(vector(known)).reshape(x.shape))
        result,report=fit_lut(lut,cal,max_nfev=60,sample_count=256,smoothness=0,magnitude=0,starts=2,split_exposure=False)
        self.assertEqual(vector(result),vector(known))
        # A 33^3 interpolated LUT cannot reproduce native byte quantization exactly.
        # Compare against the error of the generating recipe on this new prior.
        b=representative_colors()
        from tools.recipe_studio.fit import error_summary
        expected=error_summary(Model(b,cal).apply(vector(known)),apply_lut(b,lut))
        self.assertAlmostEqual(report["combined_validation"]["mean_delta_e_2000"],
                               expected["mean_delta_e_2000"],places=9)

    def test_input_warnings(self):
        from tools.recipe_studio.lut import read_cube
        with self.assertRaises(ValueError):
            read_cube("LUT_1D_SIZE 2\n0 0 0\n1 1 1")
        lut=grid_lut(lambda x:x)
        lut["title"]="Log RAW shaper"
        b=representative_colors()
        warnings=diagnostics(lut,b,apply_lut(b,lut))
        self.assertTrue(any("标题" in w for w in warnings))
        self.assertTrue(any("独立" in w for w in warnings))

    def test_regularization_and_ev(self):
        from tools.recipe_studio.lut_quality import regularization,exposure_apply,exposure_estimate,luminance_report
        v=np.zeros(40);v[0]=4
        rolled=v.copy();rolled[:12]=np.roll(v[:12],3)
        self.assertAlmostEqual(regularization(v),regularization(rolled))
        self.assertGreater(regularization(v),regularization(np.ones(40)))
        lut=grid_lut(lambda x:exposure_apply(x,-2/3))
        self.assertAlmostEqual(exposure_estimate(lut)["ev"],-2/3)
        rgb=np.full((8,3),.4)
        bands=luminance_report(rgb,rgb+.01,rgb)
        self.assertGreater(bands["midtones"]["pred_minus_target_mean_delta_Lab"][0],0)

    def test_gradient_detects_step(self):
        from tools.recipe_studio.lut_quality import smooth_gradient,gradient_report
        a=smooth_gradient()
        smooth=gradient_report(a)
        a[:,512:]=0
        stepped=gradient_report(a)
        self.assertGreater(stepped["max_adjacent_delta_e"],smooth["max_adjacent_delta_e"]+5)

    def test_web_without_photo(self):
        from tools.recipe_studio.server import create_app
        app=create_app()
        c=app.test_client()
        token=c.get("/api/config").json["token"]
        with patch("tools.recipe_studio.server.read_cube",return_value=grid_lut(lambda x:x)):
            self.assertEqual(c.post("/api/upload/lut",data={"file":(io.BytesIO(b"x"),"x.cube")},headers={"X-Studio-Token":token}).status_code,200)
        with patch("tools.recipe_studio.lut_fit.fit_lut",return_value=(neutral(),{})):
            self.assertEqual(c.post("/api/fit",json={"mode":"lut-only","recipe":neutral()},headers={"X-Studio-Token":token}).status_code,200)

if __name__=="__main__": unittest.main()
