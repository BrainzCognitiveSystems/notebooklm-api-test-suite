# notebooklm-api – Playwright Test Suite

End-to-end test series for the
[notebooklm-py](https://github.com/teng-lin/notebooklm-py) Python library.

Authentication uses a **Playwright / Chromium browser session** recorded by
`notebooklm login` and stored in `notebooklm-storage/storage_state.json`.
No browser is launched during the test run itself; the saved cookies are
injected directly into the HTTP client.

---

## Directory layout

```
notebooklm-api/
├── notebooklm-storage/
│   └── storage_state.json          ← Playwright session (already recorded)
├── notebooklm-py/                  ← library source (cloned from GitHub)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 ← shared fixtures & auth bootstrap
│   ├── helpers.py                  ← file factories, poll helper, validators
│   ├── test_01_notebook_management.py
│   ├── test_02_source_management.py
│   ├── test_03_chat_api.py
│   └── test_04_artifact_generation.py
├── pytest.ini                      ← pytest configuration
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10 + | Matches the library minimum |
| Recorded Playwright session | `notebooklm-storage/storage_state.json` must exist |

To record a fresh session:

```bash
pip install notebooklm-py[browser]
notebooklm login
# ↑ opens Chromium, log in with Google, session is saved automatically
```

---

## Quick start

```bash
# 1 – install all dependencies (library + test tools)
pip install -r requirements.txt

# 2 – run the full suite
pytest

# 3 – run only fast/read tests (skip the long generation+download tests)
pytest -m "not slow"

# 4 – run a single file
pytest tests/test_01_notebook_management.py -v

# 5 – run with verbose output and stop on first failure
pytest -x -v

# 6 – run generation + download tests (these can take up to 10 min each)
pytest -m slow --timeout=600

# 7 – preserve notebooks after the test so you can inspect them in the UI
pytest --keep-notebooks
```

### Preserving temporary notebooks for inspection

By default every notebook created during a test is **deleted** in teardown.
Pass `--keep-notebooks` to skip deletion.  The notebook URL(s) are printed at
the end of teardown so you can open them directly in your browser:

```
[--keep-notebooks] Preserved notebook(s) after this test:
  • f36b1e0b-33e6-4d4f-b80c-4cd9b8f84fed
      → https://notebooklm.google.com/notebook/f36b1e0b-33e6-4d4f-b80c-4cd9b8f84fed
```

You can combine the flag with any test filter:

```bash
# Inspect the notebook after a specific test
pytest tests/test_04_artifact_generation.py::test_generate_quiz_starts \
       --keep-notebooks -s

# Inspect after every test in the artifact module
pytest tests/test_04_artifact_generation.py --keep-notebooks -s
```

> **Note** `--keep-notebooks` leaves notebooks on your account. Remember to
> delete them manually afterwards from the NotebookLM UI or by running the
> suite again without the flag.

---

## Test modules

### `test_01_notebook_management.py` – 1. Notebook Management

| Test | What it checks |
|---|---|
| `test_list_notebooks_*` | `list()` returns `Notebook` objects with non-empty id/title |
| `test_create_notebook` | `create()` echoes the requested title |
| `test_get_notebook_by_id` | `get()` returns the correct notebook |
| `test_rename_notebook` | `rename()` updates the title (verified by `get()`) |
| `test_delete_notebook` | `delete()` removes the notebook from `list()` |
| `test_get_summary_*` | `get_summary()` returns non-empty text |
| `test_get_description_*` | `get_description()` returns `NotebookDescription` with topics |
| `test_get_metadata_*` | `get_metadata()` reflects the seeded source |

### `test_02_source_management.py` – 2. Source Management

| Test | What it checks |
|---|---|
| `test_add_url_source` | `add_url()` returns a Source with non-empty id |
| `test_add_url_source_wait_until_ready` | `wait=True` → source is `READY` |
| `test_add_youtube_source` | YouTube URL accepted without error |
| `test_add_text_source` | `add_text()` creates a `PASTED_TEXT` source |
| `test_upload_pdf_file` | PDF upload → `SourceType.PDF` |
| `test_upload_markdown_file` | Markdown upload → `SourceType.MARKDOWN` |
| `test_upload_csv_file` | CSV upload → `SourceType.CSV` |
| `test_upload_docx_file` | DOCX upload → `SourceType.DOCX` |
| `test_upload_epub_file` | EPUB upload → `SourceType.EPUB` |
| `test_get_fulltext_*` | `get_fulltext()` returns non-empty `SourceFulltext` |
| `test_get_source_guide` | `get_guide()` returns `summary` + `keywords` |
| `test_delete_source` | `delete()` removes source from `list()` |
| `test_get_source_by_id` | `get()` returns the exact matching source |
| `test_wait_until_ready` | `wait_until_ready()` returns `READY` source |

### `test_03_chat_api.py` – 3. Chat API

| Test | What it checks |
|---|---|
| `test_ask_returns_ask_result` | `ask()` returns `AskResult` with non-empty answer |
| `test_ask_new_conversation_*` | First ask → `is_follow_up=False`, `turn_number≥1` |
| `test_ask_followup_increments_turn` | Second ask in same conversation → higher `turn_number` |
| `test_ask_references_*` | `references` is a list; each has `source_id` |
| `test_get_history_*` | `get_history()` returns list; grows after `ask()` |
| `test_get_conversation_turns` | `get_conversation_turns()` completes without error |
| `test_ask_with_specific_source_ids` | Source-scoped ask succeeds |

### `test_04_artifact_generation.py` – 4. Artifact Generation

**Fast generation-start tests** (no wait, complete in seconds):

| Test | Artifact type |
|---|---|
| `test_generate_audio_starts` | Audio Overview |
| `test_generate_video_starts` | Video Overview |
| `test_generate_report_briefing_doc` | Briefing Doc report |
| `test_generate_report_study_guide` | Study Guide report |
| `test_generate_quiz_starts` | Quiz |
| `test_generate_flashcards_starts` | Flashcards |
| `test_generate_slide_deck_starts` | Slide Deck |
| `test_generate_infographic_starts` | Infographic |
| `test_generate_data_table_starts` | Data Table |
| `test_generate_mind_map` | Mind Map |

**Full generate → poll → download tests** (`@pytest.mark.timeout(600)`):

| Test | Output format |
|---|---|
| `test_poll_and_download_audio` | MP4 audio |
| `test_poll_and_download_video` | MP4 video |
| `test_poll_and_download_report` | Markdown |
| `test_poll_and_download_quiz_json` | JSON |
| `test_poll_and_download_quiz_markdown` | Markdown |
| `test_poll_and_download_flashcards_json` | JSON |
| `test_poll_and_download_flashcards_markdown` | Markdown |
| `test_poll_and_download_slide_deck_pdf` | PDF |
| `test_poll_and_download_infographic` | PNG |
| `test_poll_and_download_data_table_csv` | CSV |
| `test_poll_and_download_mind_map` | JSON |

**Task-polling tests:**

| Test | What it checks |
|---|---|
| `test_poll_status_returns_generation_status` | `poll_status()` returns `GenerationStatus` |
| `test_wait_for_completion` | `wait_for_completion()` returns terminal status |

**Listing & management:**

| Test | What it checks |
|---|---|
| `test_list_*_artifacts` | Type-specific `list_*()` returns correct `ArtifactType` |
| `test_get_artifact_not_found_returns_none` | `get()` with bad id → `None` |
| `test_delete_artifact` | `delete()` removes artifact from `list()` |
| `test_suggest_reports` | `suggest_reports()` returns a list |

---

## Configuration

### `pytest.ini`

```ini
asyncio_mode = auto      # all async tests run without explicit decorator
timeout = 90             # default per-test timeout (seconds)
```

Override per test with `@pytest.mark.timeout(N)`.

### `tests/conftest.py` constants

| Constant | Default | Purpose |
|---|---|---|
| `SOURCE_WAIT` | 3 s | Pause after source add for indexing |
| `POLL_INTERVAL` | 5 s | Base interval for `poll_until_complete()` |
| `ARTIFACT_TIMEOUT` | 300 s | Maximum time in `poll_until_complete()` |
| `GENERATION_COOLDOWN` | 10 s | Pause after generation tests |

---

## Rate-limiting behaviour

Google imposes per-account quotas on artifact generation.  When the API
returns a rate-limit error:

* `assert_generation_started()` calls `pytest.skip()` instead of failing.
* `poll_until_complete()` also calls `pytest.skip()` when the task enters
  the `failed` state with a rate-limit error code.

This means the suite stays green even when running against accounts that
have already generated several artifacts today.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ERROR: Playwright storage state not found` | Run `notebooklm login` to record a session |
| `Authentication expired` | Re-run `notebooklm login` |
| Tests skip with "rate-limited by the API" | Wait 24 h for quota reset or use a different account |
| `TimeoutError` on download tests | Increase `ARTIFACT_TIMEOUT` in `conftest.py` or re-run with `--timeout=1200` |
