set -o errexit
uv sync
uv run python manage.py connect-static --no-input
uv run python manage.py migrate
