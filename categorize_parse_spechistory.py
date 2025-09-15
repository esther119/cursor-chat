#!/usr/bin/env python3
"""
Parse .chat_history/*.md files and generate timeline data for visualization.
"""

import os
import re
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # If python-dotenv not installed, try to load manually
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip("\"'").strip()


class SpecHistoryParser:
    def __init__(
        self,
        history_dir: str = "../chat_history/",
        use_openai: bool = True,
        openai_model: str = "gpt-4o-mini",
    ):
        self.history_dir = Path(history_dir)
        self.use_openai = use_openai
        self.openai_model = openai_model
        self.sessions = []
        self.categories = {
            "plan": {
                "keywords": [
                    "how to",
                    "approach",
                    "strategy",
                    "plan",
                    "design",
                    "architecture",
                    "finding",
                ],
                "color": "#3B82F6",  # blue
                "priority": 1,
            },
            "codegen": {
                "keywords": [
                    "create",
                    "implement",
                    "add",
                    "build",
                    "integrate",
                    "generate",
                    "construct",
                ],
                "color": "#10B981",  # green
                "priority": 2,
            },
            "refactor": {
                "keywords": [
                    "refactor",
                    "improve",
                    "clean",
                    "organize",
                    "reorganize",
                    "rename",
                    "move",
                ],
                "color": "#8B5CF6",  # purple
                "priority": 3,
            },
            "debug": {
                "keywords": [
                    "error",
                    "why",
                    "issue",
                    "fix",
                    "fixing",
                    "bug",
                    "problem",
                    "syntax error",
                ],
                "color": "#F59E0B",  # yellow
                "priority": 4,
            },
            "feature": {
                "keywords": [
                    "change",
                    "update",
                    "allow",
                    "adjust",
                    "selecting",
                    "trigger",
                    "show",
                ],
                "color": "#EC4899",  # pink
                "priority": 5,
            },
            "review": {
                "keywords": [
                    "understanding",
                    "what",
                    "explain",
                    "critique",
                    "code review",
                ],
                "color": "#F97316",  # orange
                "priority": 6,
            },
            "meta": {
                "keywords": ["commit", "git", "merge", "abort", "branch"],
                "color": "#6366F1",  # indigo
                "priority": 7,
            },
            "config": {
                "keywords": [
                    "input",
                    "parameter",
                    "requirements",
                    "settings",
                    "configure",
                ],
                "color": "#06B6D4",  # cyan
                "priority": 8,
            },
        }

    def _categorize_with_openai(
        self,
        filename: str,
        timestamp: datetime,
        content: str,
        fallback_title: str,
    ) -> Optional[Dict[str, str]]:
        """Use OpenAI to produce {category,title,preview}. Returns None on failure."""
        if not self.use_openai:
            return None

        # Lazy import to avoid hard dependency if flag not used
        try:
            import openai  # type: ignore
        except Exception:
            return None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        system_prompt = (
            "You are an expert product analyst for software engineering sessions. Given the content of a single "
            "SpecStory session (extracted from a markdown conversation), produce a structured summary.\n\n"
            "Output STRICT JSON with keys: category, title, preview. No extra fields, comments, or prose.\n\n"
            "Requirements:\n- category: choose exactly one from {plan, codegen, refactor, debug, feature, review, meta, config}.\n"
            "  • plan: questions about approach/strategy/design\n  • codegen: requests to create/implement/add/build/integrate code\n"
            "  • refactor: improvements/renames/reorg/cleanup\n  • debug: errors/why/fix/bug/problem\n  • feature: change/update/allow/adjust/show/trigger/selecting\n"
            "  • review: explain/critique/understand/code review\n  • meta: git/commit/merge/branch/CI\n  • config: inputs/parameters/settings/configuration requirements\n"
            "- title: Title Case, specific and action-oriented. If the user asks a question, convert to a clear, descriptive title.\n"
            "- preview: One short sentence summarizing the user’s ask or the task outcome. ≤ 120 chars. No markdown.\n\n"
            'Return format:\n{"category":"...","title":"...","preview":"..."}'
        )

        user_template = (
            f"Filename: {filename}\n"
            f"Timestamp: {timestamp.isoformat().replace('+00:00','Z')}\n\n"
            f"User request (excerpt):\n{content[:2000]}\n\n"
            "Task: Produce JSON with keys category, title, preview."
        )

        try:
            openai.api_key = api_key
            # Support both Chat Completions and Responses depending on SDK version
            try:
                resp = openai.chat.completions.create(
                    model=self.openai_model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_template},
                    ],
                )
                text = resp.choices[0].message.content.strip()
            except Exception:
                # Fallback to legacy
                resp = openai.ChatCompletion.create(
                    model=self.openai_model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_template},
                    ],
                )
                text = resp["choices"][0]["message"]["content"].strip()

            # Parse strict JSON
            data = json.loads(text)

            # Validate keys
            if not all(k in data for k in ("category", "title", "preview")):
                return None

            # Normalize category
            if data["category"] not in self.categories.keys():
                data["category"] = "codegen"

            return data
        except Exception:
            return None

    def parse_filename(self, filename: str) -> Tuple[datetime, str]:
        """Extract timestamp and title from filename."""
        # Pattern: YYYY-MM-DD_HH-MMZ-title-with-dashes.md
        match = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})Z-(.+)\.md", filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")

        date_str, time_str, title_slug = match.groups()

        # Parse timestamp
        timestamp_str = f"{date_str}T{time_str.replace('-', ':')}:00Z"
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # Convert title from slug to readable format
        title = title_slug.replace("-", " ").title()

        return timestamp, title

    def categorize_session(self, title: str, content: str) -> Tuple[str, float]:
        """Categorize session based on title and content keywords."""
        text = f"{title} {content}".lower()

        # Score each category
        scores = {}
        for category, info in self.categories.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword in text:
                    # Title matches are weighted more
                    if keyword in title.lower():
                        score += 3
                    else:
                        score += 1
            scores[category] = score

        # Get the category with highest score
        if max(scores.values()) > 0:
            category = max(scores, key=scores.get)
            # Calculate confidence based on score
            max_score = scores[category]
            confidence = (
                "high" if max_score >= 3 else "medium" if max_score >= 1 else "low"
            )
        else:
            # Default to 'codegen' if no clear match
            category = "codegen"
            confidence = "low"

        return category, confidence

    def read_file_content(self, filepath: Path) -> str:
        """Read and extract relevant content from markdown file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract the first user query (after "User" heading)
            user_match = re.search(
                r"_\*\*User.*?\*\*_\s*\n\s*(.+?)(?=\n---|\n_\*\*)", content, re.DOTALL
            )
            if user_match:
                return user_match.group(1).strip()

            # Fallback to first non-metadata content
            lines = content.split("\n")
            for line in lines:
                if (
                    line.strip()
                    and not line.startswith("#")
                    and not line.startswith("<!--")
                ):
                    return line.strip()

            return ""
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""

    def calculate_durations(self, sessions: List[Dict]) -> List[Dict]:
        """Calculate duration for each session based on time to next session."""
        sorted_sessions = sorted(sessions, key=lambda x: x["startTime"])

        for i in range(len(sorted_sessions)):
            if i < len(sorted_sessions) - 1:
                current_time = datetime.fromisoformat(
                    sorted_sessions[i]["startTime"].replace("Z", "+00:00")
                )
                next_time = datetime.fromisoformat(
                    sorted_sessions[i + 1]["startTime"].replace("Z", "+00:00")
                )

                duration_minutes = int((next_time - current_time).total_seconds() / 60)
                # Cap at 4 hours (240 minutes) - longer gaps likely mean break
                duration_minutes = min(duration_minutes, 240)
            else:
                # Last session - assume 30 minutes
                duration_minutes = 30

            sorted_sessions[i]["duration"] = duration_minutes

        return sorted_sessions

    def parse_all_files(self) -> Dict:
        """Parse all history files and generate timeline data."""
        # Get all .md files
        print("self.history_dir", self.history_dir)
        md_files = sorted(self.history_dir.glob("*.md"))

        print(f"Found {len(md_files)} history files to parse...")

        sessions = []
        for filepath in md_files:
            try:
                # Parse filename
                timestamp, title = self.parse_filename(filepath.name)

                # Read content
                content = self.read_file_content(filepath)

                # Categorize (optionally via OpenAI)
                ai_summary = self._categorize_with_openai(
                    filepath.name, timestamp, content, title
                )
                if ai_summary:
                    print(
                        f'ai_summary - category: {ai_summary["category"]}, title: {ai_summary["title"]}, preview: {ai_summary["preview"]}'
                    )
                if ai_summary:
                    category = ai_summary["category"]
                    resolved_title = ai_summary["title"]
                    preview = ai_summary["preview"]
                    # Confidence from AI path defaults to high
                    confidence = "high"
                else:
                    category, confidence = self.categorize_session(title, content)
                    resolved_title = title
                    # Trim preview to ≤ 120 chars to match UI expectations
                    preview = content[:117] + "..." if len(content) > 120 else content

                session = {
                    "category": category,
                    "title": resolved_title,
                    "startTime": timestamp.isoformat().replace("+00:00", "Z"),
                    "confidence": confidence,
                    "filename": filepath.name,
                    "preview": preview,
                }

                sessions.append(session)
                print(f"  ✓ {title} -> {category} ({confidence})")

            except Exception as e:
                print(f"  ✗ Error parsing {filepath.name}: {e}")

        # Calculate durations
        sessions = self.calculate_durations(sessions)

        # Calculate statistics
        total_duration = sum(s["duration"] for s in sessions)

        category_stats = {}
        for cat in self.categories:
            cat_sessions = [s for s in sessions if s["category"] == cat]
            cat_duration = sum(s["duration"] for s in cat_sessions)

            if cat_sessions:
                category_stats[cat] = {
                    "duration": cat_duration,
                    "percentage": (
                        round((cat_duration / total_duration) * 100, 1)
                        if total_duration > 0
                        else 0
                    ),
                    "sessions": len(cat_sessions),
                    "color": self.categories[cat]["color"],
                }

        return {
            "sessions": sessions,
            "totalDuration": total_duration,
            "categories": category_stats,
            "metadata": {
                "generated": datetime.now().isoformat(),
                "totalSessions": len(sessions),
                "timeRange": {
                    "start": sessions[0]["startTime"] if sessions else None,
                    "end": sessions[-1]["startTime"] if sessions else None,
                },
            },
        }


def main():
    """Main entry point."""
    argp = argparse.ArgumentParser(
        description="Parse SpecStory history into timeline JSON"
    )
    argp.add_argument(
        "--history-dir",
        default="../chat_history/",
        help="Directory containing .md files",
    )
    argp.add_argument(
        "--output",
        default="../public/timeline-data.json",
        help="Output JSON path (defaults to public/timeline-data.json)",
    )
    argp.add_argument(
        "--also-write-local",
        action="store_true",
        help="Also write a copy to cursor-history/timeline-data.json",
    )
    argp.add_argument(
        "--use-openai",
        action="store_true",
        default=True,
        help="Use OpenAI to categorize and title sessions (requires OPENAI_API_KEY, enabled by default)",
    )
    argp.add_argument(
        "--no-openai",
        action="store_true",
        help="Disable OpenAI and use keyword-based categorization instead",
    )
    argp.add_argument(
        "--openai-model",
        default="gpt-4o-mini",
        help="OpenAI model to use when --use-openai is set",
    )
    argp.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JSON to stdout instead of writing files",
    )

    args = argp.parse_args()

    # Handle --no-openai flag to override default
    use_openai = args.use_openai and not args.no_openai

    parser = SpecHistoryParser(
        history_dir=args.history_dir,
        use_openai=use_openai,
        openai_model=args.openai_model,
    )
    timeline_data = parser.parse_all_files()

    # Serialize once
    json_str = json.dumps(timeline_data, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(json_str)
        return

    # Save to primary output (typically public/timeline-data.json)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Optionally write local copy in this folder for inspection
    if args.also_write_local:
        local_path = Path("timeline-data.json")
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(json_str)

    print(f"\nTimeline data saved to: {output_path}")
    if args.also_write_local:
        print("Also wrote: ./timeline-data.json")
    print(f"Total sessions: {timeline_data['metadata']['totalSessions']}")
    print(f"Total duration: {timeline_data['totalDuration']} minutes")
    print("\nCategory breakdown:")

    for cat, stats in sorted(
        timeline_data["categories"].items(),
        key=lambda x: x[1]["duration"],
        reverse=True,
    ):
        if stats["sessions"] > 0:
            print(
                f"  {cat:10} {stats['percentage']:5.1f}% ({stats['duration']:4d} min) - {stats['sessions']} sessions"
            )


if __name__ == "__main__":
    main()
