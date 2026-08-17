# HAQSETU

### Legal Awareness & Know-Your-Rights Platform

HAQSETU is a multilingual legal-awareness and Know-Your-Rights triage assistant designed to help citizens understand what may be happening in a real-world situation, what evidence they should preserve, what they can consider doing next, and where to find official legal-aid support.

The user does not need to understand legal terminology. They can explain what happened in **Hindi or English**, using **text or voice**, and HAQSETU converts that incident into structured, grounded legal-awareness guidance.

> **HAQSETU is a legal-awareness and navigation system, not a lawyer, law firm, or legal-advice/representation service.**

---

## ✨ What HAQSETU Does

A citizen describes an incident such as:

- Unpaid wages
- Workplace termination or exploitation
- Tenancy or eviction problems
- Other supported rights-related incidents

HAQSETU processes the incident and produces:

1. **Issue identification**
2. **Jurisdiction**
3. **Urgency**
4. **Grounded legal-awareness guidance**
5. **Evidence to preserve**
6. **Concrete next steps**
7. **Official legal sources**
8. **A visible legal-aid path**

The evidence and legal-aid recommendations are resolved by deterministic backend modules rather than being invented by the LLM.

---

## 🏗️ Architecture

HAQSETU uses a **single FastAPI backend application**.

There is intentionally **no separate AI server**. The AI/RAG pipeline runs in-process inside the FastAPI application.

```text
┌─────────────────────────────────────────────┐
│                  Citizen                    │
│          Hindi / English • Text / Voice     │
└──────────────────────┬──────────────────────┘
                       │
                       │ HTTPS + JWT
                       ▼
┌─────────────────────────────────────────────┐
│              React + Vite Frontend          │
│          Tailwind CSS + shadcn/ui           │
└──────────────────────┬──────────────────────┘
                       │ fetch()
                       ▼
┌─────────────────────────────────────────────┐
│              FastAPI Application            │
│                                             │
│  Auth Router                                │
│  Incident Router                            │
│  Evidence Router                            │
│  Legal Aid Router                           │
│                                             │
│  Incident Service                           │
│        │                                    │
│        └── triage.run()                     │
│              ├── Speech-to-Text             │
│              ├── Understanding              │
│              ├── Classification             │
│              ├── Retrieval                  │
│              ├── Grounded Generation       │
│              └── Validation                 │
└───────────────┬─────────────────────────────┘
                │
       ┌────────┴──────────┐
       ▼                   ▼
┌───────────────┐   ┌────────────────────────┐
│ PostgreSQL    │   │ Curated Legal Corpus    │
│               │   │ + FAISS Index          │
│ Users         │   │ + Embeddings           │
│ Context       │   │ + OpenRouter LLM       │
│ Incidents     │   └────────────────────────┘
│ Triage        │
│ Evidence      │
│ Legal Aid     │
└───────────────┘
```

### Why one FastAPI application?

The backend and AI/ML pipeline intentionally live in the same Python process.

This avoids:

- A separate AI deployment
- An additional network hop
- A second backend service
- Duplicated authentication or API boundaries

The incident flow is:

```text
Incident Router
      ↓
Incident Service
      ├── Load optional user context
      ├── triage.run()
      ├── Resolve evidence
      ├── Resolve legal aid
      ├── Persist result
      └── Compose public response
```

---

## 🧠 AI / RAG Pipeline

HAQSETU uses a curated legal corpus rather than unrestricted web search.

```text
User Incident
      │
      ▼
   STT (voice)
      │
      ▼
 Understanding
      │
      ├── structured extraction
      └── issue classification
      │
      ▼
 Jurisdiction + Urgency
      │
      ▼
 Embedding
      │
      ▼
 FAISS Retrieval
      │
      ▼
 Grounded Generation
      │
      ▼
 Output Validation
      │
      ▼
 Triage Result
```

### AI technologies

| Component | Technology |
|---|---|
| Speech-to-Text | `faster-whisper` |
| Embeddings | `intfloat/multilingual-e5-small` |
| Vector Search | FAISS `IndexFlatIP` |
| LLM | OpenRouter |
| Backend | FastAPI / Python |
| Validation | Pydantic |

The legal corpus and FAISS index are stored locally with the project.

---

## 🔐 Authentication

HAQSETU uses stateless JWT authentication.

Flow:

```text
Phone Number
     ↓
POST /auth/request-otp
     ↓
OTP Verification
     ↓
POST /auth/verify-otp
     ↓
JWT
     ↓
Authorization: Bearer <token>
```

The MVP uses a development/mock OTP rather than real SMS delivery.

Default development OTP:

```text
123456
```

JWTs are stored client-side for the MVP.

---

## 📱 Frontend Flow

The main user journey is:

```text
Landing
   ↓
Login / OTP
   ↓
Optional Context
   ↓
Incident Intake
   ↓
Processing
   ↓
Legal Awareness Result
```

The result page displays:

- Incident summary
- Identified issue
- Urgency
- Evidence checklist
- Recommended next steps
- Official legal sources
- Legal-aid contact
- Legal disclaimer

---

## 🌐 API

Important endpoints include:

### Health

```http
GET /health
```

Example:

```json
{
  "success": true,
  "data": {
    "status": "ok"
  },
  "error": null
}
```

### Authentication

```http
POST /auth/request-otp
POST /auth/verify-otp
```

### User Context

```http
PUT /users/context
```

### Incidents

```http
POST /incidents
GET /incidents/{id}
```

### Evidence

```http
GET /evidence
```

### Legal Aid

```http
GET /legalaid
```

All API responses follow the project's common response envelope.

---

# 📂 Repository Structure

```text
HAQSETU/
│
├── ps25/
│   │
│   ├── backend/
│   │   ├── auth/
│   │   ├── common/
│   │   ├── evidence/
│   │   ├── incident/
│   │   ├── legalaid/
│   │   ├── triage/
│   │   │   └── corpus/
│   │   │       ├── documents/
│   │   │       └── index/
│   │   └── main.py
│   │
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   │   └── results/
│   │   │   ├── lib/
│   │   │   └── pages/
│   │   └── package.json
│   │
│   ├── scripts/
│   │   ├── build_corpus_index.py
│   │   └── seed_static_data.py
│   │
│   ├── tests/
│   │   ├── test_incident.py
│   │   ├── test_triage_deterministic.py
│   │   └── test_triage_transcript.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

# ⚙️ Local Development

## Prerequisites

Recommended versions:

- Python 3.12
- Node.js 20 LTS
- PostgreSQL 16
- npm

---

## 1. Clone the repository

```bash
git clone https://github.com/ishaan83s/HAQSETU.git
cd HAQSETU
```

---

# 🐍 Backend Setup

```bash
cd ps25
```

Create/activate the virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Fill in the required values.

### Required backend variables

```env
DATABASE_URL=
JWT_SECRET=

OPENROUTER_API_KEY=
OPENROUTER_MODEL_PRIMARY=
OPENROUTER_MODEL_FALLBACK=

CORS_ORIGINS=
```

Optional configuration includes:

```env
MOCK_OTP=123456
EMBEDDING_MODEL=intfloat/multilingual-e5-small
WHISPER_MODEL_SIZE=small
```

---

## 2. Start the backend

From:

```text
HAQSETU/ps25
```

run:

```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn main:app --host 0.0.0.0 --port 8000
```

Expected:

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

---

## 3. Verify backend health

Open another terminal:

```bash
curl -i http://localhost:8000/health
```

Expected:

```text
HTTP/1.1 200 OK
```

---

# ⚛️ Frontend Setup

Open another terminal:

```bash
cd ~/HAQSETU/ps25/frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
.env.local
```

with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then run:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# 🧪 Frontend Build

To verify the production build:

```bash
cd ~/HAQSETU/ps25/frontend
npm run build
```

The build runs:

```text
tsc -b && vite build
```

and generates:

```text
dist/
```

---

# 🧪 Testing

The project includes tests for the major backend and triage paths.

Run:

```bash
cd ~/HAQSETU/ps25
source .venv/bin/activate
pytest
```

The testing contract covers:

- Authentication
- OTP verification
- JWT issuance
- Protected endpoints
- Text incidents
- Voice incidents
- Input validation
- STT failures
- Retrieval failures
- Generation failures
- Triage failures
- Incident persistence
- Incident ownership
- Evidence resolution
- Legal-aid resolution
- Deterministic triage behavior

---

# 🌍 Deployment Architecture

The intended deployment architecture is:

```text
Frontend
   ↓
Vercel
   ↓
FastAPI Backend
   ↓
Render
   ↓
Supabase PostgreSQL
```

The backend also uses:

```text
OpenRouter
FAISS
faster-whisper
sentence-transformers
```

### Backend

Build:

```bash
pip install -r requirements.txt
```

Start:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend

Build:

```bash
npm run build
```

Output:

```text
dist/
```

The frontend deployment requires:

```env
VITE_API_BASE_URL=<deployed-backend-url>
```

CORS must be configured to allow the exact deployed frontend origin.

---

# 🔬 Demo / End-to-End Verification

The core flow can be tested locally with:

```text
http://localhost:5173
```

### Test flow

```text
Landing
   ↓
Start Intake Flow
   ↓
Login
   ↓
Request OTP
   ↓
Verify OTP
   ↓
Context
   ↓
Skip for now
   ↓
Incident
   ↓
Enter incident
   ↓
Get guidance
   ↓
POST /incidents
   ↓
Triage + RAG + persistence
   ↓
GET /incidents/{id}
   ↓
Results
```

A successful result should contain:

- Issue classification
- Urgency
- Incident understanding
- Evidence to preserve
- Next steps
- Grounded official sources
- Legal-aid information
- Legal disclaimer

---

# 🎯 MVP Scope

HAQSETU's MVP is intentionally focused.

### Supported

- Hindi / English
- Text input
- Voice input
- Legal-awareness triage
- Maharashtra jurisdiction
- Curated legal corpus
- Evidence guidance
- Official source grounding
- Legal-aid navigation
- JWT authentication

### Explicitly out of scope

The MVP does **not** attempt to provide:

- Full India-wide legal coverage
- Legal certainty
- Case-outcome prediction
- Real SMS OTP delivery
- Live NALSA / Tele-Law API integration
- Court or e-filing integration
- Biometric authentication
- Custom model training/fine-tuning
- Generic unrestricted legal chat
- Full legal document drafting
- Production-grade rate limiting

---

# ⚠️ Legal Disclaimer

HAQSETU provides **legal awareness and navigation support**.

It does not provide:

- Legal advice
- Legal representation
- Guaranteed legal outcomes
- A lawyer-client relationship

Users should consult a qualified legal professional or appropriate official authority for advice regarding their specific circumstances.

---

# 🔒 Security Notes

Do not commit:

```text
.env
.env.local
```

Never expose:

- `JWT_SECRET`
- `DATABASE_URL`
- `OPENROUTER_API_KEY`

The project intentionally uses a development/mock OTP for the MVP.

For production deployment, authentication, secrets management, rate limiting, monitoring, and other security controls should be strengthened.

---

# 📜 Source of Truth

The implementation follows the **PS25 Modular SSOT v2.0** specification.

The SSOT package contains:

| Document | Purpose |
|---|---|
| `00_MASTER_INDEX.md` | Precedence and global rules |
| `01_product_architecture_ssot.md` | Product and architecture |
| `02_database_data_ssot.md` | Database and DTOs |
| `03_api_auth_security_ssot.md` | API, authentication and security |
| `04_ai_core_ssot.md` | AI/ML pipeline |
| `05_rag_corpus_ssot.md` | RAG and corpus |
| `06_evidence_legalaid_ssot.md` | Evidence and legal aid |
| `07_frontend_ssot.md` | Frontend |
| `08_interfaces_ownership_ssot.md` | Interfaces and ownership |
| `09_engineering_testing_deployment_ssot.md` | Testing and deployment |
| `10_cross_ssot_consistency_matrix.md` | Cross-module consistency |

---

# 🚀 Project Status

**PS-25 MVP — Integrated and End-to-End Tested**

The following flow has been verified against the running system:

```text
Frontend
   ↓
JWT Authentication
   ↓
Incident Submission
   ↓
FastAPI
   ↓
AI / RAG Pipeline
   ↓
PostgreSQL Persistence
   ↓
Incident Retrieval
   ↓
Real Results Page
```

A real incident was successfully processed into a persisted result containing issue identification, evidence guidance, official legal sources, next steps, and legal-aid information.

---

## Built for PS-25

**HAQSETU — Legal awareness made accessible.**
