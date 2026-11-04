import prompt


def welcome():
    """Печатает доступные команды."""
    print("DB project is running!")
    print("help — справка, exit — выход")


def run():
    """Читает команды до выхода пользователя."""
    welcome()
    while True:
        try:
            command = prompt.string("Введите команду: ", empty=True).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if command == "exit":
            break
        if command == "help":
            welcome()
