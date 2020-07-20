from src.engine import dueturn
from src import settings


def main():
    """Verify settings and run the battle engine's main loop."""
    settings.setup_configs()
    while True:
        dueturn.main()


if __name__ == '__main__':
    main()
