from __future__ import annotations

from pathlib import Path

import pytest

from photo_ocr_viewer.ocr import OCREngine, OCRLine


class FakeOCRBackend:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def ocr(self, image_path: str, cls: bool = True):
        self.calls.append((image_path, cls))
        return self.response


@pytest.fixture
def sample_image_path() -> Path:
    return Path("tests/data/No.263.png").resolve()


def test_single_image_ocr_processing(sample_image_path: Path) -> None:
    backend = FakeOCRBackend(
        [[[[[10, 10], [40, 10], [40, 30], [10, 30]], ["hello", 0.98]]]]
    )
    engine = OCREngine(ocr_backend=backend)

    lines = engine.recognize(str(sample_image_path))

    assert len(lines) == 1
    assert isinstance(lines[0], OCRLine)
    assert lines[0].text == "hello"
    assert lines[0].score == pytest.approx(0.98)
    assert backend.calls == [(str(sample_image_path), True)]


def test_invalid_path_raises_file_not_found() -> None:
    backend = FakeOCRBackend([])
    engine = OCREngine(ocr_backend=backend)

    with pytest.raises(FileNotFoundError):
        engine.recognize("tests/data/not_found.png")

    assert backend.calls == []


def test_no_ocr_results_returns_empty_lines(sample_image_path: Path) -> None:
    backend = FakeOCRBackend([None])
    engine = OCREngine(ocr_backend=backend)

    lines = engine.recognize(str(sample_image_path))

    assert lines == []


def test_same_file_reuses_cache(sample_image_path: Path) -> None:
    backend = FakeOCRBackend(
        [[[[[0, 0], [1, 0], [1, 1], [0, 1]], ["cached", 1.0]]]]
    )
    engine = OCREngine(ocr_backend=backend)

    first = engine.recognize(str(sample_image_path))
    second = engine.recognize(str(sample_image_path))

    assert first == second
    assert len(backend.calls) == 1


def test_force_option_bypasses_cache(sample_image_path: Path) -> None:
    backend = FakeOCRBackend(
        [[[[[0, 0], [2, 0], [2, 2], [0, 2]], ["forced", 0.9]]]]
    )
    engine = OCREngine(ocr_backend=backend)

    engine.recognize(str(sample_image_path))
    engine.recognize(str(sample_image_path), force=True)

    assert len(backend.calls) == 2
