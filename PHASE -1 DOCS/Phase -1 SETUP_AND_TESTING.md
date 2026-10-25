# Setup and Testing Guide: Phase 1 — JD Analysis Tool

---

## 1. Prerequisites

Before installing and running the JD Analysis Tool, make sure your environment meets the following requirements:

* **Python (Version 3.10 or higher):** Required to run all core backend services, scripts, and the Streamlit dashboard. You can verify your installation via `python --version`.
* **pip:** Python's package installer, which is included by default with standard Python installations.
* **Git:** Required if you are cloning the repository from version control.
* **Google Gemini API Key:** Required for LLM extraction (`JDExtractorService`). You can obtain a free-tier or paid API key from Google AI Studio.
* **Windows PowerShell:** The primary command-line shell used for running commands in this guide.

---

## 2. Obtaining and Preparing the Project

If you have downloaded or cloned the project repository locally, open **Windows PowerShell** and navigate to your project root directory:

```powershell
cd path\to\jd_analysis_tool

```

* **`cd`**: Changes the current working directory in PowerShell to point directly to the project folder.

---

## 3. Python Virtual Environment Setup

Using a virtual environment ensures that project dependencies remain isolated from your global Python installation.

### Creating the Virtual Environment

Run the following command in your project root to create a local virtual environment named `.venv`:

```powershell
python -m venv .venv

```

* **`python -m venv .venv`**: Tells Python to build a fresh virtual environment folder called `.venv` in your workspace.

### Activating the Virtual Environment

Activate the environment using PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1

```

* **Successful Activation:** Once activated, your PowerShell prompt will typically prefix your path with `(.venv)`.
* **PowerShell Execution Policy Error:** If PowerShell blocks script activation with a security error, you can temporarily allow script execution for your current session only without modifying system-wide security policies:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

```


* **Deactivation:** When you are done working, you can exit the virtual environment by typing:
```powershell
deactivate

```



### Verifying Python and Pip

Verify that your active environment points to the virtual environment binaries:

```powershell
python --version
python -m pip --version

```

---

## 4. Dependency Installation

The project dependencies are managed via `requirements.txt`. Install them by running:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

```

* **`python -m pip install -r requirements.txt`**: Reads every required library (such as `google-genai`, `pandas`, `streamlit`, `python-jobspy`, `pydantic`) and installs them into your active `.venv`.
* **Verification:** You can confirm successful package installation by listing installed packages:
```powershell
python -m pip list

```



---

## 5. Environment Variables and Configuration

The application requires configuration settings and your Gemini API key to operate correctly.

### Creating the `.env` File

Create a new file named `.env` in the root directory of your project (you can reference `.env.example` if present). Populate it with the following required and optional variables:

```env
GEMINI_API_KEY=your_actual_api_key_here
DEFAULT_MODEL_NAME=gemini-2.5-flash
DEFAULT_LOCATION=India
DEFAULT_RESULTS_LIMIT=15

```

### Configuration Variables Reference

| Variable | Required / Optional | Default Value | Purpose | Example |
| --- | --- | --- | --- | --- |
| **`GEMINI_API_KEY`** | **Required** | None | Authenticates requests to the Google Gemini API for LLM extraction. | `GEMINI_API_KEY=AIzaSy...` |
| **`DEFAULT_MODEL_NAME`** | Optional | `gemini-2.5-flash` | Specifies which Gemini model to use for structured extraction. | `DEFAULT_MODEL_NAME=gemini-2.5-flash` |
| **`DEFAULT_LOCATION`** | Optional | `India` | Default geographic scope for job scraper queries. | `DEFAULT_LOCATION=India` |
| **`DEFAULT_RESULTS_LIMIT`** | Optional | `15` | Default cap on how many results to fetch per job board. | `DEFAULT_RESULTS_LIMIT=20` |

* **How it's loaded:** `config/settings.py` utilizes `python-dotenv` to load these values into environment variables upon import.
* **Security Warning:** Never commit your `.env` file to GitHub. The project's `.gitignore` file explicitly excludes `.env` to protect your secret API keys.

---

## 6. First-Time Initialization

The application handles resource initialization automatically upon first execution:

* **Directories:** `config/settings.py` checks for and creates `data/raw/` and `data/processed/` automatically if they do not exist.
* **Database Tables:** `StorageManager` (`src/storage.py`) automatically creates the SQLite database (`data/raw/jobs.sqlite`) along with the `jobs` and `extractions` tables when first accessed.
* **Action Required:** No manual database migration or setup commands are necessary.

---

## 7. How to Run the Project

### A. Command-Line Interface (CLI)

You can run the full pipeline or individual stages via `main.py`.

* **Basic Full Pipeline Command:**
```python
python main.py --search "Full-Stack AI Engineer" --location "India" --limit 10 --extract --report

```


* **CLI Arguments Reference:**
* `--search`: Job search query keyword (e.g., `"Python AI Engineer"`).
* `--location`: Target location (e.g., `"Bengaluru"` or `"India"`).
* `--limit`: Maximum number of results to fetch per job board.
* `--extract`: Flag indicating whether to run Gemini LLM extraction on scraped jobs.
* `--report`: Flag indicating whether to generate CSV and Markdown analysis reports.



### B. Streamlit Dashboard

To launch the interactive web interface:

```powershell
python -m streamlit run ui/app.py

```

* **Accessing the App:** Streamlit will start a local server and output local URLs (typically `http://localhost:8501`) which you can open in any web browser.
* **Stopping the Server:** Press `Ctrl + C` in your PowerShell terminal.

### C. Behavior on Repeat Runs

* **Job Deduplication:** Scraping the same job listing multiple times will calculate the same SHA-256 `job_id`, and SQLite will ignore duplicates (`INSERT OR IGNORE`).
* **Extraction Caching:** `JDExtractorService` checks SQLite before calling the Gemini API. Already-extracted jobs return instantly with **0 API calls**.
* **Artifact Overwriting:** Running report generation overwrites existing files in `data/processed/` (`analyses.json`, `skill_demand.csv`, `market_report.md`) with fresh analytics.

---

## 8. Testing Strategy

### Level 1: Environment and Import Checks

Verify that Python can successfully load core settings and packages without syntax or import errors:

```powershell
python -c "import config.settings; print('Settings loaded successfully!')"
python -c "import src.models; print('Pydantic models imported successfully!')"

```

### Level 2: Component Verification (Unit & Storage)

You can test database storage and caching functionality in isolation:

```powershell
python -c "from src.storage import StorageManager; sm = StorageManager(); print('SQLite connected successfully at:', sm.db_path)"

```

### Level 3: Live End-to-End Pipeline Test (Safe / Limited)

To test the complete pipeline with a minimal footprint (fetching only 2 jobs to conserve API quotas and avoid rate limits):

```powershell
python main.py --search "Python Developer" --location "Remote" --limit 2 --extract --report

```

---

## 9. Troubleshooting Guide

| Error / Symptom | Likely Cause | How to Check | Suggested Solution |
| --- | --- | --- | --- |
| **`python: command not found`** | Python is not installed or not added to Windows PATH. | Run `python --version` in terminal. | Reinstall Python and ensure "Add python.exe to PATH" is checked during installation. |
| **`ModuleNotFoundError`** | Virtual environment is not activated or dependencies are missing. | Run `python -m pip list` to verify installed packages. | Activate your virtual environment (`.\.venv\Scripts\Activate.ps1`) and install requirements (`pip install -r requirements.txt`). |
| **`GEMINI_API_KEY not found`** | The `.env` file is missing, empty, or incorrectly named. | Check if `.env` exists in the project root. | Create a `.env` file containing your valid `GEMINI_API_KEY`. |
| **Naukri Scraper HTTP `406` / CAPTCHA** | Job board bot protection blocking automated scraping. | Inspect terminal logs for scraping errors. | This is a known external limitation; LinkedIn and Indeed will still collect successfully. |
| **Gemini API `503 UNAVAILABLE**` | Google Gemini servers experiencing high transient load. | Inspect traceback for service unavailability. | The built-in retry and backoff mechanism will handle temporary spikes automatically. Re-run your command if needed. |
| **Streamlit dashboard shows empty charts** | No processed report data exists in `data/processed/`. | Check if `analyses.json` or `skill_demand.csv` exists. | Run `python main.py --report` or run the full pipeline via CLI or UI button to generate data. |

---

## 10. Safety and Data Protection

* **Keep Secrets Private:** Never share or commit your `.env` file. Ensure `.env` is listed in your `.gitignore` file.
* **Database Backups:** Your raw job records and extractions are stored locally in `data/raw/jobs.sqlite`. Before making structural modifications or database experiments, make a safe backup copy of this file.
* **API Quota Management:** When testing extraction pipelines, always use small limits (`--limit 2` or `--limit 5`) to prevent unnecessary consumption of your Gemini API token quotas.

---

## 11. Expected Results

When the pipeline executes successfully:

1. **Terminal Output:** Displays logs indicating job collection progress, SHA-256 fingerprint generation, database insertion counts, cache hits/misses, and successful report generation.
2. **Generated Artifacts:**
* `data/raw/jobs.sqlite` (SQLite database containing raw jobs and extractions)
* `data/raw/jobs.csv` (CSV backup of scraped jobs)
* `data/processed/analyses.json` (Structured analysis data)
* `data/processed/skill_demand.csv` (Tabular skill demand percentages)
* `data/processed/market_report.md` (Executive markdown summary)


3. **Streamlit UI:** Displays key top-level metrics, interactive skill demand bar charts, and a rendered executive report with a download button.

---

### Verification Report

* **Path of the document created:** `docs/phase-1/SETUP_AND_TESTING.md`
* **Files and configuration sources inspected:** `README.md`, `requirements.txt`, `config/settings.py`, `.env.example`, `.gitignore`, `main.py`, `src/`, and `ui/app.py`.
* **Verified setup commands:** Virtual environment creation, activation, pip installation, configuration loading, CLI execution arguments, and Streamlit startup command.
* **Tests executed:** Environment import checks and storage connection verification.
* **Outstanding verification steps:** Live end-to-end extraction depends on active network connectivity and valid Gemini API key quotas.
* **Known setup blockers:** Naukri bot protection (HTTP 406) may block Naukri-specific scraping, which is isolated by design in the scraper service.