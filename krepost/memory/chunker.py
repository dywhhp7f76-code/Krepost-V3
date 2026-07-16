"""
krepost/memory/chunker.py

Детерминированное разбиение текста на чанки для векторной БД. Пакует абзацы
(разделённые пустой строкой) в чанки до max_chars; слишком длинный абзац
режется жёстко с перекрытием (overlap) для непрерывности retrieval.
"""
from __future__ import annotations

import re
from typing import List, Tuple

_PARA_SPLIT = re.compile(r"\n\s*\n")
_HEADER = re.compile(r"^(#{1,6})\s+(.*)$")


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    if not text or not text.strip():
        return []
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    overlap = max(0, min(overlap, max_chars - 1))

    paras = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]
    chunks: List[str] = []
    cur = ""

    def flush():
        nonlocal cur
        if cur:
            chunks.append(cur)
            cur = ""

    for p in paras:
        if len(p) > max_chars:
            # Длинный абзац: сбрасываем накопленное и режем жёстко с overlap.
            flush()
            step = max_chars - overlap
            for i in range(0, len(p), step):
                chunks.append(p[i:i + max_chars])
                if i + max_chars >= len(p):
                    break
            continue
        if not cur:
            cur = p
        elif len(cur) + 1 + len(p) <= max_chars:
            cur = cur + "\n" + p
        else:
            flush()
            cur = p

    flush()
    return chunks


def _split_sections(text: str) -> List[Tuple[str, str]]:
    """Разбить markdown на секции (breadcrumb, body) по заголовкам.

    breadcrumb — путь из заголовков от H1 до текущего уровня («H1 > H2»).
    Преамбула до первого заголовка идёт с пустой крошкой.
    """
    sections: List[Tuple[str, str]] = []
    stack: List[Tuple[int, str]] = []  # (уровень, текст заголовка)
    breadcrumb = ""
    body_lines: List[str] = []

    def flush_section():
        body = "\n".join(body_lines).strip()
        if body:
            sections.append((breadcrumb, body))
        body_lines.clear()

    for line in text.split("\n"):
        m = _HEADER.match(line)
        if m:
            flush_section()
            level = len(m.group(1))
            title = m.group(2).strip()
            # срезаем стек до уровня выше текущего, кладём себя
            stack[:] = [(lv, t) for (lv, t) in stack if lv < level]
            stack.append((level, title))
            breadcrumb = " > ".join(t for _, t in stack)
        else:
            body_lines.append(line)
    flush_section()
    return sections


def chunk_markdown(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """Semantic chunker: режет по заголовкам Markdown, не пересекая их границы.

    Каждый чанк несёт «хлебные крошки» заголовка (путь H1 > H2 > …) как контекст
    для retrieval; длинная секция дробится тем же паковщиком (chunk_text), но
    крошка повторяется на каждом куске. Без заголовков — полный фолбэк на
    chunk_text (побайтно совпадает).
    """
    if not text or not text.strip():
        return []
    sections = _split_sections(text)
    # Нет ни одного заголовка → обычный абзацный чанкинг.
    if not any(bc for bc, _ in sections) and len(sections) <= 1:
        return chunk_text(text, max_chars=max_chars, overlap=overlap)

    out: List[str] = []
    for breadcrumb, body in sections:
        prefix = f"[{breadcrumb}]\n" if breadcrumb else ""
        budget = max(1, max_chars - len(prefix))
        for piece in chunk_text(body, max_chars=budget, overlap=overlap):
            out.append(prefix + piece)
    return out
