"""
Пробник #50 (semantic chunker): markdown-header-aware разбиение.

Абзацный chunk_text не уважает структуру документа — секция под одним
заголовком может слипнуться с чужой. chunk_markdown режет по заголовкам
Markdown (# ## ###), не пересекает их границы и несёт «хлебные крошки»
заголовка в каждый чанк (контекст для retrieval).
"""
from krepost.memory.chunker import chunk_markdown, chunk_text


class TestChunkMarkdown:

    def test_does_not_merge_across_headers(self):
        md = "# A\nтело раздела А.\n\n# B\nтело раздела Б."
        chunks = chunk_markdown(md, max_chars=800)
        # ни один чанк не содержит тело обоих разделов сразу
        assert not any("тело раздела А" in c and "тело раздела Б" in c for c in chunks)

    def test_breadcrumb_prepended(self):
        md = "# Заголовок\n## Подраздел\nсодержимое тут."
        chunks = chunk_markdown(md, max_chars=800)
        body = [c for c in chunks if "содержимое тут" in c][0]
        assert "Заголовок" in body and "Подраздел" in body

    def test_nested_hierarchy_in_breadcrumb(self):
        md = "# H1\nx\n## H2\ny\n### H3\nglubina"
        chunks = chunk_markdown(md, max_chars=800)
        deep = [c for c in chunks if "glubina" in c][0]
        # крошка отражает путь H1 > H2 > H3
        assert "H1" in deep and "H2" in deep and "H3" in deep

    def test_long_section_split_keeps_header(self):
        long_body = "предложение. " * 200  # >800 символов
        md = f"# Большой\n{long_body}"
        chunks = chunk_markdown(md, max_chars=300, overlap=50)
        assert len(chunks) > 1
        # заголовок повторяется на каждом куске секции
        assert all("Большой" in c for c in chunks)

    def test_no_headers_falls_back(self):
        plain = "просто текст без заголовков.\n\nвторой абзац."
        chunks = chunk_markdown(plain, max_chars=800)
        assert chunks == chunk_text(plain, max_chars=800)

    def test_empty(self):
        assert chunk_markdown("", max_chars=800) == []

    def test_preamble_before_first_header(self):
        md = "вступление без заголовка.\n\n# Раздел\nтело."
        chunks = chunk_markdown(md, max_chars=800)
        assert any("вступление" in c for c in chunks)
        assert any("тело" in c for c in chunks)
