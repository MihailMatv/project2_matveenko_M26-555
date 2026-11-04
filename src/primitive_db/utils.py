import json
import os

from primitive_db.constants import DATA_DIR, ENCODING, JSON_INDENT


def load_metadata(filepath):
    """Загружает метаданные или возвращает пустой словарь."""
    try:
        with open(filepath, encoding=ENCODING) as source:
            metadata = json.load(source)
    except FileNotFoundError:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("Некорректный формат метаданных.")
    return metadata


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    save_json(filepath, data)


def save_json(filepath, data):
    """Записывает JSON через временный файл."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    temporary = f"{filepath}.tmp"
    with open(temporary, "w", encoding=ENCODING) as output:
        json.dump(data, output, ensure_ascii=False, indent=JSON_INDENT)
    os.replace(temporary, filepath)


def table_path(table_name):
    """Возвращает путь к файлу таблицы."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Читает записи таблицы; для нового файла возвращает список."""
    try:
        with open(table_path(table_name), encoding=ENCODING) as source:
            data = json.load(source)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError(f'Некорректный формат данных таблицы "{table_name}".')
    return data


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в отдельный JSON-файл."""
    save_json(table_path(table_name), data)


def remove_table_data(table_name):
    """Удаляет файл данных вместе с таблицей."""
    filepath = table_path(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)
