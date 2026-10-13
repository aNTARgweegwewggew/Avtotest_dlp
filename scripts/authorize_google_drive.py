"""Повторная OAuth-авторизация для доступа к Google Drive."""

import argparse
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


def _token_file_path():
    """Определить путь к OAuth-файлу из настроек или по умолчанию."""
    load_dotenv(PROJECT_ROOT / ".env")
    configured_path = os.getenv("GOOGLE_DRIVE_TOKEN_FILE")
    token_file = (
        Path(configured_path).expanduser()
        if configured_path
        else PROJECT_ROOT / "google_drive_token.json"
    )
    if not token_file.is_absolute():
        token_file = PROJECT_ROOT / token_file
    return token_file


def _save_token(token_file, token_json):
    """Атомарно сохранить OAuth-данные с правами доступа только владельцу."""
    temporary_file = token_file.with_name(
        f".{token_file.name}.{uuid.uuid4().hex}.tmp"
    )
    file_descriptor = os.open(
        temporary_file,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as token_stream:
            token_stream.write(token_json)
        os.chmod(temporary_file, 0o600)
        temporary_file.replace(token_file)
    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise


def main():
    """Открыть OAuth-поток и сохранить токен после согласия пользователя."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args()

    token_file = _token_file_path()
    try:
        token_data = json.loads(token_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot read existing Google OAuth client settings "
            f"({type(error).__name__})"
        ) from None

    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")
    token_uri = token_data.get("token_uri")
    if not client_id or not client_secret or not token_uri:
        raise RuntimeError(
            "Google token file does not contain the OAuth client settings "
            "needed for re-authorization"
        )

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": token_uri,
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=[DRIVE_SCOPE],
    )
    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=arguments.port,
        open_browser=False,
        prompt="consent",
        access_type="offline",
        authorization_prompt_message="Open this URL to authorize Google Drive: {url}",
        success_message="Google Drive authorization completed. You may close this tab.",
    )
    if not credentials.refresh_token:
        raise RuntimeError(
            "Google did not return a refresh token; authorization was not saved"
        )

    _save_token(token_file, credentials.to_json())
    print("Google Drive OAuth token saved securely.")


if __name__ == "__main__":
    main()
