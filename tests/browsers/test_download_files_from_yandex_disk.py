from pathlib import Path

from src.mail.yandex_disk_download import download_file


YANDEX_DISK_DIR = "/DLP_TEST"

DOWNLOAD_DIR = Path(
    "/home/user/download_yandex"
)


def test_download_files(yandex_token):
    download_file(
        yandex_token,
        YANDEX_DISK_DIR,
        DOWNLOAD_DIR
    )

    actual_files = [
        file
        for file in DOWNLOAD_DIR.iterdir()
        if file.is_file()
    ]

    assert len(actual_files) == 3