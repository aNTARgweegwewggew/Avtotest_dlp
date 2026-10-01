from pathlib import Path

from src.mail.get_file_in_path import get_files
from src.mail.yanex_disk_upload import upload_file


TEST_FILES_DIR = Path(
    "/home/user/test_yandex"
)

YANDEX_DISK_DIR = "/DLP_TEST"


def test_upload_files(yandex_token):
    files = get_files(TEST_FILES_DIR)

    for file_path in files:
        disk_path = (
            f"{YANDEX_DISK_DIR}/{file_path.name}"
        )

        upload_file(
            yandex_token,
            file_path,
            disk_path
        )