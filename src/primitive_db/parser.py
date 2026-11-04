"""Разбор команд и значений простого языка базы данных."""

import shlex


def tokenize(text):
    """Разбивает строку, сохраняя кавычки у строковых значений."""
    lexer = shlex.shlex(text, posix=False, punctuation_chars="(),=")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = []
    for token in lexer:
        if all(character in "(),=" for character in token):
            tokens.extend(token)
        else:
            tokens.append(token)
    return tokens


def parse_value(token):
    """Преобразует отдельное значение в str, int или bool."""
    if len(token) >= 2 and token[0] in "\"'" and token[-1] == token[0]:
        return token[1:-1]
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits.isdecimal():
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки пишутся в кавычках.")


def parse_assignments(tokens, multiple=False):
    """Разбирает равенство или список присваиваний через запятую."""
    result = {}
    index = 0
    while index < len(tokens):
        if index + 2 >= len(tokens) or tokens[index + 1] != "=":
            raise ValueError("Ожидается условие вида столбец = значение.")
        column = tokens[index]
        if not column.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {column}.")
        if column in result:
            raise ValueError(f"Столбец {column} указан повторно.")
        result[column] = parse_value(tokens[index + 2])
        index += 3
        if index < len(tokens):
            if not multiple or tokens[index] != "," or index + 1 == len(tokens):
                raise ValueError("Присваивания в set разделяются запятыми.")
            index += 1
    if not result:
        raise ValueError("Условие не может быть пустым.")
    return result


def parse_where(text):
    """Возвращает словарь для одного условия равенства."""
    return parse_assignments(tokenize(text))


def parse_set(text):
    """Возвращает словарь новых значений для команды update."""
    return parse_assignments(tokenize(text), multiple=True)


def parse_values(text):
    """Разбирает значения insert, заключённые в круглые скобки."""
    tokens = tokenize(text)
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Значения после values нужно заключить в скобки.")
    values = []
    inner = tokens[1:-1]
    for index, token in enumerate(inner):
        if index % 2 == 0:
            values.append(parse_value(token))
        elif token != ",":
            raise ValueError("Значения insert разделяются запятыми.")
    if inner and len(inner) % 2 == 0:
        raise ValueError("После запятой ожидается значение.")
    return values


def check_table_name(name):
    """Проверяет, что имя таблицы является обычным идентификатором."""
    if not name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {name}.")
    return name


def find_where(tokens):
    """Находит разделитель where после присваиваний update."""
    for index in range(4, len(tokens)):
        if tokens[index].lower() == "where" and (
            index + 1 == len(tokens) or tokens[index + 1] != "="
        ):
            return index
    raise ValueError("Для update обязательно условие where.")


def parse_command(text):
    """Возвращает имя команды и её разобранные аргументы."""
    tokens = tokenize(text)
    if not tokens:
        raise ValueError("Команда не введена.")
    command = tokens[0].lower()
    if command in ("help", "exit", "list_tables"):
        if len(tokens) != 1:
            raise ValueError(f"Команда {command} не принимает аргументы.")
        return {"command": command}
    if command in ("drop_table", "info"):
        if len(tokens) != 2:
            raise ValueError(f"Используйте: {command} имя_таблицы.")
        return {"command": command, "table_name": check_table_name(tokens[1])}
    if command == "create_table":
        if len(tokens) < 3:
            raise ValueError("Используйте: create_table имя_таблицы столбец:тип ...")
        return {
            "command": command,
            "table_name": check_table_name(tokens[1]),
            "columns": tokens[2:],
        }
    if command == "insert":
        if len(tokens) < 6 or tokens[1].lower() != "into":
            raise ValueError("Используйте: insert into имя_таблицы values (...)")
        if tokens[3].lower() != "values":
            raise ValueError("В команде insert ожидается слово values.")
        return {
            "command": command,
            "table_name": check_table_name(tokens[2]),
            "values": parse_values(" ".join(tokens[4:])),
        }
    if command in ("select", "delete"):
        if len(tokens) < 3 or tokens[1].lower() != "from":
            raise ValueError(f"Используйте: {command} from имя_таблицы ...")
        where_clause = None
        if len(tokens) > 3:
            if tokens[3].lower() != "where":
                raise ValueError("После имени таблицы ожидается where.")
            where_clause = parse_assignments(tokens[4:])
        elif command == "delete":
            raise ValueError("Для delete обязательно условие where.")
        return {
            "command": command,
            "table_name": check_table_name(tokens[2]),
            "where_clause": where_clause,
        }
    if command == "update":
        if len(tokens) < 4 or tokens[2].lower() != "set":
            raise ValueError("Используйте: update имя_таблицы set ... where ...")
        where_index = find_where(tokens)
        return {
            "command": command,
            "table_name": check_table_name(tokens[1]),
            "set_clause": parse_assignments(tokens[3:where_index], multiple=True),
            "where_clause": parse_assignments(tokens[where_index + 1 :]),
        }
    return {"command": command}
