#!/usr/bin/env python3
"""
Main entry point for backend server
"""

import os
import sys
import uvicorn
import subprocess
from pathlib import Path

# ==============================
# FORCE UTF-8 (Windows Fix)
# ==============================
sys.stdout.reconfigure(encoding="utf-8", errors="ignore")

# ==============================
# CRITICAL PATH SETUP FIX
# ==============================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
SRC_DIR = BASE_DIR / "src"

# Add src directory FIRST
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(PROJECT_ROOT))


# ==============================
# REQUIREMENT CHECK
# ==============================
def check_requirements():
    print("Checking requirements...")

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        print(f"OK .env file found: {env_path}")
    else:
        print("ERROR .env file missing")
        return False

    ml_models_path = BASE_DIR / "ml_models"
    if ml_models_path.exists():
        models = list(ml_models_path.glob("*.pkl"))
        print(f"OK Found {len(models)} ML model(s)")
    else:
        print("WARNING ml_models folder missing")

    print(f"Python executable: {sys.executable}")

    if ".venv" in sys.executable.lower() or "venv" in sys.executable.lower():
        print("OK Running inside virtual environment")
    else:
        print("WARNING Not inside virtual environment")

    return True


# ==============================
# LOAD ENVIRONMENT
# ==============================
def load_environment():
    try:
        from dotenv import load_dotenv
        env_path = BASE_DIR / ".env"
        load_dotenv(env_path)
        print("OK Environment variables loaded")
        return True
    except Exception as e:
        print("Failed loading .env:", e)
        return False


# ==============================
# START ACTIVITY LOGGER
# ==============================
def start_activity_logger():

    logger_path = SRC_DIR / "laptop_collector" / "activity_logger.py"

    if not logger_path.exists():
        print("WARNING activity_logger.py not found")
        return

    try:
        import psutil

        for proc in psutil.process_iter(['cmdline']):
            cmdline = proc.info.get('cmdline')
            if cmdline and "activity_logger.py" in " ".join(cmdline):
                print("Activity Logger already running")
                return

        subprocess.Popen(
            [sys.executable, str(logger_path)],
            cwd=str(logger_path.parent)
        )

        print("OK Activity Logger started")

    except Exception as e:
        print("Failed to start activity logger:", e)

# ==============================
# START SERVER
# ==============================
def main():

    print("=" * 60)
    print("Digital Fatigue Guard - Backend Server")
    print("=" * 60)
    print("Backend directory:", BASE_DIR)
    print("Project root:", PROJECT_ROOT)
    print("SRC directory:", SRC_DIR)

    print("Python path:")
    for p in sys.path[:3]:
        print(f"  - {p}")

    if not check_requirements():
        print("Setup incomplete.")
        return

    if not load_environment():
        print("Environment load failed.")
        return

    start_activity_logger()

    print("\nStarting FastAPI server...")
    print("API Docs: http://localhost:8000/docs")
    print("Health:   http://localhost:8000/health")
    print("=" * 60)

    try:
        uvicorn.run(
            "src.app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print("Server failed:", e)


if __name__ == "__main__":
    main()