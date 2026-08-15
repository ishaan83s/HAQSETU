# HAQSETU
Legal Aid & Evidence Platform

## Overview

PS-25 Modular SSOT — Legal-awareness and Know-Your-Rights triage assistant for multilingual (Hindi/English) citizens.

Built with the SSOT-driven modular architecture.

### Architecture

- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui (Vercel)
- **Backend**: FastAPI + SQLAlchemy + Pydantic (Render)
- **Database**: PostgreSQL (Supabase / Supavisor)
- **Auth**: JWT stateless (`python-jose`, HS256)
- **AI/ML**: local faster-whisper (STT), in-process FAISS (retrieval), OpenRouter LLM (generation)

### Repository Structure

```
ps25/
├── frontend/       — React + Vite app
├── backend/        — FastAPI application
├── docs/           — Documentation
├── tests/          — Shared tests
├── .env.example    — Environment variable template
└── README.md
```

### Quick Start

#### Backend

```bash
cd ps25/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd ps25/frontend
npm install
npm run dev
```

#### Health Check

```
GET http://localhost:8000/health
```

### SSOT Files

See `PS25_Modular_SSOTs_v1.0/` for authoritative specifications.

### License

Proprietary — HAQSETU Project
