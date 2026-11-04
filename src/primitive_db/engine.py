import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import HELP_TEXT, ID_COLUMN, META_FILE
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Показывает синтаксис команд."""
    print(HELP_TEXT)


def welcome():
    """Выводит приветствие и справку при запуске."""
    print("***База данных***")
    print_help()


def print_rows(schema, rows):
    """Выводит записи с заголовками столбцов."""
    output = PrettyTable()
    output.field_names = list(schema)
    for row in rows:
        output.add_row([row[column] for column in schema])
    print(output)


def manage_tables(metadata, command):
    """Обрабатывает создание, удаление и просмотр таблиц."""
    action = command["command"]
    if action == "list_tables":
        if not metadata:
            print("Таблиц пока нет.")
        for table_name in sorted(metadata):
            print(f"- {table_name}")
        return

    table_name = command["table_name"]
    if action == "create_table":
        result = core.create_table(metadata, table_name, command["columns"])
        if result is not None:
            save_table_data(table_name, [])
            save_metadata(META_FILE, result)
            columns = ", ".join(result[table_name])
            print(f'Таблица "{table_name}" успешно создана со столбцами: {columns}')
        return

    core.get_schema(metadata, table_name)
    if action == "drop_table":
        result = core.drop_table(metadata, table_name)
        if result is not None:
            save_metadata(META_FILE, result)
            print(f'Таблица "{table_name}" успешно удалена.')
    elif action == "info":
        rows = load_table_data(table_name)
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {', '.join(metadata[table_name])}")
        print(f"Количество записей: {len(rows)}")


def manage_records(metadata, command):
    """Загружает данные, вызывает CRUD и сохраняет изменения."""
    action = command["command"]
    table_name = command["table_name"]
    schema = core.get_schema(metadata, table_name)
    if action == "insert":
        result = core.insert(metadata, table_name, command["values"])
        if result is not None:
            save_table_data(table_name, result)
            new_id = result[-1][ID_COLUMN]
            print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
        return

    condition = command["where_clause"]
    if condition is not None:
        core.validate_fields(schema, condition)
    table_data = load_table_data(table_name)
    if action == "select":
        result = core.select(table_data, condition)
        if result is not None:
            print_rows(schema, result)
        return

    affected_ids = [
        row[ID_COLUMN] for row in table_data if core.matches(row, condition)
    ]
    if action == "update":
        core.validate_fields(schema, command["set_clause"], allow_id=False)
        result = core.update(table_data, command["set_clause"], condition)
    else:
        result = core.delete(table_data, condition)
    if result is None:
        return
    save_table_data(table_name, result)
    if not affected_ids:
        print("Подходящих записей не найдено.")
    for row_id in affected_ids:
        if action == "update":
            print(f'Запись с ID={row_id} в таблице "{table_name}" успешно обновлена.')
        else:
            print(f'Запись с ID={row_id} успешно удалена из таблицы "{table_name}".')


@handle_db_errors
def execute_command(text):
    """Разбирает команду и возвращает False для завершения работы."""
    command = parse_command(text)
    action = command["command"]
    if action == "exit":
        return False
    if action == "help":
        print_help()
    elif action in {"create_table", "drop_table", "list_tables", "info"}:
        manage_tables(load_metadata(META_FILE), command)
    elif action in {"insert", "select", "update", "delete"}:
        manage_records(load_metadata(META_FILE), command)
    else:
        print(f"Функции {action} нет. Попробуйте снова.")
    return True


def run():
    """Читает команды, продолжая работу после ошибок ввода."""
    welcome()
    while True:
        try:
            user_input = prompt.string("Введите команду: ", empty=True)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input.strip():
            continue
        if execute_command(user_input) is False:
            break
