import json

from primitive_db.constants import (
    DELETE_ACTION,
    DROP_ACTION,
    ID_COLUMN,
    ID_DEFINITION,
    VALID_TYPES,
)
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, remove_table_data

_select_cache = create_cacher()


def get_schema(metadata, table_name):
    """Возвращает словарь столбцов и типов существующей таблицы."""
    if table_name not in metadata:
        raise KeyError(table_name)
    return dict(column.split(":") for column in metadata[table_name])


def validate_fields(schema, fields, allow_id=True):
    """Проверяет имена полей и точное соответствие типов."""
    for column, value in fields.items():
        if column not in schema:
            raise KeyError(column)
        if not allow_id and column == ID_COLUMN:
            raise ValueError("Изменять ID нельзя.")
        expected_type = VALID_TYPES[schema[column]]
        if type(value) is not expected_type:
            raise ValueError(f'Столбец "{column}" должен иметь тип {schema[column]}.')


def matches(row, where_clause):
    """Проверяет равенство полей условию, различая bool и int."""
    return all(
        column in row and type(row[column]) is type(value) and row[column] == value
        for column, value in where_clause.items()
    )


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Добавляет таблицу с автоматическим столбцом ID."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    if any(name.casefold() == table_name.casefold() for name in metadata):
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    schema = {ID_COLUMN: "int"}
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное описание столбца: {column}.")
        name, type_name = parts
        if not name.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {name}.")
        if name.upper() == ID_COLUMN or name in schema:
            raise ValueError(f'Столбец "{name}" задан повторно или зарезервирован.')
        if type_name not in VALID_TYPES:
            raise ValueError(f"Неизвестный тип: {type_name}.")
        schema[name] = type_name
    metadata[table_name] = [ID_DEFINITION] + [
        f"{name}:{type_name}" for name, type_name in schema.items() if name != ID_COLUMN
    ]
    _select_cache.clear()
    return metadata


@handle_db_errors
@confirm_action(DROP_ACTION)
def drop_table(metadata, table_name):
    """Удаляет схему и файл таблицы после подтверждения."""
    get_schema(metadata, table_name)
    remove_table_data(table_name)
    del metadata[table_name]
    _select_cache.clear()
    return metadata


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Проверяет значения и добавляет запись с новым ID."""
    schema = get_schema(metadata, table_name)
    columns = [name for name in schema if name != ID_COLUMN]
    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается значений: {len(columns)}, получено: {len(values)}."
        )
    fields = dict(zip(columns, values))
    validate_fields(schema, fields)
    table_data = load_table_data(table_name)
    new_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    table_data.append({ID_COLUMN: new_id, **fields})
    _select_cache.clear()
    return table_data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает выборку, используя кэш одинаковых запросов."""
    condition = {} if where_clause is None else where_clause
    key = (
        json.dumps(table_data, sort_keys=True),
        json.dumps(condition, sort_keys=True),
    )
    rows = _select_cache(
        key,
        lambda: [row.copy() for row in table_data if matches(row, condition)],
    )
    return [row.copy() for row in rows]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи, соответствующие условию."""
    if ID_COLUMN in set_clause:
        raise ValueError("Изменять ID нельзя.")
    for row in table_data:
        if matches(row, where_clause):
            row.update(set_clause)
    _select_cache.clear()
    return table_data


@handle_db_errors
@confirm_action(DELETE_ACTION)
def delete(table_data, where_clause):
    """Удаляет подходящие записи после подтверждения."""
    rows = [row for row in table_data if not matches(row, where_clause)]
    _select_cache.clear()
    return rows
