#!/usr/bin/env python3
import os
import sqlite3
import json
import pathlib
import datetime
import schedule
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cursor_chat_scraper.log"), logging.StreamHandler()],
)

WS_DIR = os.path.expanduser(
    "~/Library/Application Support/Cursor/User/workspaceStorage"
)
OUT_DIR = pathlib.Path.home() / "CursorChatExports"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def export_db(db_path):
    """Export chat data from a single SQLite database file."""
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # Keys that have chat JSON (may evolve over time)
        KEYS = ("workbench.panel.aichat.view.aichat.chatdata", "aiService.prompts")
        rows = cur.execute(
            "SELECT key, value FROM ItemTable WHERE key IN (?,?)", KEYS
        ).fetchall()

        exported_files = []
        for key, value in rows:
            try:
                data = json.loads(value)
            except Exception as e:
                logging.warning(f"Failed to parse JSON for key {key}: {e}")
                continue

            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            workspace_name = pathlib.Path(db_path).parent.name
            out = OUT_DIR / f"{workspace_name}_{key}_{ts}.md"

            with open(out, "w", encoding="utf-8") as f:
                f.write(f"# Export from {db_path}\n\n")
                f.write(f"_Key: {key} — Exported: {ts}_\n\n")

                # Handle chat data structure
                if isinstance(data, dict) and "tabs" in data:
                    for tab in data["tabs"]:
                        f.write(f"## {tab.get('title','(untitled)')}\n\n")
                        for m in tab.get("messages", []):
                            role = m.get("role", "user")
                            content = m.get("content", "")
                            f.write(f"**{role}:**\n\n{content}\n\n---\n\n")
                else:
                    f.write("```json\n" + json.dumps(data, indent=2) + "\n```\n")

            exported_files.append(str(out))

        con.close()
        return exported_files

    except Exception as e:
        logging.error(f"Error processing database {db_path}: {e}")
        return []


def scrape_cursor_chat():
    """Main function to scrape all Cursor chat data."""
    logging.info("Starting Cursor chat scraping...")

    if not os.path.exists(WS_DIR):
        logging.error(f"Workspace directory not found: {WS_DIR}")
        return

    total_exported = 0
    workspaces_processed = 0

    for root, dirs, files in os.walk(WS_DIR):
        if "state.vscdb" in files:
            db_path = os.path.join(root, "state.vscdb")
            logging.info(f"Processing database: {db_path}")

            exported_files = export_db(db_path)
            total_exported += len(exported_files)
            workspaces_processed += 1

            for file_path in exported_files:
                logging.info(f"Exported: {file_path}")

    logging.info(
        f"Scraping complete. Processed {workspaces_processed} workspaces, exported {total_exported} files."
    )


def run_scheduler():
    """Run the daily scheduler."""
    logging.info("Starting Cursor chat scraper with daily scheduling...")

    # Schedule the scraping to run daily at 9 AM
    schedule.every().day.at("09:00").do(scrape_cursor_chat)

    # Run once immediately
    scrape_cursor_chat()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Cursor chat data")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--time", default="09:00", help="Daily run time (HH:MM format)")

    args = parser.parse_args()

    if args.once:
        scrape_cursor_chat()
    else:
        # Update schedule time if provided
        if args.time != "09:00":
            schedule.clear()
            schedule.every().day.at(args.time).do(scrape_cursor_chat)

        run_scheduler()
