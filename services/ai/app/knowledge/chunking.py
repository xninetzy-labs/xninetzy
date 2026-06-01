from __future__ import annotations

import re


def chunk_text(text: str, max_tokens: int = 300, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks by approximate token count (words ≈ tokens).
    Tries to split on paragraph or sentence boundaries.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = len(para.split())
        if current_tokens + para_tokens > max_tokens and current:
            chunks.append("\n\n".join(current))
            # Keep overlap
            overlap_text = " ".join(" ".join(current).split()[-overlap:])
            current = [overlap_text] if overlap_text else []
            current_tokens = len(overlap_text.split())

        if para_tokens > max_tokens:
            # Split long paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sent in sentences:
                stokens = len(sent.split())
                if current_tokens + stokens > max_tokens and current:
                    chunks.append(" ".join(current))
                    current = []
                    current_tokens = 0
                current.append(sent)
                current_tokens += stokens
        else:
            current.append(para)
            current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return [c for c in chunks if len(c.strip()) > 30]
