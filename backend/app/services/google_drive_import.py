"""
Download a spreadsheet from Google Drive using the user's OAuth access token.

Used by the POST /api/admin/import-google-drive endpoint: the frontend sends
token + file id, we download the file (or export Google Sheets as xlsx), then
the API saves it to a temp file and runs the same import pipeline as for local Excel.
"""
import logging
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"


def download_drive_file(access_token: str, file_id: str) -> tuple[bytes, str]:
    """
    Download file from Google Drive using the user's access token.
    Returns (file_content_bytes, filename_for_display).
    For native Google Sheets, exports as xlsx.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    with httpx.Client(timeout=60.0) as client:
        # Get file metadata (name, mimeType)
        meta_resp = client.get(
            f"{DRIVE_API_BASE}/files/{file_id}",
            headers=headers,
            params={"fields": "name,mimeType"},
        )
        meta_resp.raise_for_status()
        meta = meta_resp.json()
        name = meta.get("name", "export.xlsx") or "export.xlsx"
        mime = (meta.get("mimeType") or "").strip()

        if mime == GOOGLE_SHEETS_MIMETYPE:
            # Export native Google Sheet as xlsx
            export_resp = client.get(
                f"{DRIVE_API_BASE}/files/{file_id}/export",
                headers=headers,
                params={"mimeType": DRIVE_UPLOAD_MIMETYPE},
            )
            export_resp.raise_for_status()
            content = export_resp.content
            if not name.lower().endswith(".xlsx"):
                name = name.rsplit(".", 1)[0] + ".xlsx"
        else:
            # Binary download (e.g. uploaded xlsx)
            down_resp = client.get(
                f"{DRIVE_API_BASE}/files/{file_id}",
                headers=headers,
                params={"alt": "media"},
            )
            down_resp.raise_for_status()
            content = down_resp.content

    return content, name


def save_to_temp_and_run_path(content: bytes, filename: str) -> Path:
    """Write the downloaded bytes to a temporary file and return its path. Caller must delete the file when done."""
    suffix = Path(filename).suffix or ".xlsx"
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="revolusun_import_")
    try:
        with open(fd, "wb") as f:
            f.write(content)
        return Path(path)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise
