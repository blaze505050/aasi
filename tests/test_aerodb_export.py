"""
Unit Tests for AASI Aerospace Exporters.
Verifies USAF DATCOM cards, NASA S/HABP tables, and 6-DOF simulation CSV formatting.
"""

import pytest
from backend.physics.aerodb_engine import AerodynamicDatabaseEngine
from backend.export.aerodb_export import AeroDBExporter


@pytest.fixture(scope="module")
def sample_db():
    return AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name="NACA 0012",
        alpha_min=-2.0,
        alpha_max=8.0,
        alpha_step=2.0,
        reynolds_list=[3_000_000.0],
        mach_list=[0.15],
    )


def test_datcom_export_syntax(sample_db):
    """Verify DATCOM output adheres to standard namelist cards and includes UQ."""
    datcom_text = AeroDBExporter.export_datcom(sample_db)
    assert isinstance(datcom_text, str)
    assert "DIM M" in datcom_text
    assert "$FLTCON" in datcom_text
    assert "MACH(1)=0.150" in datcom_text
    assert "RNNUB(1)=3.000E+06" in datcom_text
    assert "$OPTINS" in datcom_text
    assert "$SYNTHS" in datcom_text
    assert "NACA-4-0012" in datcom_text
    assert "NEXT CASE" in datcom_text
    assert "ALPHA        CL          CD          CM" in datcom_text
    assert "UNCERTAINTY (95% CONFIDENCE" in datcom_text
    assert "U95_CL" in datcom_text


def test_shabp_export_syntax(sample_db):
    """Verify NASA S/HABP tabulated output contains required blocks and UQ values."""
    shabp_text = AeroDBExporter.export_shabp(sample_db)
    assert isinstance(shabp_text, str)
    assert "NASA S/HABP" in shabp_text
    assert "$TABLE" in shabp_text
    assert "CL_ALPHA" in shabp_text
    assert "ALPHA_0L" in shabp_text
    assert "CD_0" in shabp_text
    assert "U95_CL_MEAN" in shabp_text
    assert "U95_CL" in shabp_text
    assert "$ENDTABLE" in shabp_text


def test_6dof_csv_export(sample_db):
    """Verify 6-DOF simulation CSV table contains correct column headers, UQ metrics, and valid rows."""
    csv_text = AeroDBExporter.export_6dof_csv(sample_db)
    lines = [line.strip() for line in csv_text.strip().splitlines() if line.strip()]
    assert len(lines) >= 6  # 1 header + 5 points
    header = lines[0].split(",")
    assert "mach" in header
    assert "reynolds" in header
    assert "alpha_deg" in header
    assert "cl" in header
    assert "cd" in header
    assert "cm" in header
    assert "l_over_d" in header
    assert "cl_uncertainty_u95" in header
    assert "cd_uncertainty_u95" in header
    assert "cm_uncertainty_u95" in header
    assert "cl_alpha_per_rad" in header
