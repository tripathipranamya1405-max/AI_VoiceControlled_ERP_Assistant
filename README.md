# AI Voice-Controlled ERP Assistant

A local prototype that lets users query and manage sample ERP data through a
web chat interface or voice input. The application combines a FastAPI backend,
a browser-based dashboard, a dialog manager, intent/entity recognition, and a
SQLite-backed mock ERP.

> **Prototype notice:** This project uses sample data and is intended for local
> evaluation. Its built-in demo credentials and in-memory sessions are not
> suitable for production or for use with real ERP data.

## Features

- Inventory search, stock levels, and low-stock/reorder alerts.
- Attendance lookup and supported attendance workflows.
- Expense summaries and purchase-request workflows with confirmation.
- Sales summaries and downloadable CSV/PDF reports.
- Role-aware sign-in for guest, finance, and sales users.
- Rule-based natural-language understanding by default, with optional local
  Ollama-based NLU.
- Optional offline speech recognition with Vosk and speech synthesis with
  `pyttsx3`.
- Sample ERP data stored in SQLite; no external ERP connection is required.

## Project layout

The application is under [`voice_erp_assistant/`](./voice_erp_assistant/).

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI application and HTTP endpoints |
| `app/database.py` | SQLite schema, sample data, and ERP operations |
| `app/nlu.py`, `app/nlu_llm.py`, `app/intents.py` | Rule-based and optional LLM-based intent recognition |
| `app/dialog_manager.py`, `app/entity_resolver.py` | Conversation flow, clarification, and entity matching |
| `app/erp_gateway.py` | Role permissions and dispatch to ERP operations |
| `app/auth.py` | Prototype authentication and session handling |
| `app/reporting.py` | Sales report generation |
| `app/stt.py`, `app/tts.py` | Optional speech recognition and synthesis |
| `static/` | Browser user interface |
| `models/` | Bundled Vosk speech-recognition model |
| `tests/` | Automated tests |
| `demo.py` | Command-line demonstration |

For detailed workflows, roles, API examples, and extension notes, see the
[application guide](./voice_erp_assistant/README.md).

## Requirements

- Python 3.10 or later.
- Windows, macOS, or Linux.
- `ffmpeg` on `PATH` for audio conversion in the voice workflow.
- Optional: Ollama and a downloaded model for LLM-based NLU.
- Optional: `pyttsx3` for text-to-speech (it is not installed by the default
  requirements file).

## Installation

From the repository root, open PowerShell and run:

```powershell
cd voice_erp_assistant
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell prevents virtual-environment activation, run the commands below
using the environment's Python executable instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the application

### Command-line demo

From `voice_erp_assistant/`, run:

```powershell
python demo.py
```

This exercises the text-based ERP workflows without needing a microphone,
Ollama, or external credentials.

### Web application

From `voice_erp_assistant/`, start the local server:

```powershell
uvicorn app.main:app --reload
```

Then open:

- Web application: <http://127.0.0.1:8000/>
- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

Stop the development server with `Ctrl+C`.

## Sign-in and configuration

The local prototype includes guest access and sample employee accounts:

| Role | Username | Password |
|---|---|---|
| Finance | `finance` | `Finance@123` |
| Sales | `sales` | `Sales@123` |

These are public demo credentials for sample data only. Do not deploy the app
with them or connect them to real business data. The application guide
describes environment variables for replacing credentials and controlling
authentication, guest access, and secure cookies.

## Optional voice input and output

The repository includes a Vosk model. Install `ffmpeg` and ensure it is on
`PATH` for audio conversion. To use a different model directory, set
`VOSK_MODEL_PATH`. For speech synthesis, install `pyttsx3` in the active
environment:

```powershell
python -m pip install pyttsx3
```

The browser's Record control sends audio to the local `/voice/audio` endpoint.
Text input remains available without microphone or speech dependencies.

## Optional local LLM-based NLU

The default NLU engine uses local rules and needs no API key. To use a local
Ollama model, install Ollama, download a model such as `llama3.2:1b`, and set
the engine in PowerShell before starting the application:

```powershell
ollama pull llama3.2:1b
$env:NLU_ENGINE = "llm"
uvicorn app.main:app --reload
```

Omit that environment variable (or set it to `rule`) to use the default
rule-based engine.

## Run tests

From `voice_erp_assistant/`, run:

```powershell
python -m unittest discover -s tests -v
```

## Security and production limitations

This is a demonstration application, not a production-ready ERP system.
Authentication and session state are prototype implementations, sessions are
stored in process memory, and the ERP database contains sample data. Before
production use, replace demo credentials, use a managed identity provider and
shared session store, configure HTTPS and secure cookies, and connect only
through appropriately secured ERP APIs.
