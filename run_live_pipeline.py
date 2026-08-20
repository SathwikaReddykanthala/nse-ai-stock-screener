import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

SCRIPTS = [
    ROOT / "src" / "live_smma.py",
    ROOT / "src" / "live_ml_features.py",
    ROOT / "src" / "live_ai_signal.py",
]

print("=" * 70)
print("STOCKAI — LIVE PROCESSING PIPELINE")
print("=" * 70)

while True:

    for script in SCRIPTS:

        print()
        print("=" * 70)
        print(f"RUNNING: {script.name}")
        print("=" * 70)

        try:
            result = subprocess.run(
                [str(PYTHON), str(script)],
                cwd=str(ROOT),
                capture_output=False
            )

            if result.returncode != 0:
                print(
                    f"{script.name} failed "
                    f"with exit code {result.returncode}"
                )

        except Exception as e:
            print(
                f"Error running {script.name}: {e}"
            )

    print()
    print("Pipeline complete.")
    print("Waiting 60 seconds before next update...")

    time.sleep(60)