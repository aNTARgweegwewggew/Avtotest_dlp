import time

import requests


YANDEX_DOWNLOAD_URL = (
    "https://cloud-api.yandex.net/v1/disk/resources/download"
)

YANDEX_GET_FILE_IN_PATH = (
    "https://cloud-api.yandex.net/v1/disk/resources"
)


def get_disk_files(access_token, disk_path):
    headers = {
        "Authorization": f"OAuth {access_token}"
    }

    for attempt in range(3):
        try:
            response = requests.get(
                YANDEX_GET_FILE_IN_PATH,
                headers=headers,
                params={
                    "path": disk_path,
                },
                verify=False,
                timeout=(5, 15)
            )

            response.raise_for_status()

            items = response.json()["_embedded"]["items"]

            return [
                item["name"]
                for item in items
                if item["type"] == "file"
            ]

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):
            if attempt == 2:
                raise

            time.sleep(1)


def get_download_url(access_token, disk_path):
    headers = {
        "Authorization": f"OAuth {access_token}"
    }

    for attempt in range(3):
        try:
            response = requests.get(
                YANDEX_DOWNLOAD_URL,
                headers=headers,
                params={
                    "path": disk_path,
                },
                verify=False,
                timeout=(5, 15)
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


def download_file(
    access_token,
    disk_path,
    download_dir
):
    file_path = get_disk_files(
        access_token,
        disk_path
    )

    for file in file_path:
        file_disk_path = (
            f"{disk_path}/{file}"
        )

        download_url = get_download_url(
            access_token,
            file_disk_path
        )

        for attempt in range(3):
            try:
                response = requests.get(
                    download_url,
                    verify=False,
                    timeout=(5, 30)
                )

                response.raise_for_status()

                local_path = download_dir / file

                with local_path.open("wb") as output_file:
                    output_file.write(response.content)

                break

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError
            ):
                if attempt == 2:
                    raise

                time.sleep(1)