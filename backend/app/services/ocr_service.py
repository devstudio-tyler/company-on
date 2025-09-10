"""
이미지 OCR 서비스
JPG/PNG 이미지를 텍스트로 변환
"""
from typing import Dict, Any
from PIL import Image
import pytesseract
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """간단한 OCR 서비스 (Tesseract 기반)"""

    def __init__(self, languages: str = "kor+eng"):
        # 사용 언어: 한국어+영어. 컨테이너에 해당 언어 데이터가 설치되어 있어야 함
        self.languages = languages

    def extract_text(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        이미지 바이트에서 텍스트 추출

        Returns:
            {
                text: str,
                metadata: { width, height, mode }
            }
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            # 가능하면 OCR 인식률 향상을 위해 RGB로 변환
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image, lang=self.languages)

            metadata = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
            }

            logger.info(
                f"OCR 완료: {len(text.strip())} chars, size: {image.width}x{image.height}, mode: {image.mode}"
            )

            return {
                "text": text or "",
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"OCR 실패: {str(e)}")
            raise



