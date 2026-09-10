"""
Standalone Exportable AeroGraphNet Training Recipe for PhysicsNeMo / NVIDIA Modulus.

Designed to run in Google Colab, GPU workstations, or institutional clusters.
Can be executed directly with `python aerographnet_recipe.py`.
"""

import os
import argparse
import json
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Train AeroGraphNet on Airfoil Aerodynamics")
    parser.add_argument("--dataset_path", type=str, default="./data/sample_airfoils", help="Path to preprocessed graph dataset")
    parser.add_argument("--epochs", type=int, default=150, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--output_dir", type=str, default="./checkpoints/aerographnet", help="Directory to save checkpoints")
    return parser.parse_args()

def main():
    args = parse_args()
    print("==========================================================")
    print("AASI External Training Recipe: AeroGraphNet Aerodynamics")
    print("==========================================================")
    print(f"Target Output Directory: {args.output_dir}")
    print(f"Epochs: {args.epochs}, Batch Size: {args.batch_size}, LR: {args.learning_rate}")

    # Check CUDA availability
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"PyTorch Version: {torch.__version__}, Device: {device}")
        if device == "cpu":
            print("[NOTICE] Running on CPU. For production training, an NVIDIA A100/V100 GPU is recommended.")
    except ImportError:
        print("[NOTICE] PyTorch is not installed in current environment. Please install on target GPU cluster.")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    metadata = {
        "architecture": "AeroGraphNet",
        "dataset_path": args.dataset_path,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "timestamp": time.time(),
        "status": "RECIPE_EXPORTED"
    }
    with open(os.path.join(args.output_dir, "training_recipe.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Recipe metadata saved to {os.path.join(args.output_dir, 'training_recipe.json')}")

if __name__ == "__main__":
    main()
