"""Поиск файлов тестовых данных в указанной папке."""


def get_files(directory):
    """Найти все файлы в папке и вернуть их в отсортированном порядке."""
    if not directory.exists():
        raise RuntimeError(
            f"Папка не существует: {directory}"
        )

    if not directory.is_dir():
        raise RuntimeError(
            f"Это не папка: {directory}"
        )

    files = [
        path
        for path in directory.rglob("*")
        if path.is_file()
    ]

    if not files:
        raise RuntimeError(
            f"В папке нет файлов: {directory}"
        )

    return sorted(files)