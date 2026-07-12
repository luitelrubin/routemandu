from django.urls import path

from raptor.views import RaptorQueryView, StationSearchView

app_name = "raptor"

urlpatterns = [
    path("query/", RaptorQueryView.as_view(), name="query"),
    path("stations/", StationSearchView.as_view(), name="stations"),
]
