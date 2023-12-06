from django.conf.urls import url
from django.contrib import admin
from django.urls import include

from tlfb.views import LoginView, MarkerDateView, CalendarView, ThankYouView, TimeoutView
from tlfb.wizards import SubstanceWizard

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', LoginView.as_view(), name='login'),
    url(r'^step1_daterange/$', MarkerDateView.as_view(), name='step1'),
    url(r'^step2_calendar/$', CalendarView.as_view(), name='step2'),
    url(r'^step3_substances/$', SubstanceWizard.as_view(), name='step3'),
    url(r'^step4_thankyou/$', ThankYouView.as_view(), name='step4'),
    url(r'^timeout/$', TimeoutView.as_view(), name='timeout'),

    url(r'^tz_detect/', include('tz_detect.urls')),
]
