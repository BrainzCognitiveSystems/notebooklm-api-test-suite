"""4. Artifact Generation – end-to-end tests.

Covers generation, task-polling, listing, and file download for every
artifact type supported by the NotebookLM API:

  Audio Overview  · Video Overview  · Report  · Quiz  · Flashcards
  Slide Deck      · Infographic     · Data Table  · Mind Map

Each ``test_generate_*`` test asserts that a generation call *starts*
without error (returns a valid pending task_id).  It deliberately does
**not** wait for completion, so the whole suite stays fast.

The ``test_poll_and_*`` tests go further: they generate the artifact,
wait for completion via ``poll_until_complete``, and then download the
result to a temp file for format validation – these are the longest-running
tests and are marked with ``@pytest.mark.timeout(600)`` (10 minutes).
"""

from __future__ import annotations

import asyncio
import os
import tempfile

import pytest

from notebooklm.exceptions import ArtifactNotReadyError
from notebooklm.types import Artifact, ArtifactType, GenerationStatus

from .conftest import ARTIFACT_TIMEOUT, GENERATION_COOLDOWN, assert_generation_started
from .helpers import (
    is_valid_csv,
    is_valid_json,
    is_valid_markdown,
    is_valid_mp4,
    is_valid_pdf,
    is_valid_png,
    poll_until_complete,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _cooldown():
    """Short inter-test delay – reduces risk of API rate-limiting."""
    await asyncio.sleep(GENERATION_COOLDOWN)


# ---------------------------------------------------------------------------
# 1. Audio Overview
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_audio_starts(client, temp_notebook):
    """generate_audio() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_audio(temp_notebook.id)
    assert_generation_started(result, "Audio")


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_audio(client, temp_notebook, tmp_path):
    """Full audio flow: generate → poll until complete → download MP4."""
    result = await client.artifacts.generate_audio(temp_notebook.id)
    assert_generation_started(result, "Audio")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete, f"Audio did not complete: {status.status}"

    out = str(tmp_path / "audio.mp4")
    try:
        path = await client.artifacts.download_audio(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_mp4(path), "Downloaded audio is not a valid MP4 container"
    except ArtifactNotReadyError:
        pytest.skip("download_audio: no completed audio artifact available yet")

    await _cooldown()


# ---------------------------------------------------------------------------
# 2. Video Overview
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_video_starts(client, temp_notebook):
    """generate_video() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_video(temp_notebook.id)
    assert_generation_started(result, "Video")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_video(client, temp_notebook, tmp_path):
    """Full video flow: generate → poll until complete → download MP4."""
    result = await client.artifacts.generate_video(temp_notebook.id)
    assert_generation_started(result, "Video")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete, f"Video did not complete: {status.status}"

    out = str(tmp_path / "video.mp4")
    try:
        path = await client.artifacts.download_video(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_mp4(path), "Downloaded video is not a valid MP4 container"
    except ArtifactNotReadyError:
        pytest.skip("download_video: no completed video artifact available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 3. Report
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_report_briefing_doc(client, temp_notebook):
    """generate_report(BRIEFING_DOC) must start without error."""
    from notebooklm.rpc.types import ReportFormat  # noqa: PLC0415

    result = await client.artifacts.generate_report(
        temp_notebook.id,
        report_format=ReportFormat.BRIEFING_DOC,
    )
    assert_generation_started(result, "Report/BriefingDoc")


@pytest.mark.asyncio
async def test_generate_report_study_guide(client, temp_notebook):
    """generate_study_guide() must start without error."""
    result = await client.artifacts.generate_study_guide(temp_notebook.id)
    assert_generation_started(result, "Report/StudyGuide")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_report(client, temp_notebook, tmp_path):
    """Full report flow: generate → poll → download Markdown."""
    from notebooklm.rpc.types import ReportFormat  # noqa: PLC0415

    result = await client.artifacts.generate_report(
        temp_notebook.id,
        report_format=ReportFormat.BRIEFING_DOC,
    )
    assert_generation_started(result, "Report")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "report.md")
    try:
        path = await client.artifacts.download_report(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_markdown(path), "Downloaded report is not valid Markdown"
    except ArtifactNotReadyError:
        pytest.skip("download_report: no completed report available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 4. Quiz
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_quiz_starts(client, temp_notebook):
    """generate_quiz() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_quiz(temp_notebook.id)
    assert_generation_started(result, "Quiz")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_quiz_json(client, temp_notebook, tmp_path):
    """Full quiz flow: generate → poll → download JSON."""
    result = await client.artifacts.generate_quiz(temp_notebook.id)
    assert_generation_started(result, "Quiz")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "quiz.json")
    try:
        path = await client.artifacts.download_quiz(
            temp_notebook.id, out, output_format="json"
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_json(path), "Downloaded quiz is not valid JSON"
    except ArtifactNotReadyError:
        pytest.skip("download_quiz: no completed quiz available")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_quiz_markdown(client, temp_notebook, tmp_path):
    """Full quiz flow (markdown variant): generate → poll → download Markdown."""
    result = await client.artifacts.generate_quiz(temp_notebook.id)
    assert_generation_started(result, "Quiz/MD")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "quiz.md")
    try:
        path = await client.artifacts.download_quiz(
            temp_notebook.id, out, output_format="markdown"
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_markdown(path)
    except ArtifactNotReadyError:
        pytest.skip("download_quiz(markdown): no completed quiz available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 5. Flashcards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_flashcards_starts(client, temp_notebook):
    """generate_flashcards() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_flashcards(temp_notebook.id)
    assert_generation_started(result, "Flashcards")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_flashcards_json(client, temp_notebook, tmp_path):
    """Full flashcards flow: generate → poll → download JSON."""
    result = await client.artifacts.generate_flashcards(temp_notebook.id)
    assert_generation_started(result, "Flashcards")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "flashcards.json")
    try:
        path = await client.artifacts.download_flashcards(
            temp_notebook.id, out, output_format="json"
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_json(path), "Downloaded flashcards JSON is invalid"
    except ArtifactNotReadyError:
        pytest.skip("download_flashcards: no completed flashcards available")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_flashcards_markdown(client, temp_notebook, tmp_path):
    """Flashcards markdown download variant."""
    result = await client.artifacts.generate_flashcards(temp_notebook.id)
    assert_generation_started(result, "Flashcards/MD")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "flashcards.md")
    try:
        path = await client.artifacts.download_flashcards(
            temp_notebook.id, out, output_format="markdown"
        )
        assert os.path.exists(path)
        assert is_valid_markdown(path)
    except ArtifactNotReadyError:
        pytest.skip("download_flashcards(markdown): no completed flashcards")

    await _cooldown()


# ---------------------------------------------------------------------------
# 6. Slide Deck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_slide_deck_starts(client, temp_notebook):
    """generate_slide_deck() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_slide_deck(temp_notebook.id)
    assert_generation_started(result, "SlideDeck")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_slide_deck_pdf(client, temp_notebook, tmp_path):
    """Full slide-deck flow: generate → poll → download PDF."""
    result = await client.artifacts.generate_slide_deck(temp_notebook.id)
    assert_generation_started(result, "SlideDeck")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "slides.pdf")
    try:
        path = await client.artifacts.download_slide_deck(
            temp_notebook.id, out, output_format="pdf"
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_pdf(path), "Downloaded slide deck is not a valid PDF"
    except ArtifactNotReadyError:
        pytest.skip("download_slide_deck: no completed slide deck available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 7. Infographic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_infographic_starts(client, temp_notebook):
    """generate_infographic() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_infographic(temp_notebook.id)
    assert_generation_started(result, "Infographic")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_infographic(client, temp_notebook, tmp_path):
    """Full infographic flow: generate → poll → download PNG."""
    result = await client.artifacts.generate_infographic(temp_notebook.id)
    assert_generation_started(result, "Infographic")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "infographic.png")
    try:
        path = await client.artifacts.download_infographic(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_png(path), "Downloaded infographic is not a valid PNG"
    except ArtifactNotReadyError:
        pytest.skip("download_infographic: no completed infographic available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 8. Data Table
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_data_table_starts(client, temp_notebook):
    """generate_data_table() must return a pending GenerationStatus."""
    result = await client.artifacts.generate_data_table(temp_notebook.id)
    assert_generation_started(result, "DataTable")

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_poll_and_download_data_table_csv(client, temp_notebook, tmp_path):
    """Full data-table flow: generate → poll → download CSV."""
    result = await client.artifacts.generate_data_table(temp_notebook.id)
    assert_generation_started(result, "DataTable")

    status = await poll_until_complete(
        client, temp_notebook.id, result.task_id, timeout=ARTIFACT_TIMEOUT
    )
    assert status.is_complete

    out = str(tmp_path / "table.csv")
    try:
        path = await client.artifacts.download_data_table(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_csv(path), "Downloaded data table is not valid CSV"
    except ArtifactNotReadyError:
        pytest.skip("download_data_table: no completed data table available")

    await _cooldown()


# ---------------------------------------------------------------------------
# 9. Mind Map
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.timeout(300)
async def test_generate_mind_map(client, temp_notebook, tmp_path):
    """generate_mind_map() must return a dict with 'mind_map' key."""
    result = await client.artifacts.generate_mind_map(temp_notebook.id)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "mind_map" in result, "Result must contain 'mind_map'"
    # Note: note_id is present even if mind_map generation was rate-limited
    assert "note_id" in result, "Result must contain 'note_id'"

    await _cooldown()


@pytest.mark.asyncio
@pytest.mark.timeout(300)
async def test_poll_and_download_mind_map(client, temp_notebook, tmp_path):
    """Full mind-map flow: generate → list mind maps → download JSON."""
    # generate_mind_map is synchronous (no separate poll needed)
    gen_result = await client.artifacts.generate_mind_map(temp_notebook.id)

    if gen_result.get("mind_map") is None:
        pytest.skip("generate_mind_map returned no data – possibly rate-limited")

    out = str(tmp_path / "mindmap.json")
    try:
        path = await client.artifacts.download_mind_map(temp_notebook.id, out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        assert is_valid_json(path), "Downloaded mind map is not valid JSON"

        import json  # noqa: PLC0415

        with open(path) as fh:
            data = json.load(fh)
        assert "name" in data, "Mind map JSON must have a 'name' key"
    except ArtifactNotReadyError:
        pytest.skip("download_mind_map: no mind map available yet")

    await _cooldown()


# ---------------------------------------------------------------------------
# Artifact listing tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_artifacts(client, temp_notebook):
    """list() must return a list; all items must be Artifact instances."""
    artifacts = await client.artifacts.list(temp_notebook.id)

    assert isinstance(artifacts, list)
    for art in artifacts:
        assert isinstance(art, Artifact), f"Expected Artifact, got {type(art)}"
        assert art.id


@pytest.mark.asyncio
async def test_list_audio_artifacts(client, temp_notebook):
    """list_audio() must return a list of AUDIO artifacts only."""
    artifacts = await client.artifacts.list_audio(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.AUDIO


@pytest.mark.asyncio
async def test_list_video_artifacts(client, temp_notebook):
    """list_video() must return a list of VIDEO artifacts only."""
    artifacts = await client.artifacts.list_video(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.VIDEO


@pytest.mark.asyncio
async def test_list_reports(client, temp_notebook):
    """list_reports() must return a list of REPORT artifacts only."""
    artifacts = await client.artifacts.list_reports(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.REPORT


@pytest.mark.asyncio
async def test_list_quizzes(client, temp_notebook):
    """list_quizzes() must return a list of QUIZ artifacts only."""
    artifacts = await client.artifacts.list_quizzes(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.QUIZ
        assert art.is_quiz is True


@pytest.mark.asyncio
async def test_list_flashcards(client, temp_notebook):
    """list_flashcards() must return a list of FLASHCARDS artifacts only."""
    artifacts = await client.artifacts.list_flashcards(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.FLASHCARDS
        assert art.is_flashcards is True


@pytest.mark.asyncio
async def test_list_infographics(client, temp_notebook):
    """list_infographics() must return a list of INFOGRAPHIC artifacts only."""
    artifacts = await client.artifacts.list_infographics(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.INFOGRAPHIC


@pytest.mark.asyncio
async def test_list_slide_decks(client, temp_notebook):
    """list_slide_decks() must return a list of SLIDE_DECK artifacts only."""
    artifacts = await client.artifacts.list_slide_decks(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.SLIDE_DECK


@pytest.mark.asyncio
async def test_list_data_tables(client, temp_notebook):
    """list_data_tables() must return a list of DATA_TABLE artifacts only."""
    artifacts = await client.artifacts.list_data_tables(temp_notebook.id)
    assert isinstance(artifacts, list)
    for art in artifacts:
        assert art.kind == ArtifactType.DATA_TABLE


# ---------------------------------------------------------------------------
# Get artifact by ID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_artifact_not_found_returns_none(client, temp_notebook):
    """get() for a non-existent artifact id must return None."""
    result = await client.artifacts.get(temp_notebook.id, "nonexistent-artifact-id")
    assert result is None


# ---------------------------------------------------------------------------
# Task polling support (explicit poll_status test)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_status_returns_generation_status(client, temp_notebook):
    """poll_status() must return a GenerationStatus for a running task."""
    result = await client.artifacts.generate_flashcards(temp_notebook.id)
    assert_generation_started(result, "Flashcards/poll")

    await asyncio.sleep(2.0)

    status = await client.artifacts.poll_status(temp_notebook.id, result.task_id)

    assert isinstance(status, GenerationStatus)
    assert status.task_id == result.task_id
    assert status.status in ("pending", "in_progress", "completed", "failed")

    await _cooldown()


@pytest.mark.asyncio
async def test_wait_for_completion(client, temp_notebook):
    """wait_for_completion() must eventually return a terminal status."""
    result = await client.artifacts.generate_quiz(temp_notebook.id)
    assert_generation_started(result, "Quiz/wait")

    final = await client.artifacts.wait_for_completion(
        temp_notebook.id,
        result.task_id,
        initial_interval=3.0,
        max_interval=15.0,
        timeout=ARTIFACT_TIMEOUT,
    )

    assert isinstance(final, GenerationStatus)
    assert final.is_complete or final.is_failed, (
        f"Expected terminal status, got {final.status!r}"
    )

    await _cooldown()


# ---------------------------------------------------------------------------
# Artifact mutation: delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_artifact(client, temp_notebook):
    """delete() must return True and the artifact must vanish from list()."""
    result = await client.artifacts.generate_flashcards(temp_notebook.id)
    assert_generation_started(result, "Flashcards/delete")

    artifact_id = result.task_id

    # Brief pause so the artifact is visible in the listing
    await asyncio.sleep(3.0)

    deleted = await client.artifacts.delete(temp_notebook.id, artifact_id)
    assert deleted is True, "delete() must return True"

    artifacts = await client.artifacts.list(temp_notebook.id)
    ids = [a.id for a in artifacts]
    assert artifact_id not in ids, "Deleted artifact must not appear in list()"

    await _cooldown()


# ---------------------------------------------------------------------------
# Report suggestions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_suggest_reports(client, temp_notebook):
    """suggest_reports() must return a list."""
    from notebooklm.exceptions import RPCTimeoutError  # noqa: PLC0415

    try:
        suggestions = await client.artifacts.suggest_reports(temp_notebook.id)
    except RPCTimeoutError:
        pytest.skip("suggest_reports timed out – API may be rate-limited")

    assert isinstance(suggestions, list)
    for s in suggestions:
        assert hasattr(s, "title")
        assert hasattr(s, "description")
        assert hasattr(s, "prompt")
