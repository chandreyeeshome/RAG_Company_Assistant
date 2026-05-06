from typing import List, Optional
import re

def clean_text(s: str) -> str: 
    return " ".join(s.replace("\r", " ").split())

def split_into_sentences(text: str) -> List[str]: 
    sents = re.split(r'(?<=[.!?])\s+', text.strip()) 
    return [s for s in sents if s]

def chunk_text(
    text: str,
    target_words: int = 220,
    overlap_words: int = 40,
    title_prefix: Optional[str] = None,
    single_chunk_threshold: int = 80
) -> List[str]:

    text = clean_text(text)

    total_words = len(text.split())

    # If the docx content or text input is very small, keep single chunk
    if total_words <= single_chunk_threshold:
        chunk = text
        if title_prefix:
            chunk = f"{title_prefix}\n{chunk}"
        return [chunk]
    
    # For larger content, normal chunking is followed
    sents = split_into_sentences(text)

    chunks, cur, cur_words = [], [], 0

    for s in sents:
        words = s.split()

        if cur_words + len(words) > target_words and cur:
            chunks.append(" ".join(cur))

            if overlap_words > 0:
                tail = " ".join(" ".join(cur).split()[-overlap_words:])
                cur = [tail]
                cur_words = len(tail.split())
            else:
                cur, cur_words = [], 0

        cur.append(s)
        cur_words += len(words)

    if cur:
        chunks.append(" ".join(cur))

    if title_prefix:
        chunks = [f"{title_prefix}\n{c}" for c in chunks]

    return chunks