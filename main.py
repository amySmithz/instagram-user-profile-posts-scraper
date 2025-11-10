"""

import json
import logging
import os
import sys
from pathlib import Path

# Enable relative imports when executed as a script (python src/main.py)
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "src"

from .runner import Runner  # type: ignore

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("main")

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    config_dir = Path(__file__).resolve().parent / "config"

    # Prefer local settings.json if present; otherwise fallback to example
    settings_path = config_dir / "settings.json"
    if not settings_path.exists():
        settings_path = config_dir / "settings.example.json"
        logger.info("No settings.json found. Using settings.example.json")

    settings = load_json(settings_path)

    input_path = data_dir / "input_profiles.json"
    if not input_path.exists():
        logger.warning("data/input_profiles.json not found. Creating with default usernames.")
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(json.dumps(["zuck", "instagram"], indent=2), encoding="utf-8")

    usernames = load_json(input_path)
    if not isinstance(usernames, list) or not all(isinstance(u, str) for u in usernames):
        raise ValueError("data/input_profiles.json must be a JSON array of usernames (strings).")

    runner = Runner(settings=settings, repo_root=str(repo_root))
    runner.run(usernames)

if __name__ == "__main__":
    main()