# Aerodynamic Data Pipeline & Geometry Representation

## Architectural Objective

The data pipeline standardizes disparate raw airfoil representations (CAD contours, coordinate point clouds, wind tunnel tables) into deterministic numerical tensors for neural surrogate training and inference.

---

## 1. Coordinate Resampling & Normalization (`backend/physics_ai/geometry.py`)

1. **Origin & Unit Chord Normalization:**
   $$x_{norm} = \frac{x - x_{min}}{x_{max} - x_{min}}, \quad y_{norm} = \frac{y}{x_{max} - x_{min}}$$
   Guarantees $x \in [0.0, 1.0]$ and preserves aspect ratio.
2. **Contour Ordering:**
   Standard clockwise ordering: Trailing Edge upper ($x=1, y\approx 0$) $\to$ Leading Edge ($x=0, y=0$) $\to$ Trailing Edge lower ($x=1, y\approx 0$).
3. **Equidistant Arc-Length Spline Resampling:**
   Raw profiles vary from 30 to 500 coordinates. The pipeline resamples all contours onto a fixed $N = 64$ point equidistant arc-length grid:
   $$s_i = \sum_{k=1}^i \sqrt{(x_k - x_{k-1})^2 + (y_k - y_{k-1})^2}, \quad s_{norm} \in [0, 1]$$
   Interpolation evaluates $(x(s), y(s))$ at 64 uniform arc-length intervals, yielding tensor shape $[64, 2]$ ($128$ floats).
4. **Geometric Sanity Flags:**
   - Detects trailing edge gap inconsistency ($> 0.05c$)
   - Checks self-intersections and excessive thickness ($> 0.35c$)
   - Calculates max thickness ratio $(t/c)_{max}$ and max camber $(y_c/c)_{max}$.

---

## 2. Flow Condition Normalization (`backend/physics_ai/normalization.py`)

Flow conditions span disparate physical units:
- Mach Number $M \in [0.05, 0.40]$
- Reynolds Number $Re \in [5\times 10^5, 6\times 10^6]$ (log-scale)
- Angle of Attack $\alpha \in [-8^\circ, 18^\circ]$

The normalizer scales features:
$$X_{cond} = \left[ \frac{M - \mu_M}{\sigma_M}, \quad \frac{\log_{10}(Re) - \mu_{logRe}}{\sigma_{logRe}}, \quad \frac{\alpha - \mu_\alpha}{\sigma_\alpha} \right]$$

---

## 3. Target Processing (`backend/physics_ai/targets.py`)

Aerodynamic target coefficients:
- $C_L$ (Lift coefficient): Range $[-0.5, 1.8]$
- $C_D$ (Drag coefficient): Range $[0.005, 0.08]$ (an order of magnitude smaller than $C_L$)
- $C_M$ (Quarter-chord moment): Range $[-0.15, 0.05]$

To prevent drag from being overwhelmed by lift during gradient backpropagation, the loss applies target weighting:
$$\mathcal{L} = w_{cl} \text{MSE}(C_L) + w_{cd} \text{MSE}(C_D) + w_{cm} \text{MSE}(C_M)$$
with default weights $w_{cl} = 1.0$, $w_{cd} = 5.0$, $w_{cm} = 2.0$.
