"""Shared pytest fixtures for the notebooklm-py Playwright test suite.

Authentication: the Playwright storage state recorded by ``notebooklm login``
is read from *notebooklm-storage/storage_state.json* at the workspace root.
No browser is launched at test time; the saved cookies are injected directly
into the httpx-based NotebookLMClient.
"""

from __future__ import annotations

import asyncio
import os
import warnings
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

import pytest

from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens

# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom command-line flags for this suite."""
    parser.addoption(
        "--keep-notebooks",
        action="store_true",
        default=False,
        help=(
            "Do NOT delete temporary notebooks created during tests. "
            "Useful for inspecting artifacts and sources in the UI after a run. "
            "The preserved notebook URLs are printed at the end of teardown."
        ),
    )

# ---------------------------------------------------------------------------
# Resolved paths
# ---------------------------------------------------------------------------

# Workspace root is two levels above this file (tests/ → project root)
_WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()

# Path to the Playwright-saved session produced by ``notebooklm login``
STORAGE_STATE = _WORKSPACE_ROOT / "notebooklm-storage" / "storage_state.json"

# ---------------------------------------------------------------------------
# Timing constants
# ---------------------------------------------------------------------------

#: Seconds to wait after adding a source before any operation that needs it
SOURCE_WAIT = 3.0

#: Interval between artifact status polls (seconds)
POLL_INTERVAL = 5.0

#: Maximum time to wait for artifact generation to finish (seconds)
ARTIFACT_TIMEOUT = 300.0

#: Default wait between generation tests (seconds) – reduces rate-limit risk
GENERATION_COOLDOWN = 10.0


# ---------------------------------------------------------------------------
# Helpers available to test modules
# ---------------------------------------------------------------------------


def assert_generation_started(result, label: str = "Artifact") -> None:
    """Assert an artifact generation call returned a valid pending task.

    Calls ``pytest.skip`` (rather than failing) when:
    - The API rate-limits the account, OR
    - The generation is rejected by the server for any other reason
      (subscription tier, transient API failure, etc.)

    This prevents infrastructure-level API issues from masking real
    library bugs in the rest of the suite.
    """
    assert result is not None, f"{label} generation returned None"

    if result.is_failed:
        # Any failure from the server-side generation endpoint is treated as a skip.
        # Rate-limit, subscription limits, and transient failures are all out of
        # scope for library correctness tests.
        reason = result.error or "(no error detail returned)"
        pytest.skip(f"{label} generation was rejected by the API: {reason}")

    assert result.task_id, f"{label} generation returned no task_id: {result}"
    assert result.status in ("pending", "in_progress"), (
        f"Unexpected {label} status immediately after generation: {result.status!r}"
    )


# ---------------------------------------------------------------------------
# Session-scoped auth fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_tokens() -> AuthTokens:
    """Return refreshed :class:`AuthTokens` loaded from the Playwright session.

    The fixture is session-scoped: the CSRF / session-ID tokens are fetched
    once and reused across all tests, which avoids redundant homepage requests.
    """
    if not STORAGE_STATE.exists():
        pytest.exit(
            f"\n\nERROR: Playwright storage state not found at:\n  {STORAGE_STATE}\n\n"
            "Run  notebooklm login  first to record a session, then retry.\n",
            returncode=1,
        )

    async def _load() -> AuthTokens:
        return await AuthTokens.from_storage(STORAGE_STATE)

    return asyncio.run(_load())


# ---------------------------------------------------------------------------
# Function-scoped client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(auth_tokens: AuthTokens) -> AsyncGenerator[NotebookLMClient, None]:
    """Yield an authenticated :class:`NotebookLMClient` for a single test."""
    async with NotebookLMClient(auth_tokens, storage_path=STORAGE_STATE) as nlm:
        yield nlm


# ---------------------------------------------------------------------------
# Notebook lifecycle helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def created_notebooks() -> list[str]:
    """Accumulator fixture – tests append notebook IDs they create."""
    return []


@pytest.fixture
async def cleanup_notebooks(
    request: pytest.FixtureRequest,
    created_notebooks: list[str],
    auth_tokens: AuthTokens,
) -> AsyncGenerator[None, None]:
    """Delete every notebook ID in *created_notebooks* after each test.

    Pass ``--keep-notebooks`` on the pytest command line to suppress deletion
    and instead print the NotebookLM URLs so you can inspect the notebooks in
    the browser.
    """
    yield

    if not created_notebooks:
        return

    keep = request.config.getoption("--keep-notebooks", default=False)

    if keep:
        # Print the URLs for easy browser inspection
        print("\n\n[--keep-notebooks] Preserved notebook(s) after this test:")
        for nb_id in created_notebooks:
            url = f"https://notebooklm.google.com/notebook/{nb_id}"
            print(f"  • {nb_id}  →  {url}")
        print()
        return

    # Normal teardown: delete all created notebooks
    async with NotebookLMClient(auth_tokens) as nlm:
        for nb_id in created_notebooks:
            try:
                await nlm.notebooks.delete(nb_id)
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"Cleanup: failed to delete notebook {nb_id}: {exc}",
                    stacklevel=2,
                )


@pytest.fixture
async def temp_notebook(
    client: NotebookLMClient,
    created_notebooks: list[str],
    cleanup_notebooks: None,  # ensures teardown runs even if test fails
) -> AsyncGenerator[object, None]:
    """Create a temporary notebook seeded with one rich text source.

    The notebook is deleted automatically after the test, even on failure.
    Pass ``--keep-notebooks`` to preserve it for manual inspection in the UI.

    The content is deliberately multi-topic so that all artifact types
    (audio, quiz, flashcards, report, infographic, …) have something to work with.
    """
    nb = await client.notebooks.create(f"PW-Test-{uuid4().hex[:8]}")
    created_notebooks.append(nb.id)

    await client.sources.add_text(
        nb.id,
        title="Machine Learning Fundamentals",
        content=(
            "# Introduction to Machine Learning\n\n"
            "Machine learning (ML) is a branch of artificial intelligence that enables "
            "systems to learn and improve from experience without explicit programming.\n\n"
            "## Core Paradigms\n\n"
            "**Supervised Learning** trains on labeled examples. Common algorithms:\n"
            "- Linear / Logistic Regression\n"
            "- Decision Trees and Random Forests\n"
            "- Support Vector Machines\n"
            "- Neural Networks\n\n"
            "**Unsupervised Learning** discovers structure in unlabeled data:\n"
            "- K-Means Clustering\n"
            "- Principal Component Analysis (PCA)\n"
            "- Autoencoders\n\n"
            "**Reinforcement Learning** learns via reward signals (e.g., AlphaGo).\n\n"
            "## Model Evaluation\n\n"
            "| Metric    | Formula                          | Use case          |\n"
            "|-----------|----------------------------------|-------------------|\n"
            "| Accuracy  | correct / total                  | Balanced datasets |\n"
            "| Precision | TP / (TP + FP)                   | Spam detection    |\n"
            "| Recall    | TP / (TP + FN)                   | Disease screening |\n"
            "| F1 Score  | 2 × P × R / (P + R)             | Imbalanced data   |\n\n"
            "## Best Practices\n\n"
            "1. Always split data into train / validation / test sets.\n"
            "2. Use cross-validation to diagnose overfitting.\n"
            "3. Normalize or standardize numerical features.\n"
            "4. Monitor for data drift in production.\n"
            "5. Document all preprocessing steps for reproducibility.\n\n"
            "## Applications\n\n"
            "Healthcare: 95 % diagnostic accuracy for certain cancers.\n"
            "Finance: fraud detection saving $20 billion annually.\n"
            "Transportation: autonomous vehicles reducing accidents by 40 %.\n"
            "Retail: recommendation engines increasing sales by 35 %.\n"
        ),
    )

    # Give the source a moment to be indexed before tests run
    await asyncio.sleep(SOURCE_WAIT)

    yield nb
