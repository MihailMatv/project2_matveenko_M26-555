import time

import prompt


def _copy_metadata(wrapper, func):
    """Сохраняет имя и описание обёрнутой функции."""
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__wrapped__ = func
    return wrapper


def handle_db_errors(func):
    """Выводит ошибки базы данных без остановки приложения."""

    def wrapper(*args, **kwargs):
        """Перехватывает ошибки вызова."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")
        return None

    return _copy_metadata(wrapper, func)


def confirm_action(action_name):
    """Запрашивает подтверждение перед удалением данных."""

    def decorator(func):
        """Добавляет подтверждение к функции."""

        def wrapper(*args, **kwargs):
            """Выполняет действие только после ответа y."""
            question = f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            try:
                answer = prompt.string(question, empty=True) or ""
            except (EOFError, KeyboardInterrupt):
                print()
                answer = ""
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return _copy_metadata(wrapper, func)

    return decorator


def log_time(func):
    """Печатает время успешно выполненной операции."""

    def wrapper(*args, **kwargs):
        """Измеряет длительность вызова монотонными часами."""
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result

    return _copy_metadata(wrapper, func)


def create_cacher():
    """Создаёт независимый кэш результатов в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Возвращает сохранённый результат или вычисляет новый."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.clear = cache.clear
    return cache_result
