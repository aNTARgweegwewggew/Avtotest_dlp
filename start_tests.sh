#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_URL="${REPOSITORY_URL:-https://github.com/aNTARgweegwewggew/Avtotest_dlp.git}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/Avtotest_dlp}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$SCRIPT_DIR/requirements.txt" ]]; then
    if ! command -v git >/dev/null 2>&1; then
        printf 'Для загрузки проекта нужна программа git.\n' >&2
        exit 1
    fi

    if [[ -e "$PROJECT_DIR" ]]; then
        if [[ ! -d "$PROJECT_DIR/.git" ]]; then
            printf 'Папка уже существует и не является Git-проектом: %s\n' \
                "$PROJECT_DIR" >&2
            exit 1
        fi

        existing_url="$(git -C "$PROJECT_DIR" remote get-url origin)"
        if [[ "$existing_url" != "$REPOSITORY_URL" ]]; then
            printf 'В папке находится другой Git-проект: %s\n' \
                "$PROJECT_DIR" >&2
            exit 1
        fi
    else
        printf 'Клонирую проект в %s\n' "$PROJECT_DIR"
        git clone "$REPOSITORY_URL" "$PROJECT_DIR"
    fi

    exec bash "$PROJECT_DIR/start_tests.sh"
fi

cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    printf 'Не найден python3. Установи Python 3 и запусти скрипт снова.\n' >&2
    exit 1
fi

if [[ ! -d .venv ]]; then
    printf 'Создаю виртуальное окружение .venv\n'
    python3 -m venv .venv
fi

printf 'Устанавливаю зависимости проекта\n'
.venv/bin/python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env
    printf '\nСоздан .env из шаблона. Заполни нужные настройки перед запуском тестов.\n'
fi

mkdir -p secrets

test_folders=()
while IFS= read -r folder; do
    if find "$folder" -type f -name 'test_*.py' -print -quit | grep -q .; then
        test_folders+=("$folder")
    fi
done < <(find tests -mindepth 1 -maxdepth 1 -type d -print | sort)

if [[ ${#test_folders[@]} -eq 0 ]]; then
    printf 'В папке tests не найдено каталогов с тестами.\n' >&2
    exit 1
fi

last_test_status=0

while true; do
    printf '\nВыбери папку тестов:\n'
    for index in "${!test_folders[@]}"; do
        printf '  %s) %s\n' "$((index + 1))" "${test_folders[$index]}"
    done
    all_option="$((${#test_folders[@]} + 1))"
    printf '  %s) Все тесты\n' "$all_option"
    printf '  0) Выход\n'
    read -r -p 'Номер: ' choice

    if [[ "$choice" == "0" ]]; then
        exit "$last_test_status"
    fi
    if [[ "$choice" == "$all_option" ]]; then
        selected_path="tests"
    elif [[ "$choice" =~ ^[0-9]+$ ]] \
        && ((choice >= 1 && choice <= ${#test_folders[@]})); then
        selected_path="${test_folders[$((choice - 1))]}"
    else
        printf 'Нет такого пункта меню. Попробуй ещё раз.\n'
        continue
    fi

    printf '\nЗапускаю тесты из %s\n\n' "$selected_path"
    if .venv/bin/python -m pytest -v "$selected_path"; then
        last_test_status=0
    else
        last_test_status=$?
        printf '\nТесты завершились с ошибкой (код %s).\n' "$last_test_status"
    fi
    printf '\n'
done
