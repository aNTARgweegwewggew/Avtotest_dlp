from pathlib import Path

from src.mail.google_drive_upload import upload_file
from src.mail.get_file_in_path import get_files


TEST_FILES_DIR = Path(
    "/home/user/test_yandex"
)

GOOGLE_DRIVE_FOLDER_ID = (
    "1vMMfei1N_NLJ53Hc0MkGmSEpAuHrbXdL"
)


def test_upload_files(google_token):
    files = get_files(
        TEST_FILES_DIR
    )

    for file_path in files:
        upload_file(
            google_token,
            file_path,
            GOOGLE_DRIVE_FOLDER_ID,
        )