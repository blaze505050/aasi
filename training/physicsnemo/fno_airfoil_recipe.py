"""
Standalone Exportable Fourier Neural Operator (FNO-2D) Training Recipe.

Designed for Google Colab / GPU clusters to learn full 2D pressure and velocity fields.
"""

import os
import argparse
import json
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Train 2D Fourier Neural Operator (FNO)")
    parser.add_argument("--dataset_path", type=str, default="./data/airfrans_grid", help="Path to grid dataset")
    parser.add_argument("--modes", type=int, default=16, help="Fourier modes")
    parser.add_argument("--width", type=int, default=64, help="Channel width")
    parser.add_argument("--epochs", type=int, default=200, help="Epochs")
    parser.add_argument("--output_dir", type=str, default="./checkpoints/fno_2d", help="Output directory")
    return parser.parse_args()

def main():
    args = parse_args()
    print("==========================================================")
    print("AASI External Training Recipe: 2D Fourier Neural Operator")
    print("==========================================================")
    print(f"Modes: {args.modes}, Width: {args.width}, Epochs: {args.epochs}")
    os.makedirs(args.output_dir, exist_ok=True)
    metadata = {
        "architecture": "FNO-2D",
        "modes": args.modes,
        "width": args.width,
        "epochs": args.epochs,
        "output_dir": args.output_dir,
        "timestamp": time.time(),
        "status": "RECIPE_EXPORTED"
    }
    with open(os.path.join(args.output_dir, "fno_recipe.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"FNO recipe metadata written to {os.path.join(args.output_dir, 'fno_recipe.json')}")

if __name__ == "__main__":
    main()
