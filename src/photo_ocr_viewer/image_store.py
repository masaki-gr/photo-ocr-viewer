from __future__ import annotations

from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def list_supported_images(folder: Path) -> List[Path]:
    """Return sorted image files from a folder (non-recursive)."""
    if not folder.exists() or not folder.is_dir():
        raise NotADirectoryError(f"Invalid folder path: {folder}")

    return sorted(
        [
            p
            for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )
