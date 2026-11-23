---
name: Oceanic Intelligence
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3f4850'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#707881'
  outline-variant: '#bfc7d2'
  surface-tint: '#006398'
  primary: '#006194'
  on-primary: '#ffffff'
  primary-container: '#007bb9'
  on-primary-container: '#fdfcff'
  inverse-primary: '#93ccff'
  secondary: '#006c4a'
  on-secondary: '#ffffff'
  secondary-container: '#82f5c1'
  on-secondary-container: '#00714e'
  tertiary: '#00628d'
  on-tertiary: '#ffffff'
  tertiary-container: '#007cb1'
  on-tertiary-container: '#fcfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cce5ff'
  primary-fixed-dim: '#93ccff'
  on-primary-fixed: '#001d31'
  on-primary-fixed-variant: '#004b73'
  secondary-fixed: '#85f8c4'
  secondary-fixed-dim: '#68dba9'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#005137'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#89ceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-hero:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
  display-hero-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  data-mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  data-mono-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system positions itself as an authoritative, high-precision geospatial and environmental intelligence platform tailored for enterprise executives, hydrogeologists, and climate risk analysts. 

The aesthetic is anchored in **Technical Minimalism with Crisp Precision**: pristine white and porcelain surfaces evoke laboratory clarity, balanced by deep navy typography that conveys executive gravitas. Structural definition relies on hairline borders and calculated negative space rather than heavy drop shadows, projecting analytical rigor. High-vibrancy oceanic cyans, deep ceruleans, and crystalline emeralds serve as dynamic focal points, signaling telemetry feeds, sensor readings, and satellite layer overlays without visual noise.

## Colors
The palette balances clinical legibility with high-impact data visualization indicators.

- **Canvas & Surfaces:** Primary workspace base uses `#FFFFFF`. Ancillary navigation panels, sidebars, and control trays utilize porcelain slate `#F8FAFC`, with `#F1F5F9` reserved for table headers, embedded sub-panels, and track controls.
- **Typography & Neutrals:** Absolute high-contrast hierarchy with `#0F172A` (Slate 900) for primary metrics, titles, and critical alerts; `#334155` (Slate 700) for standard telemetry labels and body copy; and `#64748B` (Slate 500) for secondary metadata, map coordinate axes, and disabled states.
- **Dividers & Outlines:** `#E2E8F0` defines default UI sectioning and container boundaries, while `#CBD5E1` reinforces active card states and input borders.
- **Oceanic Accents (Telemetry & Actions):** `#0284C7` (Cyan 600) commands primary interactions, active vector layers, and spatial selections. `#0EA5E9` (Cyan 500) provides interactive hover feedback and active satellite path paths.
- **Environmental Accents (Status & Hydro-Metrics):** `#059669` (Emerald 600) and `#10B981` (Emerald 500) indicate optimal water table thresholds, live sensor handshakes, and baseline stability metrics.

## Typography
Typography is structured around three distinct functional roles:

1. **Space Grotesk** powers page headlines, module titles, and high-impact KPI aggregations, infusing an engineering-forward, geometric tone suitable for modern GIS intelligence.
2. **Hanken Grotesk** carries analytical commentary, configuration forms, and continuous enterprise report text, prioritizing reading ergonomics and structural balance.
3. **JetBrains Mono** handles all tabular geospatial data, coordinate readouts (lat/long), timestamp intervals, sensor hardware IDs, and telemetry metrics to guarantee columnar alignment and eliminate character ambiguity.

## Layout & Spacing
The layout follows a fluid-flexible operational shell tailored for spatial intelligence:
- **Application Shell:** Uses an anchored, collapsible navigation rail (64px collapsed, 260px expanded) paired with a responsive split-screen viewport (GIS map stage dominant at 60–75% width, telemetry inspection drawers at 25–40% width).
- **Grid Structure:** Inside analytical report tabs, content utilizes a 12-column dynamic grid with a default `1rem` (16px) gutter on mobile and `1.5rem` (24px) on desktop viewports. Outer canvas margins contract to `1rem` on compact displays and expand to `2rem` on viewports beyond 1440px.
- **Component Densities:** Compact component padding (`space-xs` and `space-sm`) is strictly enforced within map toolbars, coordinate HUDs, and layer switchers to maximize visible map real estate.

## Elevation & Depth
Depth is maintained through crisp surface containment and micro-diffused ambient light rather than pronounced skeuomorphic drops:

- **Surface Tiers:** 
  - *Tier 0 (Viewport Floor):* Base GIS map view and canvas (`#FFFFFF`).
  - *Tier 1 (Surface Containers):* Layer panels, telemetry feeds, and card modules (`#FFFFFF` resting on `#F8FAFC` backgrounds, enclosed by `#E2E8F0` 1px borders).
  - *Tier 2 (Floating Overlays):* Map viewport controls, zoom widgets, and filter bars (`#FFFFFF` with a 1px `#CBD5E1` border and an ambient micro-tinted shadow: `0 4px 12px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02)`).
  - *Tier 3 (Modals & Flyouts):* Deep analysis configuration dialogs, inspector overlays (`#FFFFFF` bordered by `#CBD5E1` with `0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`).
- **Glass Accents:** Translucent control chips embedded directly over map viewports leverage an ultra-subtle backdrop blur (`backdrop-filter: blur(8px); background-color: rgba(255, 255, 255, 0.85);`).

## Shapes
A clean, soft geometry (`roundedness: 1`) is applied uniformly across the system to preserve technical authority without feeling dated or abrasive:

- Standard cards, panels, inputs, and buttons leverage `0.25rem` (4px) corner radii.
- Secondary contextual overlays, floating map utility toolbars, and status badges take `0.5rem` (8px via `rounded-lg`).
- Strict circle geometry (`rounded-full`) is reserved purely for live sensor pulse indicators, telemetry beacon points, and user avatars.

## Components

- **Buttons:**
  - *Primary:* Solid `#0284C7` background, white text (`Space Grotesk`, medium), 1px border of `#0284C7`. On hover, transitions cleanly to `#0EA5E9`.
  - *Secondary / Outline:* Pure white `#FFFFFF` surface with a 1px `#CBD5E1` border and `#0F172A` text. Hover shifts border to `#0284C7` and text to `#0284C7`.
  - *Destructive / Alert:* Pure white surface with a 1px `#EF4444` border and `#B91C1C` text.
- **Telemetry Chips & Badges:**
  - Compact height (22px to 26px), built with `JetBrains Mono` at `11px`.
  - Live Status badges feature an illuminated blinking indicator dot: `#10B981` with soft pulsing ring for active nodes; `#0284C7` for streaming telemetry; `#64748B` for disconnected or archival status.
- **Cards & Analytical Containers:**
  - Solid `#FFFFFF` fill with 1px `#E2E8F0` border. Headers feature a crisp bottom divider (`#E2E8F0`) with trailing telemetry metadata in `data-mono-md`.
- **Form Inputs & Layer Toggles:**
  - Text fields, coordinate range selectors, and time-scrubbers use `#FFFFFF` fill, 1px `#CBD5E1` border, and sharp focus states: a 1px border of `#0284C7` accompanied by a 2px outer glow (`rgba(2, 132, 199, 0.15)`).
- **Data Tables & Hydrological Logs:**
  - Stripeless `#FFFFFF` design utilizing alternating row hover states (`#F8FAFC`). Header row features `#F1F5F9` background, `#334155` typography, uppercase `11px` monospace tracking, and a definitive bottom border (`#CBD5E1`).
- **Map Viewport Controls:**
  - Modular floating stacks anchored with 1px `#E2E8F0` borders, frosted glass translucency, housing vector toggles, zoom extents, and hydrogeology depth slice controls.