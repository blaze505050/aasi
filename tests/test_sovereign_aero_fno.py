"""
Unit tests for Module 2: aasi-aero-fno.
Verifies FourNetFlows Conv1d boundary lifting, Geo-FNO coordinate deformation,
IUFNO implicit spectral layers & U-Net skip blocks, and DLR Theodorsen unsteady aeroelasticity.
"""

import sys
import unittest
from pathlib import Path
import torch

# Add aasi-aero-fno to sys.path
mod_path = Path(__file__).resolve().parent.parent / "aasi-aero-fno"
if str(mod_path) not in sys.path:
    sys.path.insert(0, str(mod_path))

from aasi_aero_fno import (
    FourNetFlowsModel,
    GeoFNOAirfoilModel,
    MeshDeformationNetwork,
    IUFNOModel,
    TheodorsenAeroelasticSolver,
    AeroelasticState,
    UnifiedAerodynamicSurrogatePipeline,
)


class TestAASISovereignAeroFNO(unittest.TestCase):
    def test_fournetflows_forward_shape(self):
        model = FourNetFlowsModel(in_channels=5, out_channels=3, hidden_channels=32, modes=6, num_layers=2)
        model.eval()

        # Batch 2, 5 channels, 32x32 resolution
        dummy_inp = torch.randn(2, 5, 32, 32)
        with torch.no_grad():
            out = model(dummy_inp)

        self.assertEqual(out.shape, (2, 3, 32, 32))

    def test_geo_fno_mesh_deformation(self):
        deform = MeshDeformationNetwork(hidden_dim=32)
        xy = torch.tensor([[0.5, 0.1], [0.2, -0.05], [0.8, 0.0]], dtype=torch.float32)
        latent = deform(xy)
        self.assertEqual(latent.shape, (3, 2))
        # Ensure outputs are bounded in [0, 1]
        self.assertTrue(torch.all(latent >= 0.0) and torch.all(latent <= 1.0))

        # Test Jacobian calculation
        jac = deform.compute_jacobian(xy)
        self.assertEqual(jac.shape, (3, 2, 2))

    def test_iufno_implicit_unet_forward(self):
        model = IUFNOModel(in_channels=5, out_channels=3, base_channels=16, modes=6, implicit_loops=2)
        model.eval()

        dummy_inp = torch.randn(1, 5, 32, 32)
        with torch.no_grad():
            out = model(dummy_inp)

        self.assertEqual(out.shape, (1, 3, 32, 32))

    def test_theodorsen_unsteady_aeroelasticity(self):
        solver = TheodorsenAeroelasticSolver(num_strips=16, num_modes=4)
        state = AeroelasticState(
            airspeed_v_inf=50.0,
            alpha_deg=5.0,
            pitch_rate_rad_s=0.1,
            wingspan_m=8.0,
        )

        res = solver.solve_unsteady_loads(state, dt=0.01)
        self.assertGreater(res.total_lift_n, 0.0)
        self.assertEqual(len(res.generalized_modal_forces), 4)
        self.assertEqual(len(res.spanwise_stations_y), 16)
        self.assertGreater(res.flutter_margin_percent, 50.0)
        self.assertGreater(res.divergence_speed_mps, 100.0)

    def test_unified_aerodynamic_surrogate_pipeline(self):
        pipeline = UnifiedAerodynamicSurrogatePipeline(device="cpu")
        steady_eval = pipeline.evaluate_steady_airfoil(
            airfoil_name="NACA 4412",
            alpha_deg=4.0,
            reynolds=1.5e6,
            mach=0.18,
            resolution=32,
            model_type="FOURNETFLOWS",
        )
        self.assertIn("cl_2d", steady_eval)
        self.assertGreater(steady_eval["cl_2d"], 0.5)  # Cambered NACA 4412 produces strong lift
        self.assertIn("l_over_d", steady_eval)

        # Unsteady flutter evaluation
        ae_eval = pipeline.evaluate_unsteady_aeroelasticity(
            airspeed_v_inf=45.0,
            alpha_deg=4.0,
            wingspan_m=8.0,
        )
        self.assertGreater(ae_eval.total_lift_n, 1000.0)


if __name__ == "__main__":
    unittest.main()
