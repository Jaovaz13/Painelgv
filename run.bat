@echo off
echo ==========================================
echo      Painel Socioeconomico - Deployment
echo ==========================================

:: Check for venv
if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] No .venv found, using system python.
)

:: Install dependencies (optional, but good for first run)
echo [INFO] Checking dependencies...
pip install -r requirements.txt

:: Start Scheduler
echo [INFO] Starting Scheduler service (Background)...
start "Painel Scheduler" /MIN python -m scheduler.update

:: Start Dashboard
echo [INFO] Starting Streamlit Dashboard...
streamlit run app.py
