---
name: Orbital Synthetic Intelligence
colors:
  surface: '#0b1229'
  surface-dim: '#0b1229'
  surface-bright: '#323851'
  surface-container-lowest: '#060d24'
  surface-container-low: '#141a32'
  surface-container: '#181e36'
  surface-container-high: '#222941'
  surface-container-highest: '#2d344c'
  on-surface: '#dce1ff'
  on-surface-variant: '#bcc8d1'
  inverse-surface: '#dce1ff'
  inverse-on-surface: '#292f48'
  outline: '#87929b'
  outline-variant: '#3d4850'
  surface-tint: '#79d1ff'
  primary: '#83d3ff'
  on-primary: '#003549'
  primary-container: '#00bbf9'
  on-primary-container: '#004761'
  inverse-primary: '#006689'
  secondary: '#c7fff0'
  on-secondary: '#00382f'
  secondary-container: '#00f2d1'
  on-secondary-container: '#006a5a'
  tertiary: '#ffb5c9'
  on-tertiary: '#650031'
  tertiary-container: '#ff89af'
  on-tertiary-container: '#850042'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c3e8ff'
  primary-fixed-dim: '#79d1ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c68'
  secondary-fixed: '#26fedc'
  secondary-fixed-dim: '#00dfc1'
  on-secondary-fixed: '#00201a'
  on-secondary-fixed-variant: '#005144'
  tertiary-fixed: '#ffd9e1'
  tertiary-fixed-dim: '#ffb1c6'
  on-tertiary-fixed: '#3f001c'
  on-tertiary-fixed-variant: '#8e0048'
  background: '#0b1229'
  on-background: '#dce1ff'
  surface-variant: '#2d344c'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system delivers a mission-critical, high-precision command center aesthetic engineered for geospatial data scientists, climate intelligence operators, and Earth observation specialists. The design combines tactical minimalism, deep telemetry visual layering, and selective glassmorphism to emphasize complex spatial visualisations without cognitive overload.

The visual style prioritizes deep contrast and optical precision:
- **Atmospheric Depth:** Rich oceanic navy substrates evoke high-altitude orbital vantage points, allowing multi-spectral indices, NDVI thermal layers, and synthetic aperture radar (SAR) feeds to emerge vibrantly.
- **Glassmorphic HUD Elements:** Translucent floating control surfaces provide seamless spatial context over interactive multi-layered base maps.
- **Precision Data Hierarchy:** Strict separation between navigational scaffolding and analytical readout layers, utilizing luminous neon telemetry accents against muted naval panels.

## Colors

The palette leverages an orbital dark scheme designed to minimize eye fatigue during extended operations while maximizing optical distinction across complex multi-band remote sensing imagery.

### Color Tokens & Roles
- **Base Canvas (`#0A1128`):** Deep oceanic abyss serving as the universal backdrop and map boundary frame.
- **Surface Elevation 1 (`#101A36`):** Card bodies, dock surfaces, and sidebar panels.
- **Surface Elevation 2 / Glass (`rgba(16, 26, 54, 0.72)`): Floating HUD overlays, flyouts, and contextual toolbars paired with a `12px` background blur.
- **Border Stroke (`#1E2D5A`):** Structural division lines and card bounding strokes maintaining technical discipline.
- **Primary / Telemetry Blue (`#00BBF9`):** Interactive selections, primary active toggles, trajectory vectors, and vector geometries.
- **Secondary / Biosphere Emerald (`#00F5D4`):** Vegetation index data, nominal status pings, and positive environmental delta readouts.
- **Warning Amber (`#FFB703`):** Thermal anomalies, cloud cover warnings, and sensor calibration alerts.
- **Alert Rose (`#F72585`):** Deforestation alarms, critical perimeter breaches, and destructive weather anomalies.
- **Data Neutral (`#8E9AB8`):** Unfocused labels, grid axes, inactive telemetry items, and muted legends.

## Typography

The typographic hierarchy implements a bifurcated structure: **Inter** handles narrative structure, UI flow, and dashboard layout, while **JetBrains Mono** governs all raw geospatial parameters, latitude/longitude coordinates, timestamps, confidence scores, and satellite spectral band indices.

- **Numerics & GIS Coordinates:** Always rendered in JetBrains Mono with tabular lining figures (`font-variant-numeric: tabular-nums`) to prevent layout shifts during live ingestion feeds.
- **Section & Module Headers:** Uppercase tracking (`0.06em`) is applied strictly to `label-sm` and `label-md` when used as telemetry category banners.
- **Mobile Adaptations:** For mobile or constrained inspection views, `headline-xl` drops to `24px` with a `32px` line height.

## Layout & Spacing

The system is architected around an extensible HUD dashboard model featuring a persistent orbital viewport canvas bounded by dynamic, modular floating trays and panels.

### Grid & Layout Rules
- **Desktop (1440px+):** Flexible viewport layout. Side panels adhere to fixed 320px or 380px operational rails, with the central GIS map occupying dynamic remaining width.
- **Tablet (768px - 1439px):** Analytical toolbars collapse into collapsible floating drawers with `margin: 1rem` and `gutter: 1rem`.
- **Mobile (< 768px):** Single-column stacked telemetry modules with sliding bottom sheets for multi-band imagery adjustment.
- **Layout Spacing Density:** High-density telemetry displays employ `gutter-compact` (`0.5rem`) within card groups to allow instantaneous cross-referencing between charts, histograms, and map coordinates.

## Elevation & Depth

Visual hierarchy uses tonal surface layering combined with precise edge luminance and glassmorphic diffusion, avoiding heavy opaque dropshadows.

### Elevation Levels
- **Canvas Base (Level 0):** Pure `#0A1128` background layer containing tiled vector maps, raster sat tiles, or 3D point-cloud canvases.
- **Structural Containers (Level 1):** Solid `#101A36` background with a `1px` continuous border in `#1E2D5A`.
- **Floating Glass HUD (Level 2):** Semi-transparent `#101A36` tinted at 75% opacity, paired with `backdrop-filter: blur(12px)` and a subtle directional top-edge highlight (`1px solid rgba(0, 187, 249, 0.2)`).
- **Active Focus & Modals (Level 3):** Deep navy translucent fill with an outer ambient glow: `box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.6), 0 0 16px 0 rgba(0, 187, 249, 0.15)`.

## Shapes

The interface adopts a disciplined technical posture (`roundedness: 1`), utilizing restrained corner curvature (`0.25rem` base, `0.5rem` for large panels) to evoke military GIS interfaces and satellite telemetry consoles.

- **Cards & Data Panels:** `rounded-lg` (`0.5rem`) with razor-thin structural borders (`1px solid #1E2D5A`).
- **Telemetry Buttons & Filter Chips:** `rounded` (`0.25rem`) for a tactile, instrument-grade appearance.
- **Status Indicators & Coordinates:** Strict pill contours are reserved exclusively for live orbital tracking markers, sensor status badges, and geospatial pin halos.

## Components

### Buttons & Action Controls
- **Primary Telemetry Button:** `#00BBF9` background, `#0A1128` bold typography, `0.25rem` radius. On hover: subtle cyan bloom glow (`0 0 12px rgba(0, 187, 249, 0.4)`).
- **Secondary Ghost Button:** Translucent `#101A36` background, `1px solid #1E2D5A` border, `#00BBF9` text. Hover shifts border color to `#00BBF9`.
- **Destructive/Alert Button:** Deep wine fill (`rgba(247, 37, 133, 0.15)`), `1px solid #F72585`, text in `#F72585`.

### Chips & Filter Tags
- Multi-spectral band selectors (e.g., "SWIR", "NDVI", "RGB", "SAR") rendered in `label-sm` JetBrains Mono.
- Inactive state: `#101A36` background, `#8E9AB8` text, `#1E2D5A` border.
- Active state: `#0A1128` background, `#00F5D4` text, `1px solid #00F5D4` border with inner tint.

### Data Cards & Analytical Panels
- Header container features a sub-surface dividing line (`1px solid #1E2D5A`) with secondary coordinates displayed in `label-sm` monospace.
- Interior charts use `#00BBF9` (primary trend lines), `#00F5D4` (positive bounds), and `#F72585` (anomaly thresholds).

### Inputs & Sliders
- **Text & Coordinate Fields:** Background `#0A1128`, border `1px solid #1E2D5A`, text `#FFFFFF`, font `JetBrains Mono`. Focus ring: `1px solid #00BBF9` with zero shadow offset.
- **Temporal Time-Series Slider:** Rail colored `#1E2D5A`, active progress filled with gradient from `#00BBF9` to `#00F5D4`. Thumb is a sharp geometric pip with a glowing active core.

### Geospatial-Specific Components
- **Map Overlays & Layer Controls:** Compact glassmorphic floating trays anchored to map corners.
- **Coordinate Crosshairs & Reticles:** Crisp, high-contrast `#00BBF9` lines with live-updating tabular telemetry readouts.