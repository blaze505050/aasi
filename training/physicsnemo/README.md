# AASI PhysicsNeMo Training Recipes & Cluster Environment

This directory contains standalone, exportable training recipes and scripts for training high-fidelity Physics AI models (AeroGraphNet, Fourier Neural Operators, MeshGraphNet, and DoMINO) on GPU workstations, Google Colab, or institutional HPC clusters.

> **Important Workstation Notice:**  
> AASI does **not** require PhysicsNeMo or NVIDIA CUDA GPU stacks on the local development machine. These recipes are structured for external execution, remote export, or cloud GPU training.

---

## 1. System Requirements & Hardware Guidelines

- **OS**: Ubuntu 22.04 LTS or Linux container (NGC PyTorch 24.01+)
- **GPU**: NVIDIA A100 (40GB/80GB), H100, V100 (16GB/32GB), or Google Colab Pro (T4/A100)
- **CUDA**: 12.1+ / cuDNN 8.9+
- **Python**: 3.10 or 3.11

---

## 2. Installation Instructions (On GPU Server / Colab)

```bash
# 1. Create dedicated training virtual environment
conda create -n physicsnemo_env python=3.10 -y
conda activate physicsnemo_env

# 2. Install PyTorch with CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Install PhysicsNeMo / NVIDIA Modulus core & sym libraries
pip install nvidia-modulus
pip install nvidia-modulus-sym

# 4. Install geometric graph dependencies
pip install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.2.0+cu121.html

# 5. Verify installation
python -c "import torch; import modulus; print('Modulus & CUDA ready:', torch.cuda.is_available())"
```

---

## 3. Supported Model Architectures

| Model Architecture | Target Aerodynamic Quantity | Input Representation | Typical Convergence |
| :--- | :--- | :--- | :--- |
| **AeroGraphNet** | Surface pressure, skin friction, $C_L, C_D, C_M$ | Unstructured surface mesh graphs (nodes, edges) | ~150 epochs (~2 hrs on A100) |
| **FNO-2D** | Full 2D velocity & pressure field $(U_x, U_y, p)$ | Regular grid or Cartesian bounding box $(128 \times 128)$ | ~200 epochs (~3 hrs on V100) |
| **DoMINO** | Complex 3D vehicle external aerodynamics | Multi-scale surface and volume grids | ~500 epochs on multi-GPU |
| **MeshGraphNet** | Volumetric fluid flow & mesh deformation | 3D tetrahedral/polyhedral computational grids | ~300 epochs |

---

## 4. Dataset Format Specification

Datasets for AeroGraphNet and FNO training are formatted in HDF5 (`.h5`) or PyTorch Geometric `.pt` archives:
```text
dataset/
├── train/
│   ├── sample_00001.pt   # Contains: x (coords, normal), edge_index, y (p, tau_w, Cl, Cd)
│   └── ...
└── test/
    ├── sample_00801.pt
    └── ...
```

---

## 5. Execution Commands

### Train AeroGraphNet (External Aerodynamics):
```bash
python aerographnet_recipe.py \
    --dataset_path /data/airfrans \
    --epochs 150 \
    --batch_size 32 \
    --learning_rate 3e-4 \
    --output_dir ./checkpoints/aerographnet
```

### Train Fourier Neural Operator (FNO-2D):
```bash
python fno_airfoil_recipe.py \
    --dataset_path /data/airfrans_grid \
    --modes 16 \
    --width 64 \
    --epochs 200 \
    --output_dir ./checkpoints/fno_2d
```

---

## 6. Exporting Checkpoints to AASI

Once training completes, export the model checkpoint and training metadata back to the AASI Model Registry:
```bash
# Generates model manifest and cryptographic hash for backend/physics/model_registry.py
python -c "
import hashlib
with open('checkpoints/aerographnet/model_best.pt', 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()
print(f'Model Checksum: {h}')
"
```
Place the resulting hash into `backend/physics/model_registry.py`.
