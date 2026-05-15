from config import ENABLE_LOGGING


def log(message=""):

    if ENABLE_LOGGING:
        print(message)


def section(title):

    if ENABLE_LOGGING:

        print("\n" + "=" * 80)

        print(title)

        print("=" * 80)