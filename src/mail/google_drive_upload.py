import time

import requests


GOOGLE_UPLOAD_URL = (
    "https://www.googleapis.com/upload/drive/v3/files"
)


def get_upload_url(
    access_token,
    file_path,
    folder_id
):
    file_size = file_path.stat().st_size

    metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "application/octet-stream",
        "X-Upload-Content-Length": str(file_size),
    }

    for attempt in range(3):
        try:
            response = requests.post(
                GOOGLE_UPLOAD_URL,
                params={
                    "uploadType": "resumable"
                },
                headers=headers,
                json=metadata,
                verify=False,
                timeout=(5, 15),
            )

            response.raise_for_status()

            upload_url = response.headers.get("Location")

            if not upload_url:
                raise RuntimeError(
                    "Google не вернул Location"
                )

            return upload_url

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            if attempt == 2:
                raise

            time.sleep(1)


def upload_file(
    access_token,
    file_path,
    folder_id
):
    upload_url = get_upload_url(
        access_token,
        file_path,
        folder_id,
    )

    file_size = file_path.stat().st_size

    for attempt in range(3):
        try:
            with file_path.open("rb") as file:
                response = requests.put(
                    upload_url,
                    data=file,
                    headers={
                        "Content-Type": (
                            "application/octet-stream"
                        ),
                        "Content-Length": str(file_size),
                    },
                    verify=False,
                    timeout=(5, 60),
                )

            response.raise_for_status()

            result = response.json()

            print(
                f"Uploaded: {file_path.name}"
            )
            print(
                f"Google Drive ID: {result['id']}"
            )

            return result

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            if attempt == 2:
                raise

            time.sleep(1)