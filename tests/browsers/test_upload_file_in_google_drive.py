"""Проверка загрузки, скачивания и удаления тестового файла Google Drive."""

import logging
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from src.mail.google_drive_download import download_file
from src.mail.google_drive_upload import delete_file, upload_file


logger = logging.getLogger(__name__)
TEST_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cloud"
    / "avtotest-dlp-marker.txt"
)


def test_google_drive_upload_round_trip(
    google_drive_test_folder_id,
    google_token,
):
    """Передать тестовый файл в отдельную папку и сверить скачанную копию."""
    run_id = uuid.uuid4().hex
    marker = f"AVTOTEST_DLP_{run_id}"
    file_name = f"avtotest-{run_id}.txt"
    content = f"{TEST_FILE.read_text(encoding='utf-8')}\nRun marker: {marker}\n"

    logger.info("Starting Google Drive transfer test run %s", run_id)
    with TemporaryDirectory() as temp_dir:
        local_file = Path(temp_dir) / file_name
        downloaded_file = Path(temp_dir) / "downloaded" / file_name
        local_file.write_text(content, encoding="utf-8")
        uploaded = upload_file(
            google_token,
            local_file,
            google_drive_test_folder_id,
            file_name=file_name,
        )
        try:
            download_file(google_token, uploaded["id"], downloaded_file)
            assert downloaded_file.read_text(encoding="utf-8") == content
            logger.info(
                "Google Drive round-trip passed; confirm DLP incident in the "
                "ZGate incident console"
            )
        finally:
            delete_file(google_token, uploaded["id"])
