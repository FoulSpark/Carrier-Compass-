# Carrier Compass

Unified platform for helping Indian students explore careers, track admissions, and manage study resources. The repo combines multiple Flask services, reusable HTML prototypes, and automation scripts that surface AI-guided counseling, college discovery, and notification timelines under one roof.

## Highlights
- Personalized career counseling with persistent chat history, profile enrichment, and analytics powered by `login/app.py`.
- Location-aware college search microservice (`nearby_government_colleges_directory_2`) with caching, live map generation, and stream filters.
- One-click service orchestration via `run_all.py`, which validates dependencies, opens dedicated consoles, and waits for health checks.
- Modular front-end experiences (landing page, aptitude quiz, resources, timeline, profile) delivered as standalone HTML prototypes and templated views.
- SQLite-backed persistence (`ai_chat.db`) for users, conversations, preferences, and career recommendations.

## 🎥 Demo Video
[![Carrier Compass Walkthrough](https://img.youtube.com/vi/LDESbfSoMPw/hqdefault.jpg)](https://youtu.be/LDESbfSoMPw)


> Replace `VIDEO_ID` with the identifier of your published video (YouTube, Loom, etc.), or swap the thumbnail URL for a custom screenshot stored in the repository.
## Repository Layout
```
.
├── run_all.py                         # Multi-service launcher
├── requirements.txt                   # Python dependencies
├── package.json / node_modules        # Tailwind CLI dependencies
├── login/                             # Main Flask app (auth, chat, dashboards, APIs)
│   ├── app.py                         # Entry point for the primary web experience
│   ├── ai_chat.py                     # SQLite data access layer
│   ├── templates/                     # Jinja templates rendered by the Flask app
│   └── New TEMPLATES/                 # Alternate UI mockups
├── nearby_government_colleges_directory_2/  # College directory microservice
│   ├── app.py                         # Standalone Flask server & APIs
│   ├── start_college_app.py           # Dependency check + launcher wrapper
│   ├── college_cache.py               # Geo-cache for search results
│   └── templates/                     # Static HTML for the microservice
├── aptitude_&_interest_quiz_page_2/   # Quiz engine prototype and launcher scripts
├── course-to-career_path_mapping_2/   # Static career-path visualizations
├── landing_page_(homepage)_2/         # Home page prototype
├── study_material_&_resources_2/      # Study material portal mockups
├── timeline_tracker_(notifications)_2/ # Notification timeline UI
└── user_profile_&_personalization_2/  # Profile screens
```

## Prerequisites
- Python 3.10+ (tested on Windows)
- Node.js 18+ (for Tailwind CLI, if you intend to rebuild CSS)
- PowerShell or a Bash-compatible shell

## Setup
1. **Create and activate a virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Python dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Install Node/Tailwind tooling (optional)**
   ```powershell
   npm install
   ```
   Tailwind assets can then be rebuilt with:
   ```powershell
   npx tailwindcss -i input.css -o static/output.css --watch
   ```
   (Adjust input/output paths to match your workflow.)

## Running the Platform

### Option 1: Unified Launcher
Run every core service (main web app + college directory) in their own consoles:
```powershell
python run_all.py
```
`run_all.py` checks for missing files, confirms ports are free, starts each service, and waits until health checks succeed. Press `Ctrl+C` to gracefully stop all managed processes.

### Option 2: Start Services Manually
- **Main App (Flask on port 5000)**
  ```powershell
  python login/app.py
  ```
- **College Directory (Flask on port 5002)**
  ```powershell
  python nearby_government_colleges_directory_2/start_college_app.py
  ```
- **Aptitude & Interest Quiz**
  Refer to scripts in `aptitude_&_interest_quiz_page_2/` (`start_career_system.py`, `start_server.py`, etc.) to launch quiz-related prototypes as needed.

## Key Components
- **Authentication & Profiles:** User registration/login flows store hashed credentials and profile metadata through `ai_chat.py`.
- **AI Career Guidance:** Multiple chat endpoints (`/chat`, `/api/chat`, `/career_guidance_chat`, `/api/career_chat`) orchestrate Hugging Face, optional Ollama, and rule-based fallbacks for Indian education guidance.
- **Notifications & Timeline:** Dynamic notification feed with priority sorting plus timeline UI templates for exam reminders and scholarship alerts.
- **College Discovery:** `/api/search`, `/api/cache/*`, and `/maps/<filename>` endpoints provide cached queries, interactive folium maps, and geo-filtered discovery.
- **Static UX Modules:** Each `_2` directory contains polished HTML/CSS drafts that the Flask apps can serve directly or embed as templates.

## Data & Persistence
- SQLite database files (`ai_chat.db`, `career_results.json`, cached maps) ship with the repository for local experiments.
- To reset the main chat database, delete `login/ai_chat.db` (a fresh copy will be created by `ai_chat.init_db()` on next run).
- College cache artifacts live in `nearby_government_colleges_directory_2/college_cache.*`.

## Development Tips
- The main Flask app automatically initializes required tables on startup.
- Ensure ports `5000` and `5002` are free before launching; `run_all.py` skips services bound to busy ports.
- When editing templates, prefer the versions under `login/templates/` which are wired into Flask routes.
- For Tailwind-enabled styles, adjust `input.css` and rebuild via the CLI command shown above.

## Troubleshooting
- **Missing Python packages:** Re-run `pip install -r requirements.txt`; the college launcher will attempt to install essentials automatically.
- **Service health checks fail:** Verify that the Flask apps are reachable (`curl http://127.0.0.1:5000/`), and inspect terminal logs for stack traces.
- **SQLite locking issues on Windows:** Stop all running services before deleting or editing `.db` files.

## Next Steps
- Add unit tests for core services (auth, college search).
- Parameterize API keys/secrets via environment variables rather than hardcoded defaults.
- Containerize services for reproducible deployment (Docker Compose with shared volumes for SQLite).

Happy building!

