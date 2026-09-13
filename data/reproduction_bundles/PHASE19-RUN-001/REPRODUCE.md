# Replication Instructions for Phase 19 Benchmark Run
- Run ID: PHASE19-RUN-001
- Target: Validate deterministic CPU reproduction of AeroSurrogate weights and metrics.

## Execution Command:
```powershell
.\.venv\Scripts\python.exe -c "from backend.physics_ai.reproduction_campaign import Phase19CampaignOrchestrator; Phase19CampaignOrchestrator.reproduce_run_b()"
```
