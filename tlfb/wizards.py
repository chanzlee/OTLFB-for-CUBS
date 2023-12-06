from collections import OrderedDict

import dateutil.parser
import six
from django.forms import Form, BaseFormSet
from django.http import HttpResponseRedirect
from django.urls import reverse
from formtools.wizard.views import SessionWizardView

from tlfb.forms import *

FORMS = [
    ('substance-drilldown', SubstanceDrilldownForm),

    # Alcohol and Subsections
    ('alcohol-drilldown', AlcoholDrilldownForm),
    ('beer-type', BeerDetailForm),
    ('wine-type', WineDetailForm),
    ('shots-type', ShotsDetailForm),
    ('otheralcohol-type', OtherAlcoholDetailForm),

    ('tobacco-drilldown', TobaccoDrilldownForm),
    ('cigarettes-type', CigarettesDetailForm),
    ('ecigs-type', ECigarettesDetailForm),
    ('chew-type', ChewDetailForm),
    ('cigars-type', CigarsDetailForm),
    ('hookah-type', HookahDetailForm),
    ('othertobacco-type', OtherTobaccoDetailForm),

    # Cannabis and Subsections
    ('cannabis-drilldown', CannabisDrilldownForm),

    # Study Cannabis and Subsections
    ('studycannabis-drilldown', StudyCannabisDrilldownForm),
    ('studycannabis-flower-type', StudyCannabisFlowerDetailForm),
    ('studycannabis-edible-type', StudyCannabisEdibleDetailForm),

    # Non-study Cannabis and Subsections
    ('nonstudycannabis-drilldown', NonStudyCannabisDrilldownForm),
    ('nonstudycannabis-flower-type', NonStudyCannabisFlowerDetailForm),
    ('nonstudycannabis-edible-type', NonStudyCannabisEdibleDetailForm),
    ('nonstudycannabis-concentrate-type', NonStudyCannabisConcentrateDetailForm),
    ('nonstudycannabis-other-type', NonStudyCannabisOtherDetailForm),

    # No Reference to study cannabis
    ('studyremovedcannabis-drilldown', StudyRemovedCannabisDrilldownForm),
    ('studyremovedcannabis-flower-type', StudyRemovedCannabisFlowerDetailForm),
    ('studyremovedcannabis-edible-type', StudyRemovedCannabisEdibleDetailForm),
    ('studyremovedcannabis-concentrate-type', StudyRemovedCannabisConcentrateDetailForm),
    ('studyremovedcannabis-other-type', StudyRemovedCannabisOtherDetailForm),

    # Normal Prescription Drugs and Subsections
    ('prescription-drilldown', PrescriptionDrilldownForm),
    ('opioids-type', OpioidsDetailForm),
    ('sleepmedication-type', SleepMedicationDetailForm),
    ('musclerelaxants-type', MuscleRelaxantsDetailForm),
    ('nonsteroidal-type', NonSteroidalAntiInflammatoryDrugsDetailForm),
    ('nervepain-type', NervePainMedicineDetailForm),
    ('adhd-type', AdhdMedicineDetailForm),
    ('othermedication-type', OtherMedicationDetailForm),

    ('methadone-type', MethadoneDetailForm),
    ('meperidine-type', MeperidineDetailForm),
    ('suboxone-type', SuboxoneDetailForm),
    ('codeine-type', CodeineDetailForm),
    ('fentanyl-type', FentanylDetailForm),
    ('oxymorphone-type', OxymorphoneDetailForm),
    ('morphine-type', MorphineDetailForm),
    ('hydrocodone-type', HydrocodoneDetailForm),
    ('oxycodone-type', OxycodoneDetailForm),
    ('hydrocodoneER-type', HydrocodoneERDetailForm),
    ('hydromorphone-type', HydromorphoneDetailForm),
    ('other-opiod-type', OtherOpiodDetailForm),

    ('methadone-medical-type', MedicalMethadoneDetailForm),
    ('meperidine-medical-type', MedicalMeperidineDetailForm),
    ('suboxone-medical-type', MedicalSuboxoneDetailForm),
    ('codeine-medical-type', MedicalCodeineDetailForm),
    ('fentanyl-medical-type', MedicalFentanylDetailForm),
    ('oxymorphone-medical-type', MedicalOxymorphoneDetailForm),
    ('morphine-medical-type', MedicalMorphineDetailForm),
    ('hydrocodone-medical-type', MedicalHydrocodoneDetailForm),
    ('oxycodone-medical-type', MedicalOxycodoneDetailForm),
    ('hydrocodoneER-medical-type', MedicalHydrocodoneERDetailForm),
    ('hydromorphone-medical-type', MedicalHydromorphoneDetailForm),
    ('other-medical-opiod-type', MedicalOtherOpiodDetailForm),


    ('sleepmedication-medical-type', MedicalSleepMedicationDetailForm),
    ('musclerelaxants-medical-type', MedicalMuscleRelaxantsDetailForm),
    ('nonsteroidal-medical-type', MedicalNonSteroidalAntiInflammatoryDrugsDetailForm),
    ('nervepain-medical-type', MedicalNervePainMedicineDetailForm),
    ('adhd-medical-type', MedicalAdhdMedicineDetailForm),
    ('othermedication-medical-type', MedicalOtherMedicationDetailForm),

    ('sleepmedication-recreational-type', RecreationalSleepMedicationDetailForm),
    ('musclerelaxants-recreational-type', RecreationalMuscleRelaxantsDetailForm),
    ('nonsteroidal-recreational-type', RecreationalNonSteroidalAntiInflammatoryDrugsDetailForm),
    ('nervepain-recreational-type', RecreationalNervePainMedicineDetailForm),
    ('adhd-recreational-type', RecreationalAdhdMedicineDetailForm),
    ('othermedication-recreational-type', RecreationalOtherMedicationDetailForm),

    # Other Drugs
    ('illegaldrugs-type', IllegalDrugsDetailForm),
    ('other-type', OtherDetailFormSet),
    ('none-type', NoneDetailForm),
]


class SubstanceWizard(SessionWizardView):
    form_list = FORMS

    def get(self, request, *args, **kwargs):
        if not request.GET.get('date'):
            return HttpResponseRedirect(reverse('step2'))
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        return ['step3_substanceform.html']

    def done(self, form_list, **kwargs):
        substances = {}
        data = self.request.session.get('markers')
        date = dateutil.parser.parse(self.request.GET.get('date')).date().isoformat()
        data[date]['submitted'] = True
        for form in form_list:
            if isinstance(form, DrilldownForm):  # skip drilldown forms
                continue
            if isinstance(form, Form):
                substances.update(form.get_nonzero_answers())
            if isinstance(form, BaseFormSet):
                for idx, f in enumerate(form.forms):
                    substances.update(f.get_nonzero_answers(idx=idx))
            data[date]['substances'] = substances
            self.request.session['markers'] = data
        return HttpResponseRedirect(reverse('step2'))

    def get_context_data(self, form, **kwargs):
        kwargs.update({'date': self.request.GET.get('date')})
        return super().get_context_data(form, **kwargs)

    def get_form_list(self):
        """
        Slight modification of superclass definition
        """
        form_list = OrderedDict()
        for form_key, form_class in six.iteritems(self.form_list):
            if form_class.show(self):
                form_list[form_key] = form_class
        return form_list

    def get_form_kwargs(self, step=None):
        if step == 'substance-drilldown':
            return {'prescription': self.request.session.get('prescription'),'prescription2': self.request.session.get('prescription2'),'study_removed': self.request.session.get('study_removed')}
        return super(SubstanceWizard, self).get_form_kwargs(step=step)
