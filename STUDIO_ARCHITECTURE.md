# ExpertCheck Studio architecture

Studio is now separated from Core and organized by responsibility:

- `app.py` — composition root and navigation only.
- `studio/design.py` — design tokens and shared CSS.
- `studio/components.py` — reusable visual components.
- `studio/data.py` — UI-oriented data transformations and report export.
- `studio/pages/` — independent workspaces: Overview, Documents, Objects, Checks, Issues.

Core modules remain unchanged and may later be exposed through an API or another frontend.
