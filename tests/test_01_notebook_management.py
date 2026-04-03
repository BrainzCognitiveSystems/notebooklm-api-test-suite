"""1. Notebook Management – end-to-end tests.

Covers:
- Create notebook
- List notebooks
- Get notebook details
- Rename notebook
- Delete notebook
- Get summary (raw text)
- Get description (AI-generated summary + suggested topics)
"""

from __future__ import annotations

import pytest

from notebooklm.types import Notebook, NotebookDescription


# ---------------------------------------------------------------------------
# Listing notebooks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notebooks_returns_list(client):
    """list() must return a list; every element must be a Notebook."""
    notebooks = await client.notebooks.list()
    assert isinstance(notebooks, list), "Expected a list from notebooks.list()"
    for nb in notebooks:
        assert isinstance(nb, Notebook), f"Expected Notebook, got {type(nb)}"


@pytest.mark.asyncio
async def test_list_notebooks_has_id_and_title(client):
    """Every listed notebook must expose a non-empty id and a title string."""
    notebooks = await client.notebooks.list()
    if not notebooks:
        pytest.skip("Account has no notebooks – skipping field validation")
    for nb in notebooks:
        assert nb.id, "Notebook id must not be empty"
        assert isinstance(nb.title, str), "Notebook title must be a string"


# ---------------------------------------------------------------------------
# Create  →  Get  →  Rename  →  Delete lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_notebook(client, created_notebooks, cleanup_notebooks):
    """Creating a notebook returns a Notebook with the requested title."""
    title = "PW-Create-Test"
    nb = await client.notebooks.create(title)
    created_notebooks.append(nb.id)

    assert isinstance(nb, Notebook)
    assert nb.id, "Created notebook must have a non-empty id"
    assert nb.title == title, f"Expected title {title!r}, got {nb.title!r}"


@pytest.mark.asyncio
async def test_get_notebook_by_id(client, temp_notebook):
    """get() must return the same notebook (matching id)."""
    fetched = await client.notebooks.get(temp_notebook.id)

    assert fetched is not None
    assert isinstance(fetched, Notebook)
    assert fetched.id == temp_notebook.id, (
        f"Fetched id {fetched.id!r} must match requested id {temp_notebook.id!r}"
    )


@pytest.mark.asyncio
async def test_get_notebook_includes_title(client, temp_notebook):
    """get() must return a non-empty title string."""
    fetched = await client.notebooks.get(temp_notebook.id)
    assert isinstance(fetched.title, str)
    assert fetched.title  # not empty


@pytest.mark.asyncio
async def test_rename_notebook(client, temp_notebook):
    """rename() must update the notebook title.

    The renamed title is verified by a subsequent get().
    """
    new_title = "PW-Renamed-Notebook"
    renamed = await client.notebooks.rename(temp_notebook.id, new_title)

    # rename() returns the updated notebook directly
    assert renamed.title == new_title or renamed.id == temp_notebook.id

    # Verify via an independent get()
    fetched = await client.notebooks.get(temp_notebook.id)
    assert fetched.title == new_title, (
        f"Expected renamed title {new_title!r}, got {fetched.title!r}"
    )


@pytest.mark.asyncio
async def test_delete_notebook(client, created_notebooks, cleanup_notebooks):
    """delete() must return True and the notebook must disappear from the listing."""
    nb = await client.notebooks.create("PW-Delete-Target")
    nb_id = nb.id

    # Delete immediately
    result = await client.notebooks.delete(nb_id)
    assert result is True, "delete() must return True on success"

    # Verify it is gone from the listing
    notebooks = await client.notebooks.list()
    ids = [n.id for n in notebooks]
    assert nb_id not in ids, "Deleted notebook must not appear in list()"

    # Remove from cleanup list (already deleted)
    if nb_id in created_notebooks:
        created_notebooks.remove(nb_id)


# ---------------------------------------------------------------------------
# Description / summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_summary_returns_string(client, temp_notebook):
    """get_summary() should return a non-empty string for a seeded notebook."""
    summary = await client.notebooks.get_summary(temp_notebook.id)

    assert isinstance(summary, str), "Expected a string from get_summary()"
    # The notebook has enough content to produce a summary
    assert len(summary) > 0, "Summary should not be empty for a seeded notebook"


@pytest.mark.asyncio
async def test_get_description_structure(client, temp_notebook):
    """get_description() must return a NotebookDescription with a non-empty summary."""
    desc = await client.notebooks.get_description(temp_notebook.id)

    assert isinstance(desc, NotebookDescription), (
        f"Expected NotebookDescription, got {type(desc)}"
    )
    assert isinstance(desc.summary, str), "summary must be a str"
    assert desc.summary, "summary must not be empty for a seeded notebook"
    assert isinstance(desc.suggested_topics, list), "suggested_topics must be a list"


@pytest.mark.asyncio
async def test_get_description_suggested_topics(client, temp_notebook):
    """suggested_topics entries must have question and prompt fields."""
    desc = await client.notebooks.get_description(temp_notebook.id)

    for topic in desc.suggested_topics:
        assert hasattr(topic, "question"), "SuggestedTopic must have .question"
        assert hasattr(topic, "prompt"), "SuggestedTopic must have .prompt"
        assert isinstance(topic.question, str)
        assert isinstance(topic.prompt, str)


# ---------------------------------------------------------------------------
# Notebook raw data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_raw_returns_list(client, temp_notebook):
    """get_raw() must return a list (raw API payload)."""
    raw = await client.notebooks.get_raw(temp_notebook.id)
    assert raw is not None
    assert isinstance(raw, list), f"Expected list from get_raw(), got {type(raw)}"


# ---------------------------------------------------------------------------
# Notebook metadata (composite)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_metadata_reflects_source(client, temp_notebook):
    """get_metadata() should show at least one source for the seeded notebook."""
    meta = await client.notebooks.get_metadata(temp_notebook.id)

    assert meta is not None
    assert meta.id == temp_notebook.id
    assert isinstance(meta.title, str)
    # The temp_notebook fixture adds one text source
    assert len(meta.sources) >= 1, (
        "Metadata must reflect the source added by temp_notebook fixture"
    )
