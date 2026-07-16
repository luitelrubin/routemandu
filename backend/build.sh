set -o errexit
set -o pipefail
set -o xtrace
uv sync
uv run python manage.py connect-static --no-input
uv run python manage.py migrate
