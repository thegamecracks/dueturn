from src import engine
from src import settings


def main():
    """Verify settings and run the battle engine's main loop."""
    settings.setup_configs()
    while True:
        engine.main()


if __name__ == '__main__':
    main()
