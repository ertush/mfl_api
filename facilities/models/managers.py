"""
Various managers to allow to easily filter the facilities
"""
from django.db import models


class CompleteFacilityFilter(models.Manager):
    """
    Filter only those facilities whose mandatory details have been filled in
    """

    def get_queryset(self):
        return super(
            CompleteFacilityFilter, self).get_queryset()
