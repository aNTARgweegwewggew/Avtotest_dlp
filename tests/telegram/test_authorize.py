"""Локальные проверки отдельной команды авторизации Telegram."""

from unittest.mock import Mock

import pytest

from src.telegram import authorize


def test_authorization_requires_an_interactive_terminal(monkeypatch):
    """Не запускать ввод телефона и кода из фонового процесса."""
    terminal = Mock()
    terminal.isatty.return_value = False
    create_client = Mock()
    monkeypatch.setattr(authorize.sys, "stdin", terminal)
    monkeypatch.setattr(authorize, "create_telegram_client", create_client)

    with pytest.raises(SystemExit, match="интерактивный терминал"):
        authorize.main()

    create_client.assert_not_called()


def test_authorization_starts_client_only_when_called_explicitly(
    monkeypatch,
    capsys,
):
    """В явной команде выполнить вход и закрыть клиент."""
    terminal = Mock()
    terminal.isatty.return_value = True
    client = Mock()
    client.is_user_authorized.return_value = True
    monkeypatch.setattr(authorize.sys, "stdin", terminal)
    monkeypatch.setattr(authorize, "create_telegram_client", lambda: client)

    authorize.main()

    client.start.assert_called_once()
    client.disconnect.assert_called_once()
    assert "успешно сохранена" in capsys.readouterr().out
