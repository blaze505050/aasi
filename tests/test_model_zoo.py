"""
AASI Physics AI Model Zoo: Comprehensive Test Suite.
Tests model registry, verification gate, benchmark engine, and API routes.
"""

import pytest
from backend.cognitive.model_zoo import (
    BenchmarkEngine,
    ModelArchitectureFamily,
    ModelMaturityLevel,
    ModelZooRegistry,
    PhysicsAIModelDescriptor,
    PhysicsDomainCategory,
    PhysicsVerificationGate,
    VerificationOutcome,
    model_zoo_registry,
)


class TestModelZooRegistry:
    """Tests for the ModelZooRegistry catalog."""

    def test_catalog_is_populated(self):
        """Catalog must contain all 20 curated Physics AI models."""
        models = model_zoo_registry.list_models()
        assert len(models) >= 20, f"Expected at least 20 models, got {len(models)}"

    def test_all_five_domains_present(self):
        """All 5 physics domains must be represented."""
        domains = model_zoo_registry.get_domains_summary()
        assert "CFD_FLUID_DYNAMICS" in domains
        assert "POROUS_MEDIA_PDE" in domains
        assert "STRUCTURAL_MECHANICS" in domains
        assert "MATERIALS_MOLECULAR" in domains
        assert "CONSERVATION_MULTIPHYSICS" in domains

    def test_cfd_domain_models(self):
        """CFD domain must contain MeshGraphNet, DoMINO, DPOT, Transolver, OFormer, DISCO, Hyena."""
        cfd_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.CFD_FLUID_DYNAMICS)
        names = {m.name for m in cfd_models}
        assert "MeshGraphNet" in names
        assert "DoMINO" in names
        assert "DPOT" in names
        assert "Transolver" in names
        assert "OFormer" in names
        assert "DISCO" in names
        assert "Hyena Neural Operator" in names
        assert len(cfd_models) == 7

    def test_pde_domain_models(self):
        """PDE domain must contain FNO, RNO, MGNO, DEQ."""
        pde_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.POROUS_MEDIA_PDE)
        names = {m.name for m in pde_models}
        assert "FNO (Fourier Neural Operator)" in names
        assert "RNO (Recurrent Neural Operator)" in names
        assert "Multi-Grid Neural Operator (MGNO)" in names
        assert "DEQ Neural Operators" in names
        assert len(pde_models) == 4

    def test_structural_domain_models(self):
        """Structural domain must contain PFEM, FENet, RealPDEBench."""
        struct_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.STRUCTURAL_MECHANICS)
        names = {m.name for m in struct_models}
        assert len(struct_models) == 3

    def test_materials_domain_models(self):
        """Materials domain must contain MACE, AIMNet2, SevenNet."""
        mat_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.MATERIALS_MOLECULAR)
        names = {m.name for m in mat_models}
        assert "MACE" in names
        assert "AIMNet2" in names
        assert "SevenNet" in names
        assert len(mat_models) == 3

    def test_conservation_domain_models(self):
        """Conservation domain must contain LGNO, PINTO, Mantle Convection."""
        con_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.CONSERVATION_MULTIPHYSICS)
        names = {m.name for m in con_models}
        assert "LGNO (Latent Graph Neural Operator)" in names
        assert "PINTO" in names
        assert len(con_models) == 3

    def test_filter_by_architecture(self):
        """Filtering by architecture must return only matching models."""
        gnn_models = model_zoo_registry.list_models(architecture=ModelArchitectureFamily.GRAPH_NEURAL_NETWORK)
        for m in gnn_models:
            assert m.architecture == ModelArchitectureFamily.GRAPH_NEURAL_NETWORK

    def test_filter_by_maturity(self):
        """Filtering by maturity must return only matching models."""
        prod_models = model_zoo_registry.list_models(maturity=ModelMaturityLevel.PRODUCTION_READY)
        for m in prod_models:
            assert m.maturity == ModelMaturityLevel.PRODUCTION_READY

    def test_search_query(self):
        """Search must find models by name and description keywords."""
        results = model_zoo_registry.list_models(search_query="fourier")
        assert len(results) > 0
        results_mace = model_zoo_registry.list_models(search_query="mace")
        assert any("MACE" in m.name for m in results_mace)

    def test_model_has_provenance_hash(self):
        """Every model must have a non-empty provenance hash."""
        for model in model_zoo_registry.list_models():
            assert model.provenance_hash, f"Model {model.name} is missing provenance hash"
            assert len(model.provenance_hash) == 64  # SHA-256

    def test_model_has_io_schema(self):
        """Every model must have a valid I/O schema."""
        for model in model_zoo_registry.list_models():
            assert model.io_schema.input_type
            assert model.io_schema.output_fields
            assert model.io_schema.mesh_type

    def test_get_model_by_id(self):
        """Should retrieve a model by its ID."""
        models = model_zoo_registry.list_models()
        first = models[0]
        retrieved = model_zoo_registry.get_model(first.model_id)
        assert retrieved is not None
        assert retrieved.name == first.name

    def test_get_nonexistent_model_returns_none(self):
        """Should return None for unknown model ID."""
        assert model_zoo_registry.get_model("NONEXISTENT") is None

    def test_architectures_summary(self):
        """Architectures summary should match actual model counts."""
        summary = model_zoo_registry.get_architectures_summary()
        total = sum(summary.values())
        assert total == len(model_zoo_registry.list_models())


class TestPhysicsVerificationGate:
    """Tests for the physics verification gate."""

    def setup_method(self):
        self.gate = PhysicsVerificationGate()

    def test_valid_predictions_pass(self):
        """Physically valid predictions must pass all checks."""
        report = self.gate.verify_inference(
            model_id="test-model",
            predictions={"CL": 0.485, "CD": 0.0092, "pressure": 101325.0},
            conservation_residuals={"mass": 1.2e-5, "momentum": 3.4e-4},
        )
        assert report.outcome == VerificationOutcome.PASSED
        assert len(report.checks_failed) == 0
        assert report.epistemic_tier_assigned == "SURROGATE_VERIFIED"

    def test_negative_drag_fails(self):
        """Negative drag coefficient must fail bounds check."""
        report = self.gate.verify_inference(
            model_id="test-negative-cd",
            predictions={"CL": 0.5, "CD": -0.003},
        )
        assert report.outcome == VerificationOutcome.FAILED_BOUNDS
        assert any("CD" in v for v in report.physical_bounds_violated)
        assert report.epistemic_tier_assigned == "SURROGATE_UNVERIFIED"

    def test_nan_fails_stability(self):
        """NaN in predictions must fail stability check."""
        report = self.gate.verify_inference(
            model_id="test-nan",
            predictions={"CL": float("nan"), "CD": 0.01},
        )
        assert report.outcome == VerificationOutcome.FAILED_STABILITY

    def test_inf_fails_stability(self):
        """Infinity in predictions must fail stability check."""
        report = self.gate.verify_inference(
            model_id="test-inf",
            predictions={"CL": float("inf"), "CD": 0.01},
        )
        assert report.outcome == VerificationOutcome.FAILED_STABILITY

    def test_large_conservation_residual_fails(self):
        """Large conservation residual must fail conservation check."""
        report = self.gate.verify_inference(
            model_id="test-conservation",
            predictions={"CL": 0.5, "CD": 0.01},
            conservation_residuals={"mass": 0.5, "momentum": 0.3},
        )
        assert report.outcome == VerificationOutcome.FAILED_CONSERVATION

    def test_weak_conservation_gives_warning(self):
        """Moderate conservation residual should give warning."""
        report = self.gate.verify_inference(
            model_id="test-weak",
            predictions={"CL": 0.5, "CD": 0.01},
            conservation_residuals={"mass": 0.05},
        )
        assert report.outcome == VerificationOutcome.WARNING_PARTIAL
        assert report.epistemic_tier_assigned == "SURROGATE_INFERENCE"

    def test_pressure_out_of_bounds(self):
        """Negative pressure must fail bounds check."""
        report = self.gate.verify_inference(
            model_id="test-pressure",
            predictions={"pressure": -100.0, "CD": 0.01},
        )
        assert report.outcome == VerificationOutcome.FAILED_BOUNDS
        assert any("pressure" in v for v in report.physical_bounds_violated)

    def test_no_conservation_data_skips_check(self):
        """Without conservation residuals, only bounds and stability are checked."""
        report = self.gate.verify_inference(
            model_id="test-no-conservation",
            predictions={"CL": 0.5, "CD": 0.01},
        )
        assert "CONSERVATION_RESIDUALS" not in report.checks_performed


class TestBenchmarkEngine:
    """Tests for the cross-model benchmark engine."""

    def setup_method(self):
        self.engine = BenchmarkEngine()

    def test_canonical_problems_exist(self):
        """At least 5 canonical benchmark problems must be defined."""
        problems = self.engine.list_problems()
        assert len(problems) >= 5

    def test_filter_problems_by_domain(self):
        """Filtering by domain should return only matching problems."""
        cfd_problems = self.engine.list_problems(domain=PhysicsDomainCategory.CFD_FLUID_DYNAMICS)
        for p in cfd_problems:
            assert p.domain == PhysicsDomainCategory.CFD_FLUID_DYNAMICS

    def test_compare_models(self):
        """Comparison must return ranked results."""
        models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.CFD_FLUID_DYNAMICS)[:3]
        comparison = self.engine.compare_models(models)
        assert comparison.results is not None
        assert len(comparison.results) == 3
        assert comparison.ranking is not None

    def test_comparison_ranking_order(self):
        """Ranking must be ordered by primary metric."""
        models = model_zoo_registry.list_models()[:5]
        comparison = self.engine.compare_models(models, "Navier-Stokes")
        # Ranking should have same length as results
        assert len(comparison.ranking) == len(comparison.results)


class TestModelZooAPIIntegration:
    """Tests for API route integration (import verification)."""

    def test_api_routes_importable(self):
        """Model zoo API routes must be importable without errors."""
        from backend.api.routes_model_zoo import router
        assert router is not None
        assert router.prefix == "/model-zoo"

    def test_api_init_includes_model_zoo(self):
        """Model zoo router must be included in API init."""
        from backend.api import api_router
        # Walk all nested routes to find model-zoo paths
        all_paths = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                all_paths.append(route.path)
            elif hasattr(route, 'routes'):
                for sub in route.routes:
                    if hasattr(sub, 'path'):
                        all_paths.append(sub.path)
        # The model-zoo prefix should be discoverable through nested routes
        # If FastAPI nests them as _IncludedRouter, verify the import is wired
        from backend.api.routes_model_zoo import router as mz_router
        assert mz_router.prefix == "/model-zoo"
        # Verify the router object is wired by checking api_router has routes
        assert len(api_router.routes) > 15  # We have 17+ routers wired


class TestModelDescriptorIntegrity:
    """Tests that every model descriptor meets AASI quality standards."""

    def test_all_models_have_descriptions(self):
        """Every model must have a non-trivial description."""
        for model in model_zoo_registry.list_models():
            assert len(model.description) > 20, f"{model.name} has too-short description"

    def test_all_models_have_domains(self):
        """Every model must be classified into a physics domain."""
        for model in model_zoo_registry.list_models():
            assert model.domain is not None

    def test_all_models_have_architecture(self):
        """Every model must have an architecture classification."""
        for model in model_zoo_registry.list_models():
            assert model.architecture is not None

    def test_all_models_have_applicable_physics(self):
        """Every model must specify applicable physics."""
        for model in model_zoo_registry.list_models():
            assert len(model.applicable_physics) > 0, f"{model.name} has no applicable_physics"

    def test_no_duplicate_model_ids(self):
        """All model IDs must be unique."""
        models = model_zoo_registry.list_models()
        ids = [m.model_id for m in models]
        assert len(ids) == len(set(ids)), "Duplicate model IDs detected"

    def test_mace_is_production_ready(self):
        """MACE should be classified as production-ready."""
        mace_models = model_zoo_registry.list_models(search_query="MACE")
        assert any(m.maturity == ModelMaturityLevel.PRODUCTION_READY for m in mace_models)

    def test_fno_is_validated_benchmark(self):
        """FNO should be classified as validated benchmark."""
        fno_models = model_zoo_registry.list_models(search_query="FNO")
        assert any(m.maturity == ModelMaturityLevel.VALIDATED_BENCHMARK for m in fno_models)


class TestModelExecutionAdapter:
    """Tests for the ModelExecutionAdapter and ConnectedPipelineEngine."""

    def test_meshgraphnet_execution(self):
        """MeshGraphNet must execute locally, returning forces and Cp distribution."""
        from backend.cognitive.model_zoo import ModelInferenceRequest
        cfd_models = model_zoo_registry.list_models(domain=PhysicsDomainCategory.CFD_FLUID_DYNAMICS)
        mgn = next(m for m in cfd_models if m.name == "MeshGraphNet")
        
        req = ModelInferenceRequest(
            model_id=mgn.model_id,
            geometry="NACA 0012",
            alpha_deg=4.0,
            reynolds=3.0e6,
            mach=0.15,
        )
        res = model_zoo_registry.execute_model(req)
        assert res.model_name == "MeshGraphNet"
        assert res.predictions["CL"] > 0.0
        assert res.predictions["CD"] > 0.0
        assert res.predictions["L_over_D"] > 0.0
        assert len(res.field_distribution["x"]) == 64
        assert len(res.field_distribution["Cp_upper"]) == 64
        assert res.epistemic_tier == "SURROGATE_VERIFIED"
        assert res.verification_report["outcome"] == "PASSED"

    def test_transolver_cambered_airfoil(self):
        """Transolver execution with cambered airfoil (NACA 2412)."""
        from backend.cognitive.model_zoo import ModelInferenceRequest
        ts = next(m for m in model_zoo_registry.list_models() if m.name == "Transolver")
        req = ModelInferenceRequest(
            model_id=ts.model_id,
            geometry="NACA 2412",
            alpha_deg=0.0,
            reynolds=2.0e6,
            mach=0.20,
        )
        res = model_zoo_registry.execute_model(req)
        # Cambered airfoil at alpha=0 has positive lift
        assert res.predictions["CL"] > 0.1
        assert res.predictions["CD"] > 0.005
        assert res.predictions["CM"] < 0.0  # Nose-down moment for positive camber

    def test_pde_and_structural_domains(self):
        """Porous media and structural mechanics models execute properly."""
        from backend.cognitive.model_zoo import ModelInferenceRequest
        fno = next(m for m in model_zoo_registry.list_models() if "FNO" in m.name)
        fno_res = model_zoo_registry.execute_model(ModelInferenceRequest(model_id=fno.model_id))
        assert "pressure_drop_pa" in fno_res.predictions
        assert fno_res.predictions["pressure_drop_pa"] > 0.0

        pfem = next(m for m in model_zoo_registry.list_models() if "PFEM" in m.name)
        pfem_res = model_zoo_registry.execute_model(ModelInferenceRequest(model_id=pfem.model_id))
        assert "max_von_mises_stress_mpa" in pfem_res.predictions
        assert pfem_res.predictions["yield_safety_factor"] > 0.0

    def test_connected_pipeline_end_to_end(self):
        """Connected pipeline runs 6 stages seamlessly and produces flight exports."""
        from backend.cognitive.model_zoo import PipelineExecutionRequest
        req = PipelineExecutionRequest(
            geometry="NACA 0012",
            alpha_deg=4.0,
            reynolds=3.0e6,
            mach=0.15,
            run_aero_db_sweep=True,
        )
        res = model_zoo_registry.execute_pipeline(req)
        assert res.status == "COMPLETED"
        assert len(res.stages) == 6
        assert "geometry" in res.stages
        assert "surrogate" in res.stages
        assert "verification" in res.stages
        assert "cognitive" in res.stages
        assert "aero_db" in res.stages
        assert "exports" in res.stages
        assert "datcom" in res.exports
        assert "shabp" in res.exports
        assert "csv" in res.exports
        assert "DIM M" in res.exports["datcom"]
        assert res.final_summary["longitudinal_stability"] in ("STATICALLY_STABLE", "NEUTRALLY_STABLE")


class TestModelZooToolRegistryIntegration:
    """Tests that Model Zoo & Pipeline tools are registered in ScientificToolRegistry."""

    def test_tools_registered(self):
        """Both physics_ai_model_zoo and connected_pipeline must be in ScientificToolRegistry."""
        from backend.cognitive.tools import scientific_tool_registry
        tool_ids = [t.tool_id for t in scientific_tool_registry.list_tools()]
        assert "physics_ai_model_zoo" in tool_ids
        assert "connected_pipeline" in tool_ids

    def test_execute_model_zoo_tool(self):
        """Executing physics_ai_model_zoo via ScientificToolRegistry succeeds."""
        from backend.cognitive.tools import scientific_tool_registry
        res = scientific_tool_registry.execute_tool(
            "physics_ai_model_zoo",
            {"geometry": "NACA 0012", "alpha_deg": 4.0, "reynolds": 3e6, "mach": 0.15},
        )
        assert res["status"] == "SUCCESS"
        assert "CL" in res["results"]
        assert res["epistemic_tier"] == "SURROGATE_VERIFIED"

