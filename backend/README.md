# AASI Backend

FastAPI backend service and agent orchestration layer for **AASI** (Autonomous Aerospace Scientific Intelligence).

## Purpose & Scope

The backend serves as the bridge between user clients (Next.js frontend) and local open-weight model runtimes (Ollama). It handles:
- Request validation via Pydantic.
- System prompt formulation with domain constraints (aerospace, physics, mathematics).
- Runtime health monitoring and error reporting for Ollama.
- Structured response dispatching.

## Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- Ollama installed and running locally

## Setup & Running

1. Create and activate a Python virtual environment:

   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables (optional):

   ```powershell
   cp backend/.env.example backend/.env
   ```

4. Start the FastAPI development server:

   ```powershell
   uvicorn backend.main:app --reload --port 8000
   ```

5. Explore the interactive API documentation at `http://localhost:8000/docs`.

## API Endpoints

- `GET /api/health`: Check backend status, version, and Ollama connectivity.
- `POST /api/chat`: Send prompt to AASI agent and receive generated response.
