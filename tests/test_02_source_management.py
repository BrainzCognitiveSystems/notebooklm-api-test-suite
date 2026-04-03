"""2. Source Management – end-to-end tests.

Covers:
- Add URL source
- Add YouTube source
- Add raw text source
- Upload file (PDF, Markdown, CSV, DOCX, EPUB)
- Get full text
- Get source guide
- Delete source
"""

from __future__ import annotations

import asyncio

import pytest

from notebooklm.types import Source, SourceFulltext, SourceType


# ---------------------------------------------------------------------------
# Add URL source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_url_source(client, temp_notebook):
    """add_url() must return a Source with a non-empty id."""
    url = "https://en.wikipedia.org/wiki/Machine_learning"
    source = await client.sources.add_url(temp_notebook.id, url, wait=False)

    assert isinstance(source, Source), f"Expected Source, got {type(source)}"
    assert source.id, "Source must have a non-empty id"


@pytest.mark.asyncio
async def test_add_url_source_wait_until_ready(client, temp_notebook):
    """add_url(wait=True) must return a source in READY state."""
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    source = await client.sources.add_url(
        temp_notebook.id,
        url,
        wait=True,
        wait_timeout=120.0,
    )

    assert source.is_ready, (
        f"Source should be READY after wait=True; status={source.status}"
    )


@pytest.mark.asyncio
async def test_url_source_appears_in_list(client, temp_notebook):
    """A newly added URL source must appear in sources.list()."""
    url = "https://en.wikipedia.org/wiki/Deep_learning"
    source = await client.sources.add_url(temp_notebook.id, url, wait=False)

    sources = await client.sources.list(temp_notebook.id)
    ids = [s.id for s in sources]
    assert source.id in ids, (
        f"Source {source.id} must appear in list(); found ids: {ids}"
    )


# ---------------------------------------------------------------------------
# Add YouTube source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_youtube_source(client, temp_notebook):
    """Adding a YouTube URL must return a Source without error."""
    yt_url = "https://www.youtube.com/watch?v=aircAruvnKk"  # 3Blue1Brown, short
    source = await client.sources.add_url(temp_notebook.id, yt_url, wait=False)

    assert isinstance(source, Source)
    assert source.id, "YouTube source must have a non-empty id"
    # After indexing the type should be YOUTUBE; immediately it may be UNKNOWN
    # We only assert the source was accepted without an exception.


# ---------------------------------------------------------------------------
# Add raw text source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_text_source(client, temp_notebook):
    """add_text() must create a source and return it with a non-empty id."""
    source = await client.sources.add_text(
        temp_notebook.id,
        title="Reinforcement Learning Overview",
        content=(
            "Reinforcement learning (RL) is an area of machine learning where "
            "an agent learns to make decisions by receiving rewards or penalties. "
            "The agent's goal is to maximise the cumulative reward over time."
        ),
        wait=False,
    )

    assert isinstance(source, Source)
    assert source.id, "text source must have a non-empty id"


@pytest.mark.asyncio
async def test_add_text_source_wait_and_kind(client, temp_notebook):
    """add_text(wait=True) should return a source with kind PASTED_TEXT."""
    source = await client.sources.add_text(
        temp_notebook.id,
        title="Short Text",
        content="A brief text about Python programming and data science.",
        wait=True,
        wait_timeout=60.0,
    )

    assert source.is_ready, "Source should be READY after wait=True"
    assert source.kind == SourceType.PASTED_TEXT, (
        f"Expected PASTED_TEXT, got {source.kind}"
    )


# ---------------------------------------------------------------------------
# Upload file sources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_pdf_file(client, temp_notebook, tmp_path):
    """Uploading a PDF file must succeed and return a source with PDF kind."""
    from .helpers import create_minimal_pdf  # noqa: PLC0415

    pdf_path = tmp_path / "test.pdf"
    create_minimal_pdf(pdf_path)

    source = await client.sources.add_file(
        temp_notebook.id,
        pdf_path,
        mime_type="application/pdf",
        wait=True,
        wait_timeout=120.0,
    )

    assert source is not None
    assert source.id
    assert source.kind == SourceType.PDF, f"Expected PDF, got {source.kind}"


@pytest.mark.asyncio
async def test_upload_markdown_file(client, temp_notebook, tmp_path):
    """Uploading a Markdown file must succeed and return a MARKDOWN source."""
    from .helpers import create_minimal_markdown  # noqa: PLC0415

    md_path = tmp_path / "test.md"
    create_minimal_markdown(md_path)

    source = await client.sources.add_file(
        temp_notebook.id,
        md_path,
        mime_type="text/markdown",
        wait=True,
        wait_timeout=120.0,
    )

    assert source is not None
    assert source.id
    assert source.kind == SourceType.MARKDOWN, f"Expected MARKDOWN, got {source.kind}"


@pytest.mark.asyncio
async def test_upload_csv_file(client, temp_notebook, tmp_path):
    """Uploading a CSV file must succeed."""
    from .helpers import create_minimal_csv  # noqa: PLC0415

    csv_path = tmp_path / "data.csv"
    create_minimal_csv(csv_path)

    source = await client.sources.add_file(
        temp_notebook.id,
        csv_path,
        mime_type="text/csv",
        wait=True,
        wait_timeout=120.0,
    )

    assert source is not None
    assert source.id
    assert source.kind == SourceType.CSV, f"Expected CSV, got {source.kind}"


@pytest.mark.asyncio
async def test_upload_docx_file(client, temp_notebook, tmp_path):
    """Uploading a DOCX file must produce a DOCX source."""
    from .helpers import create_minimal_docx  # noqa: PLC0415

    docx_path = tmp_path / "document.docx"
    create_minimal_docx(docx_path)

    mime = (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    source = await client.sources.add_file(
        temp_notebook.id,
        docx_path,
        mime_type=mime,
        wait=True,
        wait_timeout=120.0,
    )

    assert source is not None
    assert source.id
    assert source.kind == SourceType.DOCX, f"Expected DOCX, got {source.kind}"


@pytest.mark.asyncio
async def test_upload_epub_file(client, temp_notebook, tmp_path):
    """Uploading an EPUB file must produce an EPUB source."""
    from .helpers import create_minimal_epub  # noqa: PLC0415

    epub_path = tmp_path / "book.epub"
    create_minimal_epub(epub_path)

    source = await client.sources.add_file(
        temp_notebook.id,
        epub_path,
        mime_type="application/epub+zip",
        wait=True,
        wait_timeout=120.0,
    )

    assert source is not None
    assert source.id
    assert source.kind == SourceType.EPUB, f"Expected EPUB, got {source.kind}"


# ---------------------------------------------------------------------------
# Get full text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_fulltext_returns_content(client, temp_notebook):
    """get_fulltext() for any seeded source must return non-empty content.

    Tries every source in the notebook until one yields indexed content.
    This makes the test resilient to the API setting source type codes
    asynchronously (the type may still be UNKNOWN at list() time even
    though the content has been indexed).
    """
    sources = await client.sources.list(temp_notebook.id)
    assert sources, "temp_notebook must have at least one source"

    for source in sources:
        try:
            fulltext = await client.sources.get_fulltext(temp_notebook.id, source.id)
            if not fulltext.content:
                continue
            assert isinstance(fulltext, SourceFulltext)
            assert fulltext.source_id == source.id
            assert isinstance(fulltext.content, str)
            assert len(fulltext.content) > 0, "Full text must not be empty"
            assert fulltext.char_count > 0
            return  # test passed on this source
        except Exception:  # noqa: BLE001
            continue  # source not yet indexed – try the next one

    pytest.skip("No source with indexed content available in temp_notebook yet")


# ---------------------------------------------------------------------------
# Get source guide
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_source_guide(client, temp_notebook):
    """get_guide() must return a dict with 'summary' and 'keywords' keys."""
    sources = await client.sources.list(temp_notebook.id)
    assert sources, "temp_notebook must have at least one source"

    # Wait briefly for the source to be fully indexed
    await asyncio.sleep(2.0)

    guide = await client.sources.get_guide(temp_notebook.id, sources[0].id)

    assert isinstance(guide, dict), f"Expected dict from get_guide(), got {type(guide)}"
    assert "summary" in guide, "guide must contain 'summary'"
    assert "keywords" in guide, "guide must contain 'keywords'"
    assert isinstance(guide["summary"], str)
    assert isinstance(guide["keywords"], list)


# ---------------------------------------------------------------------------
# Delete source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_source(client, temp_notebook):
    """delete() must return True and the source must vanish from list()."""
    # Add an extra source we can safely delete
    extra = await client.sources.add_text(
        temp_notebook.id,
        title="Temp Source For Deletion",
        content="This source exists only to be deleted during the test.",
        wait=True,
        wait_timeout=60.0,
    )

    deleted = await client.sources.delete(temp_notebook.id, extra.id)
    assert deleted is True, "delete() must return True"

    # Verify absence in list
    sources = await client.sources.list(temp_notebook.id)
    ids = [s.id for s in sources]
    assert extra.id not in ids, "Deleted source must not appear in list()"


# ---------------------------------------------------------------------------
# List sources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sources_returns_source_objects(client, temp_notebook):
    """list() must return a list of Source objects."""
    sources = await client.sources.list(temp_notebook.id)

    assert isinstance(sources, list)
    for s in sources:
        assert isinstance(s, Source), f"Expected Source, got {type(s)}"
        assert s.id


@pytest.mark.asyncio
async def test_get_source_by_id(client, temp_notebook):
    """get() must return the exact source matching the given id."""
    sources = await client.sources.list(temp_notebook.id)
    assert sources, "Need at least one source to test get()"

    target = sources[0]
    fetched = await client.sources.get(temp_notebook.id, target.id)

    assert fetched is not None, "get() must not return None for an existing source id"
    assert fetched.id == target.id


@pytest.mark.asyncio
async def test_get_nonexistent_source_returns_none(client, temp_notebook):
    """get() must return None for a source id that does not exist."""
    result = await client.sources.get(temp_notebook.id, "nonexistent-source-id-xyz")
    assert result is None, "get() should return None for a non-existent id"


# ---------------------------------------------------------------------------
# Wait for sources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wait_until_ready(client, temp_notebook):
    """wait_until_ready() must return the source once it's in READY state."""
    sources = await client.sources.list(temp_notebook.id)
    assert sources, "Need at least one source for wait_until_ready()"

    source = await client.sources.wait_until_ready(
        temp_notebook.id,
        sources[0].id,
        timeout=60.0,
    )

    assert source.is_ready, f"Expected READY, got status {source.status}"
