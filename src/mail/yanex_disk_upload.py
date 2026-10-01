import time

import requests


YANDEX_UPLOAD_URL = (
    "https://cloud-api.yandex.net/v1/disk/resources/upload"
)


def get_upload_url(access_token, disk_path):
    headers = {
        "Authorization": f"OAuth {access_token}"
    }

    for attempt in range(3):
        try:
            response = requests.get(
                YANDEX_UPLOAD_URL,
                headers=headers,
                params={
                    "path": disk_path,
                    "overwrite": "true"
                },
                verify=False,
                timeout=(5,15)
            )

            response.raise_for_status()

            return response.json()["href"]

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):
            if attempt == 2:
                raise

            time.sleep(1)


def upload_file(
    access_token,
    file_path,
    disk_path
):
    upload_url = get_upload_url(
        access_token,
        disk_path
    )

    for attempt in range(3):

        try:
            with file_path.open("rb") as file:
                response = requests.put(
                    upload_url,
                    files={
                        "file": (
                            file_path.name,
                            file,
                            "application/octet-stream"
                        )
                    },
                    verify=False,
                    timeout=(5,30)
                )

            response.raise_for_status()

            return

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):
            if attempt == 2:
                raise

            time.sleep(1)