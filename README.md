## Cursor Chat Timeline Viewer

An interactive frontend (Vite + React + TypeScript) for exploring Cursor chat history and derived datasets, plus supporting scripts for scraping and data preparation.

## AI Categorization criteria

| Category                 | Description                                                         | Example Title                            |
| ------------------------ | ------------------------------------------------------------------- | ---------------------------------------- |
| **codegen\:ui**          | Implementing new UI elements, components, or visual behavior        | Build Responsive Modal With              |
| **codegen\:core**        | Writing core logic, data structures, state machines, algorithms     | Implement Trie-Based Autocomplete Engine |
| **codegen\:infra**       | Building infrastructure code (APIs, DB schemas, auth, jobs, queues) | Add Background Worker With               |
| **codegen\:integration** | Connecting existing systems, services, or libraries                 | Integrate Checkout Into App              |
| **codegen\:tooling**     | Writing dev tooling, scripts, or CLIs                               | Create Git Commit Lint Script            |
| **codegen\:tests**       | Writing new unit/integration tests                                  | Add Jest Tests For User Controller       |
| **codegen\:experiment**  | Prototyping something uncertain or new for exploration              | Try With for Data Fetching               |

### Quick Start

1. Install Node.js 18+ (recommended) and npm.
2. Install frontend dependencies and start the dev server:

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
- `data_parsing/categorize_parse_spechistory.py`: Categorization and parsing utility that processes SpecStory history files into timeline data.
- `scripts/com.esther.cursor-chat-export.plist`: macOS LaunchAgent for automating exports (optional, macOS only).

### Running the Data Parser

The `categorize_parse_spechistory.py` script processes SpecStory history files and generates timeline data:

#### Basic usage (with OpenAI categorization):

```bash
cd data_parsing
python3 categorize_parse_spechistory.py
```

This reads from `../.specstory/history/` and outputs to `../public/timeline-data.json`.

#### Without OpenAI (keyword-based categorization):

```bash
python3 categorize_parse_spechistory.py --no-openai
```

#### Custom paths:

```bash
python3 categorize_parse_spechistory.py --history-dir /path/to/history --output /path/to/output.json
```

#### All options:

- `--history-dir`: Directory with SpecStory .md files (default: `../.specstory/history`)
- `--output`: Output JSON path (default: `../public/timeline-data.json`)
- `--also-write-local`: Write a copy to current directory
- `--no-openai`: Use keyword-based categorization
- `--openai-model`: OpenAI model (default: `gpt-4o-mini`)
- `--dry-run`: Print to console instead of writing files

### Python dependencies (optional)

For data processing scripts:

```bash
pip3 install openai python-dotenv
```

For AI categorization, create a `.env` file with:

```
OPENAI_API_KEY=your-key-here
```

The script will analyze your SpecStory history files and categorize them into different types (plan, codegen:ui, codegen:core, refactor, debug, etc.) to create an interactive timeline visualization.

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

### License

MIT (or your preferred license). Update this section as needed.
