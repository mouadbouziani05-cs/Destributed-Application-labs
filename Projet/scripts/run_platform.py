from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import bootstrap  # noqa: F401


PROJECT_ROOT = Path(__file__).resolve().parents[1]


SERVICE_SCRIPTS = [
    ("analysis", PROJECT_ROOT / "scripts" / "run_analysis_service.py"),
    ("auth", PROJECT_ROOT / "scripts" / "run_auth_service.py"),
    ("audit", PROJECT_ROOT / "scripts" / "run_audit_service.py"),
    ("gateway", PROJECT_ROOT / "scripts" / "run_gateway.py"),
    ("web-ui", PROJECT_ROOT / "scripts" / "run_web_ui.py"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the full phishing detection platform locally.")
    parser.add_argument("--seed", action="store_true", help="Initialize demo users and SQLite databases before starting.")
    return parser.parse_args()


def launch_process(label: str, script_path: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
    )


def terminate_processes(processes: list[tuple[str, subprocess.Popen[str]]]) -> None:
    for label, process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for label, process in reversed(processes):
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    args = parse_args()
    started: list[tuple[str, subprocess.Popen[str]]] = []

    try:
        if args.seed:
            subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "seed_demo.py")], cwd=str(PROJECT_ROOT), check=True)

        for label, script_path in SERVICE_SCRIPTS:
            process = launch_process(label, script_path)
            started.append((label, process))
            print(f"Started {label} (pid={process.pid})")

        print("Platform started. Press Ctrl+C to stop all services.")
        for _, process in started:
            process.wait()
        return 0
    except KeyboardInterrupt:
        print("Stopping services...")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"Seed step failed with exit code {exc.returncode}")
        return exc.returncode
    finally:
        terminate_processes(started)


if __name__ == "__main__":
    raise SystemExit(main())