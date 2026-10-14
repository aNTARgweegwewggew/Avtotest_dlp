#!/usr/bin/env bash

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$PROJECT_ROOT/.venv/bin/python}"

usage() {
    printf 'Использование: %s {quick|google|cloud|mail|yandex-mail|all}\n' "$0" >&2
}

if [[ $# -ne 1 ]]; then
    usage
    exit 2
fi

case "$1" in
    quick)
        test_paths=(tests/mail)
        ;;
    google)
        test_paths=(tests/browsers/test_upload_file_in_google_drive.py)
        ;;
    cloud)
        test_paths=(
            tests/browsers/test_upload_file_in_google_drive.py
            tests/browsers/test_upload_file_in_yandex_disc.py
        )
        ;;
    mail)
        test_paths=(tests/smtp)
        ;;
    yandex-mail)
        test_paths=(tests/smtp/test_yandex_mail.py)
        ;;
    all)
        test_paths=(tests)
        ;;
    *)
        usage
        exit 2
        ;;
esac

if [[ ! -x "$PYTHON" ]]; then
    printf 'Не найден Python для тестов: %s\n' "$PYTHON" >&2
    exit 2
fi

cd "$PROJECT_ROOT"

run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
run_dir="$PROJECT_ROOT/artifacts/test-runs/$run_id"
if ! mkdir -p "$run_dir"; then
    printf 'Не удалось создать папку результатов: %s\n' "$run_dir" >&2
    exit 2
fi
chmod 700 "$run_dir"

log_file="$run_dir/output.log"
status_file="$run_dir/exit-code.txt"
summary_file="$run_dir/summary.txt"

printf 'Набор тестов: %s\nЗапуск: %s\n' "$1" "$run_id" | tee "$summary_file"
printf 'Команда: %s -m pytest -v' "$PYTHON" | tee -a "$summary_file"
printf ' %q' "${test_paths[@]}" | tee -a "$summary_file"
printf '\nРезультаты: %s\n\n' "$run_dir" | tee -a "$summary_file"

"$PYTHON" -m pytest -v "${test_paths[@]}" 2>&1 | tee "$log_file"
pipeline_status=("${PIPESTATUS[@]}")
test_status="${pipeline_status[0]}"
tee_status="${pipeline_status[1]}"

printf '%s\n' "$test_status" > "$status_file"
chmod 600 "$log_file" "$status_file" "$summary_file"

if [[ "$tee_status" -ne 0 ]]; then
    printf 'Не удалось полностью сохранить вывод тестов в %s\n' "$log_file" >&2
    exit 2
fi

if [[ "$test_status" -eq 0 ]]; then
    printf 'Итог: успешно\n' | tee -a "$summary_file"
else
    printf 'Итог: ошибка (код %s)\n' "$test_status" | tee -a "$summary_file"
fi

exit "$test_status"
