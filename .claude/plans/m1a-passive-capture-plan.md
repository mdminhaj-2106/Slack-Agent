# Implementation Plan: Milestone 1a — Passive Capture & Ephemeral Confirmation Loop (LangChain & LangGraph Edition)

This updated plan outlines the architecture, directory structure, module responsibilities, and step-by-step code implementation to build the passive detection and consent-based decision capture flow (M1a). It uses a modular domain-driven structure and integrates **LangChain** and **LangGraph** for the classification pipeline.

---

## 🏗️ Directory & File Structure
To ensure modularity and scalability as the codebase grows, we organize the application into domain directories (`handlers/`, `slack_app/`, `ai/`):

```text
Slack-Agent/
  ├── main.py                     - Entrypoint (FastAPI + Socket Mode thread startup)
  ├── config.py                   - Configuration parser (Settings class)
  ├── requirements.txt            - Dependencies
  │
  ├── handlers/                   - Controller layer: Entrypoints for Slack payloads
  │   ├── __init__.py             - Router registry wrapper
  │   ├── events.py               - message/app_mention event listeners & worker thread
  │   └── actions.py              - confirm_log/dismiss_log action listeners & worker thread
  │
  ├── slack_app/                  - View/Persistence layer: Slack Web API, layouts, and schema
  │   ├── __init__.py
  │   ├── canvas.py               - Slack Canvas API editing functions
  │   ├── blocks.py               - Ephemeral & status Block Kit templates
  │   ├── formatter.py            - Formats data into Canvas-compliant markdown list items
  │   └── schemas.py              - PointerRecord validation schema
  │
  └── ai/                         - Intelligence layer: AI / LangGraph / Classifier
      ├── __init__.py
      ├── llm.py                  - LLM Client initializer (exposes reusable ChatGoogleGenerativeAI)
      ├── classifier.py           - LangGraph state graph classification workflow
      ├── state.py                - Graph state TypedDict definition
      └── schemas.py              - Structured output validation schema (ClassificationResult)
```

---

## 📝 Detailed Module Explanations & Responsibilities

### 1. Requirements Setup
*   **File:** `requirements.txt`
*   **Action:** Add the following dependencies:
    *   `pydantic>=2.0.0` (FastAPI-compatible data validations)
    *   `langchain>=0.2.0` (core orchestration)
    *   `langchain-google-genai>=1.0.0` (Gemini API bridge)
    *   `langgraph>=0.1.0` (stateful workflow engine)

### 1.5 Configuration Layer
*   **File:** `config.py`
*   **Class:** `Settings`
*   **Explanation:** Loads variables from `.env` using `load_dotenv` and populates configuration fields (`SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`, `GEMINI_API_KEY`, `SLACK_CANVAS_ID`). A single global instance `settings` is exported for use across all files.

### 2. Slack Persistence & UI Layouts (`slack_app/`)
*   **File:** `slack_app/schemas.py`
    *   **Class:** `PointerRecord` (inherits `pydantic.BaseModel`)
    *   **Explanation:** Represents our evidence database schema (`channel_id`, `ts`, `permalink`, `type`, `owner_id`, `confidence`, `status`).
*   **File:** `slack_app/canvas.py`
    *   **Function:** `write_pointer_to_canvas(client: WebClient, canvas_id: str, pointer: PointerRecord) -> bool`
    *   **Explanation:** Edits the target team Canvas using the `canvases.edit` API. It strictly rejects any writes containing raw message text or custom LLM-generated summaries to maintain document security.
*   **File:** `slack_app/blocks.py`
    *   **Function:** `get_ephemeral_confirm_blocks(user_id: str, category: str, payload_value: str) -> list[dict]`
        *   *Explanation:* Builds the Block Kit payload for the confirmation prompt containing the `✓ Log` and `✗ Dismiss` interactive buttons.
    *   **Function:** `get_logged_success_blocks(user_id: str, category: str) -> list[dict]`
        *   *Explanation:* Builds a success block to overwrite the buttons once confirmed.
    *   **Function:** `get_dismissed_blocks() -> list[dict]`
        *   *Explanation:* Builds a dismissed status block to clean up the ephemeral message.
*   **File:** `slack_app/formatter.py`
    *   **Function:** `format_pointer_as_markdown(pointer: PointerRecord) -> str`
    *   **Explanation:** Serializes the pointer object into a single markdown list item featuring the permalink and owner user tag (which Slack natively unfurls for context).
        `• ![](@owner_id) | *{type.capitalize()}* | Status: \`{status}\` | Link: <{permalink}>`

### 3. Controller Layer (`handlers/`)
*   **File:** `handlers/events.py`
    *   **Listeners:** `message` and `app_mention` events.
    *   **Explanation:** Captures raw messages, filters out bots, ack events, and fires a background thread to invoke the classifier and post the ephemeral confirmation prompt.
*   **File:** `handlers/actions.py`
    *   **Listeners:** Button click actions (`confirm_log` and `dismiss_log`).
    *   **Explanation:** Intercepts button clicks, ack actions, writes confirmed pointers to the Canvas using `slack_app/canvas.py`, and updates the ephemeral UI state.

### 4. AI Domain Layer (`ai/`)
*   **File:** `ai/llm.py`
    *   **Explanation:** Exposes a reusable `ChatGoogleGenerativeAI` wrapper initialized using centralized `settings.GEMINI_API_KEY`.
*   **File:** `ai/schemas.py`
    *   **Class:** `ClassificationResult`
    *   **Explanation:** Defines LLM output fields (`category`, `confidence`, `owner_id`, `due_date_hint`).
*   **File:** `ai/state.py`
    *   **Class:** `ClassifierState` (inherits `typing.TypedDict`)
    *   **Explanation:** Holds graph state (`message_text`, `sender_id`, `result`).
*   **File:** `ai/classifier.py`
    *   **Explanation:** Sets up the `StateGraph`, defines the classifier node, compiles the graph, and exposes the entrypoint `classify_text`.

---

## 🛠 Step-by-Step Execution Plan

### Step 1: Install Dependencies
Update `requirements.txt` and install:
```bash
pip install langchain langchain-google-genai langgraph pydantic
```

### Step 2: Establish the Configuration Layer
1.  Create `config.py` defining the settings parser.

### Step 3: Establish the AI Domain
1.  Create `ai/llm.py` to instantiate and configure `ChatGoogleGenerativeAI`.
2.  Create `ai/schemas.py` and `ai/state.py`.
3.  Create `ai/classifier.py` using `get_llm()`, `ClassifierState`, and `ClassificationResult`.

### Step 4: Establish the Slack Domain
1.  Create `slack_app/schemas.py`.
2.  Create `slack_app/blocks.py` and `slack_app/formatter.py`.
3.  Create `slack_app/canvas.py`.

### Step 5: Establish the Controller Domain
1.  Create `handlers/events.py` and `handlers/actions.py`.
2.  Create `handlers/__init__.py` exposing `register_handlers(slack_app)` to register listeners on the global app object.

### Step 6: Orchestrate and Validate
1.  Refactor `main.py` to register all listeners on the global `slack_app` object using `handlers.register_handlers`.
2.  Run the validation checklist:
    *   Syntax validation: `python -m py_compile main.py`
    *   Run process locally: `python main.py`
    *   Smoke test Slack interactions.
