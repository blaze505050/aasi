"""
Comprehensive test suite for standalone AASI modules:
- data_preprocessing.py
- train_models.py
- api_server.py
- Turnkey commercial study packaging
"""

import io
import json
import zipfile
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Target modules
from data_preprocessing import AirfoilPreprocessor, AerospaceDatasetIngestor
from train_models import TrainingConfig, SecureAerodynamicSurrogate, run_training_pipeline
from api_server import app


# ─── 1. Data Preprocessing Tests ──────────────────────────────────────────────

def test_naca4_generation_and_features():
    """Verify NACA 4-digit analytical generation and geometric feature extraction."""
    x, y = AirfoilPreprocessor.generate_naca4("0012", num_points=160)
    assert len(x) == 161
    assert len(y) == 161
    assert np.isclose(x[0], 1.0, atol=1e-3) # TE upper
    assert np.isclose(x[len(x)//2], 0.0, atol=1e-3) # LE

    features = AirfoilPreprocessor.extract_features("NACA_0012", x, y)
    assert features.is_symmetric is True
    assert np.isclose(features.max_thickness, 0.12, atol=0.01)
    assert np.isclose(features.max_camber, 0.0, atol=0.005)

def test_cambered_airfoil_features():
    """Verify camber line detection for NACA 4412."""
    x, y = AirfoilPreprocessor.generate_naca4("4412", num_points=160)
    features = AirfoilPreprocessor.extract_features("NACA_4412", x, y)
    assert features.is_symmetric is False
    assert np.isclose(features.max_camber, 0.04, atol=0.01)
    assert np.isclose(features.max_thickness, 0.12, atol=0.01)

def test_raw_coordinate_text_parsing():
    """Verify Selig / CSV coordinate text ingestion."""
    raw_text = """NACA 0012 Test Airfoil
1.000000 0.001260
0.950000 0.011320
0.800000 0.038230
0.500000 0.078020
0.200000 0.082600
0.000000 0.000000
0.200000 -0.082600
0.500000 -0.078020
0.800000 -0.038230
0.950000 -0.011320
1.000000 -0.001260
"""
    name, x_raw, y_raw = AirfoilPreprocessor.parse_coordinate_text(raw_text)
    assert "NACA_0012" in name
    assert len(x_raw) == 11
    x_norm, y_norm = AirfoilPreprocessor.normalize_and_redistribute(x_raw, y_raw, num_panels=80)
    assert len(x_norm) == 81

def test_uiuc_polar_ingestion():
    """Verify UIUC wind tunnel polar parsing."""
    sample_polar = """Alpha  CL      CD      CDp     CM
-4.00  -0.380  0.0078  0.0021  0.005
 0.00   0.050  0.0062  0.0018  0.002
 4.00   0.490  0.0075  0.0025 -0.001
 8.00   0.920  0.0110  0.0040 -0.003
12.00   1.280  0.0195  0.0090 -0.004
"""
    polar_data = AerospaceDatasetIngestor.parse_uiuc_polar(sample_polar)
    assert polar_data["num_points"] == 5
    assert polar_data["cl_max"] == 1.280
    assert polar_data["alpha_stall_deg"] == 12.0

def test_shm_vibration_signal_analysis():
    """Verify SHM vibration feature extraction."""
    t = np.linspace(0, 1, 1000, endpoint=False)
    sig = np.sin(2 * np.pi * 60 * t) # 60 Hz sine wave
    report = AerospaceDatasetIngestor.preprocess_shm_vibration_signal(sig.tolist(), sampling_rate_hz=1000.0)
    assert report["dominant_frequency_hz"] == 60.0
    assert report["status"] == "NORMAL"


# ─── 2. Model Training & Surrogate Tests ──────────────────────────────────────

def test_surrogate_training_and_cryptographic_seal(tmp_path):
    """Verify decoupled training, high-accuracy prediction, and tamper detection."""
    cfg = TrainingConfig(
        model_name="Test_Surrogate",
        polynomial_degree=2,
        regularization_alpha=1e-4,
        save_dir=str(tmp_path)
    )
    surrogate, metrics = run_training_pipeline(cfg)
    assert metrics["test_r2_CL"] > 0.95
    assert metrics["test_r2_CD"] > 0.90
    assert metrics["test_r2_CM"] > 0.95

    # Test safe loading
    saved_file = tmp_path / "Test_Surrogate.json"
    assert saved_file.exists()
    loaded_model = SecureAerodynamicSurrogate.load(str(saved_file))
    assert loaded_model.provenance_sha256 == surrogate.provenance_sha256

    # Verify tamper resistance: modify file content
    with open(saved_file, "r") as f:
        tampered_data = json.load(f)
    tampered_data["degree"] = 99  # Unauthorized modification
    with open(saved_file, "w") as f:
        json.dump(tampered_data, f)

    with pytest.raises(ValueError, match="tampering detected"):
        SecureAerodynamicSurrogate.load(str(saved_file))


# ─── 3. API Server Endpoints & Commercial Study Tests ─────────────────────────

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["physics_engine"] == "Vortex_Panel_VLM_ASME_VV20"

def test_api_preprocess_airfoil():
    response = client.post(
        "/api/v1/preprocess/airfoil",
        json={"airfoil_code": "2412", "num_panels": 120},
        headers={"X-API-Key": "aasi_dev_key_test_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["features"]["name"] == "NACA_2412"
    assert data["features"]["max_thickness"] == 0.12

def test_api_surrogate_predict():
    response = client.post(
        "/api/v1/surrogate/predict",
        json={
            "max_camber": 0.02,
            "camber_loc": 0.40,
            "thickness": 0.12,
            "thick_loc": 0.30,
            "alpha_deg": 4.0,
            "mach": 0.15,
            "reynolds": 1000000
        },
        headers={"X-API-Key": "aasi_dev_key_test_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "CL" in data["predictions"]
    assert "CD" in data["predictions"]
    assert data["epistemic_check"]["valid_regime"] is True

def test_api_turnkey_study_zip_package():
    """Verify the turnkey commercial study endpoint produces a valid, complete ZIP package."""
    response = client.post(
        "/commercial/turnkey-study",
        json={
            "airfoil_code": "2412",
            "airframe_name": "Test_Fixed_Wing_UAV",
            "aspect_ratio": 8.0,
            "taper_ratio": 0.7,
            "quarter_chord_sweep_deg": 2.5
        },
        headers={"X-API-Key": "aasi_dev_key_test_123"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Inspect zip contents
    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        file_list = zf.namelist()
        assert "aerodynamics/polar_table.csv" in file_list
        assert "aerodynamics/stability_derivatives.json" in file_list
        assert "simulation/usaf_datcom_Test_Fixed_Wing_UAV.dat" in file_list
        assert "simulation/nasa_shabp_Test_Fixed_Wing_UAV.shabp" in file_list
        assert "simulation/jsbsim_6dof_Test_Fixed_Wing_UAV.xml" in file_list
        assert "simulation/px4_params_Test_Fixed_Wing_UAV.params" in file_list
        assert "verification/ASME_VV20_Dossier.md" in file_list
        assert "verification/asme_vv20_report.json" in file_list

        # Verify content of DATCOM card
        datcom_text = zf.read("simulation/usaf_datcom_Test_Fixed_Wing_UAV.dat").decode("utf-8")
        assert "$FLTCON" in datcom_text
        assert "$WGPLNF" in datcom_text

        # Verify ASME V&V 20 report
        vv20_text = zf.read("verification/ASME_VV20_Dossier.md").decode("utf-8")
        assert "Grid Convergence Index" in vv20_text
        assert "Observed Order of Accuracy" in vv20_text

def test_api_authentication_enforcement():
    """Verify unauthorized rejection when an invalid API key is supplied."""
    response = client.post(
        "/api/v1/preprocess/airfoil",
        json={"airfoil_code": "0012"},
        headers={"X-API-Key": "unauthorized_malicious_key"}
    )
    assert response.status_code == 401
    assert "Invalid or expired API Key" in response.json()["error"]["message"]
