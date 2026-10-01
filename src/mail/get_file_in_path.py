def get_files(directory):
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
        for path in directory.iterdir()
        if path.is_file()
    ]

    if not files:
        raise RuntimeError(
            f"В папке нет файлов: {directory}"
        )

    return sorted(files)