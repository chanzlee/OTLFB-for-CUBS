import collections
import logging
import random
import dateutil.parser

from datetime import timedelta
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from tlfb import tasks
from tlfb.data.models import RoughData
from tlfb.settings import USE_CELERY
from tlfb.encrypttest import encrip, decrip
from tlfb.forms import LoginForm, MarkerDateForm, TimeoutForm
from tlfb.encrypt_data import get_encrypted_session, get_decrypted_session
LOGGER = logging.getLogger(__name__)


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'
    success_url = reverse_lazy('step1')

    def form_valid(self, form):
        k = '9678365400123890'

        enc = self.request.GET.get('encrypted') or False
        offset = self.request.GET.get('offset') or 0
        days = self.request.GET.get('days') or 14

        if enc:
            subid = encrip(k, form.cleaned_data['subid_1'])
            timepoint = form.cleaned_data['timepoint_1']
        else:
            subid = form.cleaned_data['subid_1']
            timepoint = form.cleaned_data['timepoint_1']

        if offset:
            try:
                offset = int(float(offset))
            except:
                offset = 0

        if days:
            try:
                days = int(float(days))
            except:
                days = 14

        markers = {}
        for i in range(0, days):
            date = timezone.localdate(timezone.now()) - timedelta(days=(i + offset))
            markers[date.isoformat()] = {'markers': []}
        self.request.session['markers'] = markers

        study_cohort = self.request.GET.get('cohort') or ''
        activate_study_cannabis = self.request.GET.get('with_study_cbs') or False
        keep_prescription = self.request.GET.get('prescription') or True
        remove_label_study = self.request.GET.get('studyrm') or False

        random_submission_number = random.randint(1, 9999)
        today = timezone.localdate(timezone.now())

        self.request.session['subid'] = subid
        self.request.session['timepoint'] = timepoint
        self.request.session['pid'] = f"{subid}-{timepoint}-{today.isoformat()}-" \
                                      f"{str(random_submission_number).zfill(4)}"

        self.request.session['offset'] = offset
        self.request.session['cohort'] = study_cohort

        self.request.session['study_cannabis'] = True if activate_study_cannabis else False
        self.request.session['days'] = days
        self.request.session['prescription'] = keep_prescription
        self.request.session['study_removed'] = True if remove_label_study else False
        return super(LoginView, self).form_valid(form)


class MarkerDateView(FormView):
    form_class = MarkerDateForm
    template_name = 'step1_markerdates.html'

    def form_valid(self, form):
        if 'add' in form.data:
            markers = self.request.session.get('markers')
            date, event = form.get_marker()

            if not markers.get(date.isoformat()):
                # sometimes the JS widget lets you put in invalid info
                return HttpResponseRedirect(reverse('step1'))

            markers[date.isoformat()]['markers'].append(event)
            self.request.session['markers'] = markers
            return HttpResponseRedirect(reverse('step1'))

        elif 'done' in form.data:
            return HttpResponseRedirect(reverse('step2'))

    def get_context_data(self, **kwargs):
        markers = self.request.session.get('markers')

        # for the template, convert to python dates
        markers = {dateutil.parser.parse(k): v for k, v in markers.items()}
        kwargs['markers'] = collections.OrderedDict(sorted(markers.items()))

        kwargs['encrypted_session'] = get_encrypted_session(self.request.session)
        return super(MarkerDateView, self).get_context_data(**kwargs)


class CalendarView(TemplateView):
    template_name = 'step2_calendar.html'

    def get_context_data(self, **kwargs):
        markers = self.request.session.get('markers')
        kwargs['finished'] = True
        for date, data in self.request.session.get('markers').items():
            if not data.get('submitted'):
                kwargs['finished'] = False

        # for the template, convert to python dates
        markers = {dateutil.parser.parse(k): v for k, v in markers.items()}
        kwargs['markers'] = collections.OrderedDict(sorted(markers.items()))

        kwargs['encrypted_session'] = get_encrypted_session(self.request.session)
        return super(CalendarView, self).get_context_data(**kwargs)


class ThankYouView(TemplateView):
    template_name = 'step4_thankyou.html'

    def get(self, request, *args, **kwargs):
        subid = self.request.session.get('subid')
        timepoint = self.request.session.get('timepoint')
        encrypted_cohort = self.request.session.get('cohort')
        session_data = self.request.session.get('markers')
        pid = self.request.session.get("pid")

        # validate that all have been submitted
        for date, data in session_data.items():
            if not data.get('submitted'):
                messages.error(request, 'You must complete the form for each day on the calendar.')
                return HttpResponseRedirect(reverse('step2'))

        k = '9678365400123890'
        try:
            subid = decrip(k, subid)[0:4]
        except:
            logging.error(f"failed to decrypt {subid}")

        try:
            rd = RoughData.objects.create(subid=subid,
                                          timepoint=timepoint,
                                          cohort=encrypted_cohort,
                                          answers=session_data)

            rd.save()
        except:
            logging.error(f"subid: '{subid}'")
            logging.error(f"timepoint: '{timepoint}'")
            logging.error(f"encrypted_cohort: '{encrypted_cohort}'")
            logging.error(f"session_data: '{session_data}'")

        # TODO: uncomment this line if you are also running celery and uploading data somewhere.
        # attempt_export(self.request.session)

        return super(ThankYouView, self).get(request, *args, **kwargs)


class TimeoutView(FormView):
    form_class = TimeoutForm
    template_name = 'timeout.html'

    def form_valid(self, form):
        if 'restart' in form.data:
            return HttpResponseRedirect(reverse('login'))

        elif 'continue' in form.data:

            try:
                session_data = get_decrypted_session(form.cleaned_data["encrypted_session"])
                for key, value in session_data.items():
                    self.request.session[key] = value
                return HttpResponseRedirect(reverse('step1'))
            except:
                return HttpResponseRedirect(reverse('login'))


def attempt_export(session):
    try:
        if USE_CELERY:
            tasks.submit.delay(subid=session.get('subid'),
                               timepoint=session.get('timepoint'),
                               cohort=session.get('cohort'),
                               pid_number=session.get("pid"),
                               data=session.get('markers'))
        else:
            tasks.redcap_upload(subid=session.get('subid'),
                                timepoint=session.get('timepoint'),
                                cohort=session.get('cohort'),
                                pid_number=session.get("pid"),
                                data=session.get('markers'))
    except Exception as e:
        logging.error(e)
