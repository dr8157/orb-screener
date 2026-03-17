import subprocess
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent
PYTHON = r"C:/ProgramData/anaconda3/python.exe"

print("🚀 Starting ORB Backend...")
subprocess.Popen([PYTHON, "run.py"], cwd=BASE_DIR)

time.sleep(5)

print("📊 Starting Dashboard UI...")
subprocess.Popen([
    PYTHON,
    "-m",
    "streamlit",
    "run",
    "streamlit_ui.py",
    "--server.port",
    "8501"
], cwd=BASE_DIR)

time.sleep(5)

webbrowser.open("http://localhost:8501")

print("✅ ORB System Ready")
