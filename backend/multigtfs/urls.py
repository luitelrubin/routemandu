from django.urls import path
from multigtfs import views

urlpatterns = [
    path(
        "feed/",
        views.GTFSImportView.as_view(),
    )
]
