# AASI — $0 MVP Strategy

## Reality

The MVP can be developed and demonstrated with a $0 mandatory infrastructure budget, but unlimited compute/storage/API usage can never be guaranteed free.

Design the product so paid services are optional scaling layers.

## Open stack

### Application
- Next.js
- React
- TypeScript
- FastAPI
- Python

### Scientific
- OpenFOAM
- NumPy
- SciPy
- pandas
- matplotlib
- scikit-learn
- CalculiX when useful

### AI

Use an `AIProvider` abstraction:

```text
AIProvider
├── LocalModelProvider
├── OptionalCloudProvider
└── DeterministicScientificProvider
```

The scientific workflow must remain useful when an LLM is unavailable.

### Compute

Primary free paths:

1. user's local machine through AASI Runner
2. Google Colab free tier
3. future HPC provider abstraction

### Storage

Start with SQLite/filesystem. For public beta, use available free tiers with strict quotas and retention limits.

### Hosting

Use available free tiers for frontend/backend where practical. Keep the app containerized and provider-independent so a changed free tier does not break the architecture.

## Cost-control rules

Every remote computation gets:
- resource estimate
- user approval
- timeout
- output-size limit
- retention policy

Never run an unlimited autonomous experiment loop.

## What should remain optional

- paid LLM APIs
- commercial CFD
- paid vector databases
- expensive GPUs
- commercial datasets
- managed enterprise infrastructure

## Target topology

```text
Browser
  ↓
Free web host
  ↓
FastAPI
  ↓
SQLite/filesystem

        ↙                 ↘
AASI Local Runner       Google Colab
OpenFOAM/Python         OpenFOAM/Python
```
