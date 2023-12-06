from django.contrib.postgres.fields import JSONField
from django.db import models
from django_extensions.db.models import TimeStampedModel


class RoughData(TimeStampedModel):
    # lastfive = models.CharField(max_length=255)
    # firstletter = models.CharField(max_length=255,default='')
    subid = models.CharField(max_length=225)
    timepoint = models.CharField(max_length=225)
    answers = JSONField()
    uploaded = models.BooleanField(default=False)
    cohort = models.CharField(max_length=100,default='')
