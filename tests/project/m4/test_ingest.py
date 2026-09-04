"""Chunks are contiguous slices with provenance; unchanged text keeps its hash."""

from aiapp.knowledge import chunk_document, parse_markdown
from aiapp.knowledge.ingest import quality_problems
from tests.project.m4.conftest import load_docs


def test_every_chunk_is_a_slice_of_the_document_and_stays_inside_one_section() -> None:
    for doc in load_docs():
        chunks = chunk_document(doc, max_chars=600)
        assert chunks, doc.doc_id
        for c in chunks:
            assert doc.text[c.start : c.end] == c.text, "citations rely on start/end pointing at the source"
            assert "\n#" not in c.text.strip("\n")[1:], "a chunk never crosses a heading"
            assert c.chunk_id.startswith(f"{doc.doc_id}#") and c.version == doc.version
        assert [c.chunk_id for c in chunks] == [f"{doc.doc_id}#{i}" for i in range(len(chunks))]


def test_small_budget_splits_a_section_into_paragraph_groups() -> None:
    text = "# Big\n\n" + "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(6))
    big = chunk_document(parse_markdown("big", text), max_chars=5_000)
    small = chunk_document(parse_markdown("big", text), max_chars=500)
    assert len(big) == 1 and len(small) > 1
    assert all(c.section == "Big" for c in small)
    assert "".join(c.text for c in small).count("Paragraph") == 6, "nothing is lost when splitting"


def test_content_hash_survives_a_new_version_when_text_is_unchanged() -> None:
    v1 = chunk_document(parse_markdown("d", "# A\n\nsame text\n\n# B\n\nold text", version=1))
    v2 = chunk_document(parse_markdown("d", "# A\n\nsame text\n\n# B\n\nnew text", version=2))
    assert v1[0].content_hash == v2[0].content_hash and v1[1].content_hash != v2[1].content_hash


def test_quality_problems_flag_bad_encoding_and_duplicates() -> None:
    chunks = chunk_document(parse_markdown("q", "# A\n\nRefunds are pro�essed weekly.\n\n# B\n\nsame\n\n# C\n\nsame"))
    problems = quality_problems(chunks)
    assert any("replacement character" in p for p in problems)
    assert not any("duplicate" in p for p in problems), "same text under different headings hashes differently on purpose"
    dup = chunk_document(parse_markdown("q", "# A\n\n" + "\n\n".join(["exactly the same paragraph " * 30] * 2), ), max_chars=100)
    assert any("duplicate" in p for p in quality_problems(dup))
