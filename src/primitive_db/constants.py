META_FILE = "db_meta.json"
DATA_DIR = "data"
ENCODING = "utf-8"
JSON_INDENT = 2
ID_COLUMN = "ID"
ID_DEFINITION = "ID:int"
VALID_TYPES = {"int": int, "str": str, "bool": bool}
DROP_ACTION = "удаление таблицы"
DELETE_ACTION = "удаление записей"

HELP_TEXT = """
Управление таблицами:
  create_table <таблица> <столбец:тип> ...
  list_tables
  drop_table <таблица>
  info <таблица>

Операции с данными:
  insert into <таблица> values (<значение>, ...)
  select from <таблица> [where <столбец> = <значение>]
  update <таблица> set <столбец> = <значение> where <столбец> = <значение>
  delete from <таблица> where <столбец> = <значение>

Типы столбцов: int, str, bool. ID добавляется автоматически.
Строки нужно заключать в кавычки, логические значения — true или false.
В set можно указать несколько присваиваний через запятую.
help — справка, exit — выход.
"""
