from __future__ import annotations

import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dataclasses import dataclass
from typing import Dict, List, Tuple
from paddleocr import PaddleOCR


Point = Tuple[float, float]


@dataclass
class OCRLine:
    points: List[Point]
    text: str
    score: float


class OCREngine:
    """Thin wrapper around PaddleOCR with in-memory cache."""

    def __init__(self, lang: str = "japan") -> None:
        self._ocr = PaddleOCR(
    		use_angle_cls=True,
    		lang=lang
	)
        self._cache: Dict[str, List[OCRLine]] = {}

    def recognize(self, image_path: str, force: bool = False) -> List[OCRLine]:
        if not force and image_path in self._cache:
            return self._cache[image_path]

        result = self._ocr.ocr(image_path, cls=True)
        lines: List[OCRLine] = []

        if result and result[0]:
            for item in result[0]:
                box = item[0]
                text, score = item[1]
                points = [(float(x), float(y)) for x, y in box]
                lines.append(OCRLine(points=points, text=text, score=float(score)))

        self._cache[image_path] = lines
        return lines

    def clear_cache_for(self, image_path: str) -> None:
        self._cache.pop(image_path, None)
