"""
ORB Institutional Screener - Run Script
File: run.py
(UPDATED for automated Kite authentication)
"""

import subprocess
import sys
from pathlib import Path


def print_banner():
    print("\n" + "=" * 70)
    print("  ORB INSTITUTIONAL SCREENER")
    print("  Opening Range Breakout Strategy Scanner")
    print("=" * 70 + "\n")


def check_files():
    """Check required files"""
    required = [
        'main.py',
        'models.py',
        'baseline_engine.py',
        'live_stream_engine.py',
        'scoring_engine.py',
        'kite_credentials.py',
        'requirements.txt'
    ]

    missing = [f for f in required if not Path(f).exists()]

    if missing:
        print("[X] Missing files:")
        for f in missing:
            print(f"   - {f}")
        return False

    print("[OK] All files found")
    return True


def check_credentials():
    """
    Validate Kite credentials using REAL authentication
    (token.txt / auto-login aware)
    """
    try:
        from kite_credentials import API_KEY, get_kite_instance

        if not API_KEY or API_KEY == "your_api_key_here":
            print("\n❌ Kite API_KEY not configured!")
            print("Set API_KEY and API_SECRET in credentials.json")
            return False

        # Actual authentication test
        kite = get_kite_instance()
        profile = kite.profile()

        print(f"[OK] Credentials configured | User: {profile['user_name']}")
        return True

    except ImportError as e:
        print("[X] Cannot import kite_credentials.py")
        print(e)
        return False

    except Exception as e:
        print("[X] Kite authentication failed")
        print(e)
        return False


def install_deps():
    """Install dependencies"""
    print("\nInstalling dependencies...")

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", "requirements.txt", "--quiet"
        ])
        print("[OK] Dependencies installed")
        return True
    except Exception as e:
        print("[X] Failed to install dependencies")
        print(e)
        return False


def start_server():
    """Start FastAPI server"""
    print("\n" + "=" * 70)
    print("Starting ORB Screener Backend...")
    print("=" * 70)
    print("\n> Server: http://localhost:8000")
    print("> API Docs: http://localhost:8000/docs")
    print("> WebSocket: ws://localhost:8000/ws/stream")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 70 + "\n")

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "warning"  # Reduce noise - only show warnings/errors
        ])
    except KeyboardInterrupt:
        print("\n\n[OK] Server stopped")
    except Exception as e:
        print(f"\n[X] Error starting server: {e}")


def main():
    """Main entry point"""
    print_banner()

    if not check_files():
        sys.exit(1)

    if not check_credentials():
        print("\n" + "=" * 70)
        print("Setup required")
        print("=" * 70)
        sys.exit(1)

    # Start server directly without prompting
    start_server()


if __name__ == "__main__":
    main()
