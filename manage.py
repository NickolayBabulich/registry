import os
import sys

import environ


def main():
    """Run administrative tasks."""
    env = environ.Env()
    env.read_env(os.path.join(os.path.dirname(__file__), f".env.{os.environ.get('DJANGO_ENV', 'dev')}"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", env("DJANGO_SETTINGS_MODULE"))
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?",
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
