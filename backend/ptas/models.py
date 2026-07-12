from django.db import models
from django.conf import settings


# Create your models here.
class PublicTransitAgency(models.Model):
    id = models.CharField(
        primary_key=True,
    )
    name = models.CharField(max_length=125, db_index=True, unique=True)
    color = models.CharField(
        max_length=7, help_text="Route shape color on map", unique=True
    )
    owner = models.OneToOneField(
        getattr(settings, "AUTH_USER_MODEL"),
        help_text="User who acts on behalf of this bus company",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name="pta",
    )
