set -o errexit
set -o pipefail
set -o xtrace
apt-get install gdal-bin libgdal-dev proj-bin proj-data
export GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
export PROJ_LIB=/usr/share/proj
uv sync
uv run python manage.py collectstatic --no-input
uv run python manage.py migrate
