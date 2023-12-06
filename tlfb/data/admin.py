import logging
import time

from django.contrib import admin
from django.http import HttpResponse
from raven.contrib.django.raven_compat.models import client

from tlfb.data.models import RoughData
from tlfb.transform_helper import export_transformed_data, transform_data
from tlfb.encrypttest import decrip

LOGGER = logging.getLogger(__name__)


@admin.register(RoughData)
class RoughDataAdmin(admin.ModelAdmin):
    list_display = ('subid', 'created')
    actions = ['export_as_csv', 'resubmit_to_redcap']

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=export.csv'

        first = True
        for obj in queryset:
            if first:
                response.write(transform_data(subid=obj.subid, timepoint=obj.timepoint, cohort = obj.cohort, data=obj.answers))
                first = False
                continue
            response.writelines(transform_data(subid=obj.subid, timepoint=obj.timepoint, cohort = obj.cohort, data=obj.answers,
                                                         with_header=False))
        return response

    export_as_csv.short_description = "Export as Redcap-format CSV"

    def resubmit_to_storage(self, request, queryset):
        for obj in queryset:
            try:
                output = transform_data(subid=obj.subid,
                                                  timepoint=obj.timepoint,
                                                  cohort=obj.cohort,
                                                  data=obj.answers)
                uploaded = export_transformed_data(output)
                LOGGER.info("Uploaded id '{}' to storage. Success: {}".format(obj.subid, uploaded))
            except:
                LOGGER.error("Unable to upload id '{}' to storage.".format(obj.subid))
                client.captureException()

    resubmit_to_storage.short_description = "Resubmit to storage"
