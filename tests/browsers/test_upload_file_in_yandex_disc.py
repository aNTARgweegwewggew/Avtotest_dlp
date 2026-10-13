"""Проверка загрузки и скачивания тестового файла Яндекс.Диска."""

import logging
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from src.mail.yanex_disk_upload import upload_file
from src.mail.yandex_disk_download import download_file


logger = logging.getLogger(__name__)
TEST_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cloud"
    / "avtotest-dlp-marker.txt"
)


def test_yandex_disk_upload_round_trip(
    yandex_test_folder,
):
    """Передать тестовый файл в отдельную папку и сверить скачанную копию."""
    yandex_token, remote_folder = yandex_test_folder
    run_id = uuid.uuid4().hex
    marker = f"AVTOTEST_DLP_{run_id}"
    file_name = f"avtotest-{run_id}.txt"
    content = f"{TEST_FILE.read_text(encoding='utf-8')}\nRun marker: {marker}\n"
    remote_file = f"{remote_folder}/{file_name}"

    logger.info("Starting Yandex Disk DLP test run %s", run_id)
    with TemporaryDirectory() as download_dir:
        local_source = Path(download_dir) / file_name
        local_source.write_text(content, encoding="utf-8")
        upload_status = upload_file(yandex_token, local_source, remote_file)
        assert upload_status in {201, 202}

        download_path = Path(download_dir) / "downloaded"
        downloaded_files = download_file(
            yandex_token,
            remote_folder,
            download_path,
        )
        assert [path.name for path in downloaded_files] == [file_name]
        assert downloaded_files[0].read_text(encoding="utf-8") == content

    logger.info(
        "Yandex Disk round-trip passed with upload HTTP %s; "
        "confirm DLP incident in the ZGate incident console",
        upload_status,
    )
