"""Shared test-support utilities.

Provides:
- Minimal yet valid binary file factories (PDF, DOCX, EPUB, PNG, JPG, CSV, MD).
- ``poll_until_complete`` – awaitable helper that polls an artifact task with
  exponential back-off and raises on timeout or failure.
- Magic-byte checkers used in download assertions.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import zipfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Minimal file factories
# ---------------------------------------------------------------------------


def create_minimal_pdf(path: Path) -> None:
    """Write a syntactically correct single-page PDF to *path*."""
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF for NotebookLM) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000210 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
310
%%EOF"""
    path.write_bytes(content)


def create_minimal_docx(path: Path) -> None:
    """Write a minimal but parseable DOCX (ZIP-based) to *path*."""
    content_types = b"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>"""

    document = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>Test DOCX content for NotebookLM upload testing.</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)
    path.write_bytes(buf.getvalue())


def create_minimal_epub(path: Path) -> None:
    """Write a minimal EPUB 3 file to *path*."""
    mimetype = b"application/epub+zip"

    container_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    content_opf = b"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:12345678-1234-1234-1234-123456789abc</dc:identifier>
    <dc:title>Test EPUB</dc:title>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">2025-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml"
          media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml"
          media-type="application/xhtml+xml" properties="nav"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>"""

    chapter = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
  <h1>Chapter 1</h1>
  <p>Test EPUB content for NotebookLM upload testing.</p>
</body>
</html>"""

    nav = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <ol><li><a href="chapter1.xhtml">Chapter 1</a></li></ol>
  </nav>
</body>
</html>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be stored uncompressed per EPUB spec
        zf.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/chapter1.xhtml", chapter)
        zf.writestr("OEBPS/nav.xhtml", nav)
    path.write_bytes(buf.getvalue())


def create_minimal_png(path: Path) -> None:
    """Write a 1×1 transparent PNG to *path*."""
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path.write_bytes(png)


def create_minimal_csv(path: Path) -> None:
    """Write a simple CSV with header and one data row to *path*."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Name", "Value", "Description"])
        w.writerow(["Alpha", "1", "First item"])
        w.writerow(["Beta", "2", "Second item"])


def create_minimal_markdown(path: Path) -> None:
    """Write a small Markdown document to *path*."""
    path.write_text(
        "# Test Markdown Document\n\n"
        "## Introduction\n\n"
        "This is a minimal Markdown file for testing purposes.\n\n"
        "## Key Points\n\n"
        "- Point one\n"
        "- Point two\n"
        "- Point three\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Magic-byte file-type validators (used in download assertions)
# ---------------------------------------------------------------------------

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_PDF_MAGIC = b"%PDF"
_MP4_FTYP = b"ftyp"   # located at offset 4 in valid MP4 / AAC containers


def is_valid_png(path: str | Path) -> bool:
    with open(path, "rb") as fh:
        return fh.read(8) == _PNG_MAGIC


def is_valid_pdf(path: str | Path) -> bool:
    with open(path, "rb") as fh:
        return fh.read(4) == _PDF_MAGIC


def is_valid_mp4(path: str | Path) -> bool:
    """Return True when the file looks like an MP4 container."""
    with open(path, "rb") as fh:
        header = fh.read(12)
    return len(header) >= 8 and header[4:8] == _MP4_FTYP


def is_valid_markdown(path: str | Path) -> bool:
    """Return True when the file has non-empty text content."""
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    return len(content) > 0


def is_valid_json(path: str | Path) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            json.load(fh)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def is_valid_csv(path: str | Path) -> bool:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
        return len(rows) > 0 and len(rows[0]) > 0
    except (csv.Error, OSError, UnicodeDecodeError):
        return False


# ---------------------------------------------------------------------------
# Artifact polling helper
# ---------------------------------------------------------------------------


async def poll_until_complete(
    client,
    notebook_id: str,
    task_id: str,
    *,
    interval: float = 5.0,
    timeout: float = 300.0,
    allow_failed: bool = False,
):
    """Poll *task_id* until it completes (or fails), then return the final status.

    Args:
        client: An open :class:`~notebooklm.NotebookLMClient`.
        notebook_id: The notebook that owns the artifact.
        task_id: The task / artifact ID returned by ``generate_*``.
        interval: Seconds between polls (uses exponential back-off up to 2× interval).
        timeout: Maximum wall-clock seconds before raising :exc:`TimeoutError`.
        allow_failed: When *True*, a ``failed`` status is returned instead of
            raising, useful for rate-limit tests.

    Returns:
        :class:`~notebooklm.types.GenerationStatus` in state ``"completed"``
        (or ``"failed"`` when *allow_failed* is True).

    Raises:
        TimeoutError: When the task does not finish within *timeout* seconds.
        AssertionError: When the task fails and *allow_failed* is False.
    """
    from notebooklm.exceptions import RPCTimeoutError  # noqa: PLC0415

    elapsed = 0.0
    current_interval = interval

    while elapsed < timeout:
        try:
            status = await client.artifacts.poll_status(notebook_id, task_id)
        except RPCTimeoutError:
            # Network hiccup – continue polling
            await asyncio.sleep(current_interval)
            elapsed += current_interval
            current_interval = min(current_interval * 2, interval * 4)
            continue

        if status.is_complete:
            return status

        if status.is_failed:
            if allow_failed:
                return status
            if status.is_rate_limited:
                pytest.skip(f"Artifact {task_id}: rate-limited during generation")
            pytest.fail(f"Artifact {task_id} failed: {status.error}")

        await asyncio.sleep(current_interval)
        elapsed += current_interval
        current_interval = min(current_interval * 2, interval * 4)

    raise TimeoutError(
        f"Artifact {task_id} did not complete within {timeout:.0f} s "
        f"(last status: {status.status!r})"
    )
