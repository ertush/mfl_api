from __future__ import division

import reversion
import json
import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import encoding

from common.models import (
    AbstractBase, Ward, Contact, SequenceMixin, SubCounty, County,
    Town, ApiAuthentication
)
from common.fields import SequenceField
from .facility_models import Facility

LOGGER = logging.getLogger(__name__)



@reversion.register(follow=['parent'])
@encoding.python_2_unicode_compatible
class InfrastructureCategory(AbstractBase):

    """
    Categorization of health specilaists. e.g Anesthesiologist, Gastroentologist,
    Radiologists etc.
    """
    name = models.CharField(
        max_length=100,
        help_text="What is the name of the category? ")
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form of the category e.g ANC for antenatal')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        help_text='The parent category under which the category falls',
        related_name='sub_categories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def specialities_count(self):
        return len(self.category_services.all())

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'specialities categories'



@reversion.register(follow=['category'])
@encoding.python_2_unicode_compatible
class Infrastructure(SequenceMixin, AbstractBase):

    """
    Health specilities.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form for the infrastructure'
        )
    category = models.ForeignKey(
        InfrastructureCategory,
        on_delete=models.PROTECT,
        help_text="The classification that the specialities lies in.",
        related_name='category_infrastructure')
    code = SequenceField(unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(Infrastructure, self).save(*args, **kwargs)

    @property
    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'infrastructure'


@reversion.register(follow=['facility', 'infrastructure'])
@encoding.python_2_unicode_compatible
class FacilityInfrastructure(AbstractBase):

    """
    A facility can have zero or more infrastructure.
    """
    facility = models.ForeignKey(
        Facility, related_name='facility_infrastructure',
        on_delete=models.PROTECT)

    infrastructure = models.ForeignKey(
        Infrastructure, 
        on_delete=models.PROTECT,)

    present = models.BooleanField(
        default=False, 
        help_text='True if the listed infrastructure is present.')

    @property
    def speciality_name(self):
            return self.infrastructure.name

    def __str__(self):
        return "{}: {}".format(self.facility, self.infrastructure)

    def validate_unique_speciality(self):

        if len(self.__class__.objects.filter(
                infrastructure=self.infrastructure, facility=self.facility,
                deleted=False)) == 1 and not self.deleted:
            error = {
                "infrastructure": [
                    ("The infrastructure {} has already been added to the "
                     "facility").format(self.infrastructure.name)]
            }
            raise ValidationError(error)

    def clean(self, *args, **kwargs):
        self.validate_unique_speciality()
