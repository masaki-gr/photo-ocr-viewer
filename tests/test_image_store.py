from __future__ import annotations

from pathlib import Path

import pytest

from photo_ocr_viewer.image_store import list_supported_images


def test_multiple_images_in_folder_are_sorted_and_listed() -> None:
    images = list_supported_images(Path("tests/data"))

    assert len(images) >= 2
    assert images == sorted(images)
    assert all(path.suffix.lower() in {".png", ".jpg", ".jpeg"} for path in images)


def test_non_image_files_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"not real image but extension is enough")
    (tmp_path / "note.txt").write_text("ignore me", encoding="utf-8")

    images = list_supported_images(tmp_path)

    assert [p.name for p in images] == ["a.png"]


def test_invalid_folder_path_raises_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "does_not_exist"

    with pytest.raises(NotADirectoryError):
        list_supported_images(invalid_path)
