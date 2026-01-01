"""
PDF Processor - Download and extract text from arXiv PDFs
"""
import io
import re
import logging
import requests
from typing import Optional
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Download and extract text from PDF files"""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Research-Paper-Curator/1.0 (Academic Research Tool)"
        }

    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """
        Download PDF from URL

        Args:
            pdf_url: URL to PDF file (usually arXiv)

        Returns:
            PDF bytes or None if download fails
        """
        try:
            logger.info(f"Downloading PDF: {pdf_url}")

            response = requests.get(
                pdf_url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not pdf_url.endswith(".pdf"):
                logger.warning(f"Unexpected content type: {content_type}")

            pdf_bytes = response.content
            logger.info(f"Downloaded {len(pdf_bytes)} bytes")

            return pdf_bytes

        except requests.RequestException as e:
            logger.error(f"Failed to download PDF: {e}")
            return None

    def extract_text(self, pdf_bytes: bytes) -> Optional[str]:
        """
        Extract text from PDF bytes

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            text_parts = []
            total_pages = len(reader.pages)

            logger.info(f"Extracting text from {total_pages} pages")

            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {i}: {e}")
                    continue

            if not text_parts:
                logger.warning("No text extracted from PDF")
                return None

            full_text = "\n\n".join(text_parts)

            # Clean the extracted text
            full_text = self._clean_text(full_text)

            logger.info(f"Extracted {len(full_text)} characters from PDF")

            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted PDF text

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Fix common PDF extraction issues
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)  # Fix hyphenated words

        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Remove common header/footer patterns
        text = re.sub(r'arXiv:\d+\.\d+v\d+\s*\[[\w\.-]+\]\s*\d+\s*\w+\s*\d+', '', text)

        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def process_paper(self, pdf_url: str) -> Optional[str]:
        """
        Full pipeline: download PDF and extract text

        Args:
            pdf_url: URL to PDF file

        Returns:
            Extracted text or None if processing fails
        """
        if not pdf_url:
            logger.warning("No PDF URL provided")
            return None

        # Download PDF
        pdf_bytes = self.download_pdf(pdf_url)
        if not pdf_bytes:
            return None

        # Extract text
        text = self.extract_text(pdf_bytes)

        return text


# Global singleton instance
_pdf_processor = None


def get_pdf_processor() -> PDFProcessor:
    """Get or create PDF processor singleton"""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor
