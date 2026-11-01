---
name: ui-ux-pro-max
description: Comprehensive design intelligence database and styling engine. Use whenever designing, building, or refining user interfaces, web applications, components, or styling to ensure state-of-the-art visual hierarchy, curated color palettes, typography scales, spacing systems, and responsive design.
---

# UI-UX Pro Max Design Intelligence

## 1. Color System & Harmony
- **Avoid Generic Palettes**: Never use plain primaries (#ff0000, #00ff00, #0000ff). Use sophisticated HSL-calibrated scales.
- **Dark Mode Elevation**:
  - Background Base: `#0a0b10` or `#0d1117`
  - Surface 1 (Cards, panels): `#141824` / `#161b26`
  - Surface 2 (Hover, active): `#1e2436`
  - Borders: `rgba(255, 255, 255, 0.08)` to `rgba(255, 255, 255, 0.14)`
  - Accents: Vibrant electric indigo (`#6366f1`), teal/cyan (`#06b6d4`), violet (`#8b5cf6`), or emerald (`#10b981`).
- **Contrast**: Maintain strict WCAG AAA compliance for body copy (minimum 7:1) and AA for headings (4.5:1).

## 2. Typography Scale
- Modern variable Google Fonts: Inter, Outfit, Plus Jakarta Sans, Geist, or Space Grotesk.
- Modular type scale:
  - Hero `h1`: 2.5rem - 3.75rem, font-weight 700/800, line-height 1.1, tracking -0.02em
  - Section `h2`: 1.75rem - 2.25rem, font-weight 600/700, line-height 1.25
  - Subhead `h3`: 1.25rem - 1.5rem, font-weight 600
  - Body: 0.9375rem - 1rem, line-height 1.6, font-weight 400
  - Captions/Badges: 0.75rem - 0.8125rem, tracking 0.04em, font-weight 600, uppercase

## 3. Visual Depth & Surface Design
- **Glassmorphism**: `background: rgba(20, 24, 38, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1);`
- **Soft Shadows**: Multi-layered shadows (`box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 2px 6px -1px rgba(0, 0, 0, 0.3);`).
- **Gradients**: Subtle radial glow backgrounds (`radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.15), transparent 70%)`).

## 4. Micro-Interactions & States
- Smooth transitions: `transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);`
- Button hover: subtle lift (`transform: translateY(-1px)`), glow accentuation.
- Active state: slight scale down (`transform: scale(0.98)`).
- Loading states: Shimmer skeletons over blank placeholders.
