## Cursor Chat Timeline Viewer

An interactive frontend (Vite + React + TypeScript) for exploring Cursor chat history and derived datasets, plus supporting scripts for scraping and data preparation.

### Quick Start

1) Install Node.js 18+ (recommended) and npm.
2) Install frontend dependencies and start the dev server:

```bash
cd frontend
npm ci # or: npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

### What’s in this repo

- `frontend/`: Vite + React app that renders a timeline UI (`Timeline.tsx`).
  - `public/timeline-data.json`: Data file consumed by the timeline UI.
  - `src/`: App source (`App.tsx`, `Timeline.tsx`, styles).
- `chat_history/`: Raw markdown exports of Cursor chat sessions.
- `cleaned_data/`: Processed JSON datasets derived from chat history.
- `data_parsing/`: Utilities for categorization and parsing.
- `scripts/`: Misc. automation (e.g., macOS agent for exporting).
- `cursor_chat_scraper.log`: Log output from scraping tasks.

### Prerequisites

- Node.js 18+ and npm.
- Optional (for data scripts): Python 3.10+.

### Frontend: develop, build, preview

From the project root:

```bash
cd frontend

# Install deps
npm ci # or: npm install

# Run dev server
npm run dev

# Build for production (outputs to frontend/dist)
npm run build

# Preview the production build locally
npm run preview
```

Notes:
- The app reads timeline data from `frontend/public/timeline-data.json`. You can edit or replace this file while the dev server is running; Vite will update the UI on save.
- If you deploy to a subpath, update `base` in `frontend/vite.config.ts` accordingly.

### Managing timeline data

- Default dataset: `frontend/public/timeline-data.json`.
- To update the UI, shape your data to match what `Timeline.tsx` expects (open the file to see field names). Typical fields include identifiers, timestamps, labels, and descriptions per event.
- Large datasets: Consider pagination or server-side slicing before writing to `public/` to keep bundles lean.

### Data sources and scripts

- `chat_history/`: Source `.md` files exported from Cursor.
- `cleaned_data/`: Normalized JSON, suitable for direct UI consumption or further processing.
- `data_parsing/categorize_parse_spechistory.py`: Example categorization/parsing utility. See inline comments for usage.
- `scripts/com.esther.cursor-chat-export.plist`: macOS LaunchAgent for automating exports (optional, macOS only).

Optional Python setup (if you plan to run data utilities):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
# Install any required libs referenced by your scripts
```

Because this repo doesn’t ship a pinned `requirements.txt`, install only what you need for the particular script you are running.

### Project structure

```
frontend/
  public/
    timeline-data.json
  src/
    App.tsx
    Timeline.tsx
    Timeline.css
    main.tsx
    index.css
  package.json
  vite.config.ts

chat_history/
cleaned_data/
data_parsing/
scripts/
```

### Conventions

- TypeScript and React in the frontend. Prefer descriptive names and early returns. Keep components small and focused.
- Linting: If a lint script exists, run `npm run lint`. Otherwise, you can lint ad‑hoc via:

```bash
npx eslint src --ext .ts,.tsx
```

### Deployment

This is a static site. Any static host works (Vercel, Netlify, GitHub Pages, S3/CloudFront, etc.).

1) Build the app:

```bash
cd frontend
npm run build
```

2) Deploy the contents of `frontend/dist` to your host.

Tips:
- For GitHub Pages or non-root paths, set the `base` option in `vite.config.ts`.
- Ensure your host serves `index.html` for unknown routes if you later add client-side routing.

### Troubleshooting

- Dev server not starting: Ensure Node 18+ and a clean install (`rm -rf node_modules && npm ci`).
- No data showing: Validate `public/timeline-data.json` is valid JSON and matches the fields consumed by `Timeline.tsx`.
- Styling not applied: Confirm imports in `App.tsx` and `Timeline.tsx` reference the correct `.css` files.

### License

MIT (or your preferred license). Update this section as needed.

