#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DL retraining pipeline and auto-promote best artifact")
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--image-size", type=int, default=192)
    parser.add_argument("--tta-rounds", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--output-stem", type=str, default="custom_cnn_finetuned_calibrated_refresh")
    parser.add_argument("--cache-dataset", action="store_true")
    parser.add_argument("--skip-image-rf", action="store_true")
    parser.add_argument("--rf-n-estimators", type=int, default=400)
    parser.add_argument("--rf-cv", type=int, default=3)
    parser.add_argument("--dry-run-promote", action="store_true")
    return parser.parse_args()


def run_step(cmd: list[str], env: dict[str, str]) -> None:
    print("\n>>>", " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, check=True)


def main() -> int:
    args = parse_args()

    if not VENV_PYTHON.exists():
        raise SystemExit(f"Missing virtualenv interpreter: {VENV_PYTHON}")

    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".mplconfig"))

    train_cmd = [
        str(VENV_PYTHON),
        "scripts/train_dl_finetune_calibrated.py",
        "--architecture",
        "custom_cnn",
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--image-size",
        str(args.image_size),
        "--tta-rounds",
        str(args.tta_rounds),
        "--learning-rate",
        str(args.learning_rate),
        "--output-stem",
        args.output_stem,
    ]
    if args.cache_dataset:
        train_cmd.append("--cache-dataset")
    run_step(train_cmd, env)

    if not args.skip_image_rf:
        image_rf_cmd = [
            str(VENV_PYTHON),
            "scripts/train_dl_image_rf.py",
            "--n-estimators",
            str(args.rf_n_estimators),
            "--cv",
            str(args.rf_cv),
            "--cache",
        ]
        run_step(image_rf_cmd, env)

    promote_cmd = [sys.executable, "scripts/promote_best_dl_model.py"]
    if args.dry_run_promote:
        promote_cmd.append("--dry-run")
    run_step(promote_cmd, env)

    compare_cmd = [sys.executable, "scripts/compare_dl_summaries.py"]
    run_step(compare_cmd, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
