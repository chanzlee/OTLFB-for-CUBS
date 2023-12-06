import os
import time
import celery

from tlfb.transform_helper import export_transformed_data, transform_data

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tlfb.settings')

app = celery.Celery('tlfb')
app.config_from_object('django.conf:settings')


@app.task
def submit(subid, timepoint, cohort, pid_number, data):
    redcap_upload(subid, timepoint, cohort, pid_number, data)


def redcap_upload(subid, timepoint, cohort, pid_number, data):
    output = transform_data(subid=subid,
                            timepoint=timepoint,
                            cohort=cohort,
                            pid_number=pid_number,
                            data=data)
    export_transformed_data(output)
