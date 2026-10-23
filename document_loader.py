"""PDF ingestion that preserves original PDF page numbers."""
from dataclasses import dataclass
from pathlib import Path
import re
from pypdf import PdfReader

@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    page: int

def _split_text(text: str, max_chars: int = 1100, overlap: int = 150) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        return []

    # Preserve PDF headings and section boundaries by splitting on line breaks.
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    chunks = []
    current_lines = []
    current_length = 0

    for line in lines:
        # Split unusually long lines without dropping any text.
        if len(line) > max_chars:
            if current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_length = 0

            start = 0
            while start < len(line):
                piece = line[start:start + max_chars].strip()
                if piece:
                    chunks.append(piece)
                start += max_chars - overlap
            continue

        added_length = len(line) + (1 if current_lines else 0)

        if current_length + added_length <= max_chars:
            current_lines.append(line)
            current_length += added_length
        else:
            previous_chunk = "\n".join(current_lines)
            chunks.append(previous_chunk)

            # Retain some context from the previous chunk.
            tail = previous_chunk[-overlap:].strip() if overlap else ""
            current_lines = [tail, line] if tail else [line]
            current_length = sum(len(part) for part in current_lines) + max(0, len(current_lines) - 1)

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks

def load_pdf_directory(data_dir: str | Path) -> list[DocumentChunk]:
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"PDF directory does not exist: {data_path}")

    pdf_paths = sorted(data_path.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {data_path}")

    chunks: list[DocumentChunk] = []
    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        for page_index, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            for part_index, part in enumerate(_split_text(page_text), start=1):
                chunks.append(DocumentChunk(
                    chunk_id=f"{pdf_path.name}-p{page_index}-c{part_index}",
                    text=part,
                    source=pdf_path.name,
                    page=page_index
                ))

    if not chunks:
        raise ValueError("No readable text was extracted from the PDFs.")
    return chunks