from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

Point = Tuple[float, float]


@dataclass
class OCRLine:
    points: List[Point]
    text: str
    score: float


class OCREngine:
    """Thin wrapper around PaddleOCR with in-memory cache and test-friendly injection."""

    def __init__(
        self,
        lang: str = "japan",
        ocr_backend: Optional[Any] = None,
        backend_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self._backend_factory = backend_factory or self._create_default_backend
        self._ocr = ocr_backend or self._backend_factory(lang)
        self._cache: Dict[str, List[OCRLine]] = {}

    def _create_default_backend(self, lang: str) -> Any:
        # Import lazily so unit tests can run without heavy OCR dependencies.
        from paddleocr import PaddleOCR

        return PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def recognize(self, image_path: str, force: bool = False) -> List[OCRLine]:
        normalized_path = str(Path(image_path))
        image_file = Path(normalized_path)
        if not image_file.exists() or not image_file.is_file():
            raise FileNotFoundError(f"Image path does not exist: {normalized_path}")

        if not force and normalized_path in self._cache:
            return self._cache[normalized_path]

        result = self._ocr.ocr(normalized_path, cls=True)
        lines = self._parse_ocr_result(result)

        self._cache[normalized_path] = lines
        return lines

    def _parse_ocr_result(self, result: Any) -> List[OCRLine]:
        lines: List[OCRLine] = []
        if result and result[0]:
            for item in result[0]:
                box = item[0]
                text, score = item[1]
                points = [(float(x), float(y)) for x, y in box]
                lines.append(OCRLine(points=points, text=text, score=float(score)))
        return lines

    def clear_cache_for(self, image_path: str) -> None:
        self._cache.pop(str(Path(image_path)), None)
