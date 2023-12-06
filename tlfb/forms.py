import re

from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.forms import TextInput, formset_factory
from django.utils.safestring import mark_safe

from tlfb.templates.widgets import PhoneWidget


class LoginForm(forms.Form):
    subid_1 = forms.CharField(label='Enter subject id here')
    subid_2 = forms.CharField(label='Confirm subject id here')

    timepoint_1 = forms.CharField(label='Enter timepoint here')
    timepoint_2 = forms.CharField(label='Confirm timepoint here')

    def clean_subid_1(self):
        data = self.cleaned_data.get('subid_1')
        if len(data) != 4:
            raise ValidationError('Must provide 4 digit subject id')
        if not data.isdigit():
            raise ValidationError('Letters and special characters are not allowed')
        return data

    def clean_subid_2(self):
        data = self.cleaned_data.get('subid_2')
        if len(data) != 4:
            raise ValidationError('Must provide 4 digit subject id')
        if not data.isdigit():
            raise ValidationError('Letters and special characters are not allowed')
        if data != self.cleaned_data.get('subid_1'):
            raise ValidationError('Both inputs must match')
        return data

    def clean_timepoint_1(self):
        data = self.cleaned_data.get('timepoint_1')
        if len(data) != 3:
            raise ValidationError('Must provide 3 character timepoint')
        return data

    def clean_timepoint_2(self):
        data = self.cleaned_data.get('timepoint_2')
        if len(data) != 3:
            raise ValidationError('Must provide 3 character timepoint')
        if data != self.cleaned_data.get('timepoint_1'):
            raise ValidationError('Both inputs must match')
        return data


class MarkerDateForm(forms.Form):
    date = forms.DateField(
        label='Date of important or memorable event in the last 2 weeks',
        widget=DatePickerInput(
            options={
                "format": "MM/DD/YYYY",
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            }
        ), required=False)
    event_name = forms.CharField(required=False)

    def clean(self):
        if 'add' in self.data:
            if not self.cleaned_data.get('date'):
                msg = forms.ValidationError("Date is required to add an event")
                self.add_error('date', msg)
            if not self.cleaned_data.get('event_name'):
                msg = forms.ValidationError("A marker event must have a name")
                self.add_error('event_name', msg)

    def get_marker(self):
        return self.cleaned_data['date'], self.cleaned_data['event_name']


class TimeoutForm(forms.Form):
    encrypted_session = forms.CharField(label='encrypted_session', required=True,
                                        widget=forms.HiddenInput(attrs={"id": "encryptedSession"}))


# ##### ABSTRACT CLASSES AND HELPER FUNCTIONS #####
class DrilldownForm(forms.Form):
    show_condition_step = ''
    show_condition_field = ''

    def clean(self):
        checked = self.cleaned_data.get('types')
        if not checked:
            raise ValidationError('You must fill in at least one option')
        if len(checked) > 1 and 'none' in checked:
            raise ValidationError('Cannot check None and other entries')

    @classmethod
    def show(cls, wizard):
        data = wizard.get_cleaned_data_for_step(cls.show_condition_step) or {}
        show = cls.show_condition_field in data.get('types') if data else False
        if show:  # you have to crawl backwards too because drilldowns can be multilevel
            from tlfb.wizards import FORMS
            show &= [f[1] for f in FORMS if f[0] == cls.show_condition_step][0].show(wizard)
        return show


def make_choices(singular, plural, options=None):
    if not options:
        options = ['----', '1/2 or less', '1', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4', '4 1/2', '5', '6', '7',
                   '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20 or more']
    tuples = []
    for option in options:
        pluralize = plural if option not in ['1/4 or less', '3/4', '1/2', '1/2 or less', '1', '1 or less', '1.0'] else singular
        # Make these numeric
        value = '-8888' if option in ['----'] else option
        value = '-9999' if value in ['Unknown'] else value
        value = value.replace('1/2', '.5')
        value = value.replace('1/4', '.25')
        value = value.replace('3/4', '.75')
        value = value.replace('or more', '')
        value = value.replace('or less', '')
        value = value.replace(' ', '')
        value = re.sub("[\(\[].*?[\)\]]", "", value)
        tuples.append(
            (value, option + ' {}'.format(pluralize) if option != '----' else option)
        )
    return tuples


class SubstanceDetailForm(forms.Form):
    show_condition_step = ''
    show_condition_field = ''

    def get_nonzero_answers(self, idx=None):
        nonzero_answers = {}
        for field, value in self.cleaned_data.items():
            if value:
                key = field
                if idx:
                    key = key + str(idx)
                nonzero_answers[key] = {
                    'answer': value,
                    'label': self.fields[field].label
                }
                if hasattr(self.fields[field], 'choices'):
                    nonzero_answers[field]['answer_display'] = dict(self.fields[field].choices)[value]
        return nonzero_answers

    @classmethod
    def show(cls, wizard):
        data = wizard.get_cleaned_data_for_step(cls.show_condition_step) or {}
        show = cls.show_condition_field in data.get('types') if data else False
        if show:  # you have to crawl backwards too because drilldowns can be multilevel
            from tlfb.wizards import FORMS
            show &= [f[1] for f in FORMS if f[0] == cls.show_condition_step][0].show(wizard)
        return show


# ##### CONCRETE DRILLDOWN AND DETAIL FORMS #####
class SubstanceDrilldownForm(DrilldownForm):
    name = 'Were any substances used on this day? If so, please select all of the substances used. ' \
           'If no, please select None'
    OPTIONS = [
        ("alcohol", mark_safe("<b>Alcohol</b> (i.e cannabis infused alcohol, beer, wine, hard liquor, etc.)")),
        ("tobacco", mark_safe("<b>Tobacco</b> Tobacco (cigarettes, e-cigarettes, chew/dip,cigars, hookah, dokha, nicotine patch, etc.)")),
        ("cannabis", mark_safe("<b>Cannabis</b> Cannabis (i.e. medical AND recreational use of flower/bud, edibles, concentrates/dabs, topicals, etc.)")),
        ("cannabis-studyremoved", mark_safe("<b>Cannabis</b> Cannabis (i.e. medical AND recreational use of flower/bud, edibles, concentrates/dabs, topicals, etc.)")),
        ("prescription-drugs",
         mark_safe("<b>Prescription drugs for medical and recreational use</b> (i.e., opioids, anti-depressant,"
                   " ADHD medication, etc.)")),
        ("illegal-drugs", mark_safe("<b>Illegal recreational drugs</b> (i.e. cocaine, LSD, etc.)")),
        ("other", mark_safe("<b>Other</b> Other (i.e. recreational use of prescription drugs, salvia, kratom, synthetic cannabis (K2, spice), etc.)")),
        ("none", mark_safe("<b>None</b> (I did not use substances on this day)")),
    ]
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                      choices=OPTIONS)

    def __init__(self, *args, **kwargs):
        remove_prescription2 = kwargs.pop('prescription2')
        keep_prescription = kwargs.pop('prescription')
        remove_study = kwargs.pop('study_removed')

        super().__init__(*args, **kwargs)

        import copy
        temp_options = copy.deepcopy(self.OPTIONS)
        if remove_study:
            temp_options.remove(temp_options[2])
        else:
            temp_options.remove(temp_options[3])

        if not keep_prescription and remove_prescription2:
            temp_options.remove(temp_options[3])

        self.fields['types'].choices = temp_options

    @classmethod
    def show(cls, wizard):
        return True  # always show this one




class AlcoholDrilldownForm(DrilldownForm):
    name = 'What type of alcohol did you have?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'alcohol'
    OPTIONS = [
        ("beer", mark_safe("<b>Beer</b>")),
        ("wine", mark_safe("<b>Wine/Champagne</b>")),
        ("shots", mark_safe("<b>Hard liquor</b> (or mixed drinks)")),
        ("other", mark_safe("<b>Other alcohol</b> (include liqueur (e.g. schnapps), cannabis infused beer, cannabis infused hard liquor, etc)")),
    ]
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                      choices=OPTIONS)


class BeerDetailForm(SubstanceDetailForm):
    name = 'How many beers did you drink? (consider a 12 oz. can/bottle = 1 beer AND a 16 oz US pint = 1 1/2 beers)'
    show_condition_step = 'alcohol-drilldown'
    show_condition_field = 'beer'

    beer = forms.ChoiceField(
        label='Beer',
        choices=make_choices('beer', 'beers'),
        required=True)


class WineDetailForm(SubstanceDetailForm):
    name = "How many glasses of wine did you drink? (1 glass = 5 oz. = 1 standard drink)"
    show_condition_step = 'alcohol-drilldown'
    show_condition_field = 'wine'

    wine = forms.ChoiceField(
        label='Wine/Champagne',
        choices=make_choices('glass', 'glasses'),
        required=True)


class ShotsDetailForm(SubstanceDetailForm):
    name = 'How many shots (or mixed drinks) of hard liquor did you have? (consider 1 shot = 1.5 oz, ' \
           'drinks are usually more than 1 shot)'
    show_condition_step = 'alcohol-drilldown'
    show_condition_field = 'shots'

    shots = forms.ChoiceField(
        label='Hard liquor',
        choices=make_choices('shot', 'shots'),
        required=True)


class OtherAlcoholDetailForm(SubstanceDetailForm):
    name = 'Please answer the following questions about the other alcohol you drank'
    show_condition_step = 'alcohol-drilldown'
    show_condition_field = 'other'

    other_alcohol_name = forms.CharField(
        label='Other alcohol',
        help_text="Please fill in type (e.g., cannabis infused beer)",
        required=True)
    other_alcohol_quantity = forms.CharField(
        label='Other alcohol quantity',
        help_text="Please fill in the potency, content, or amount of what you used with units "
                  "(i.e., drinks, mg, grams, ml, %, etc.)",
        required=True)


class TobaccoDrilldownForm(DrilldownForm):
    name = 'What type of tobacco did you use?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'tobacco'

    OPTIONS = [
        ("cigarettes", mark_safe("<b>Cigarettes</b>")),
        ("ecigs", mark_safe("<b>E-Cigarettes</b>")),
        ("chew", mark_safe("<b>Chew/Dip</b>")),
        ("cigars", mark_safe("<b>Cigars</b>")),
        ("hookah", mark_safe("<b>Hookah</b>")),
        ("other", mark_safe("<b>Other tobacco</b> (include dokha, nicotine patch, etc)")),
    ]
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                      choices=OPTIONS)


class CigarettesDetailForm(SubstanceDetailForm):
    name = 'How many cigarettes did you smoke? (consider 20 cigs = 1 pack)'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'cigarettes'

    cigarettes = forms.ChoiceField(
        label="Cigarettes",
        help_text="",
        choices=make_choices('cigarette', 'cigarettes'),
        required=True)


class ECigarettesDetailForm(SubstanceDetailForm):
    name = 'How many times did you use your e-cigarette? (consider 1 e-cigarette use= ~10 minutes of' \
           ' smoking or 15 puffs)'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'ecigs'

    ecigs = forms.ChoiceField(
        label="E-Cigarettes",
        choices=make_choices('e-cigarette', 'e-cigarettes', ['----', '1/4 or less', '1/2', '3/4', '1', '1 1/2', '2',
                                                             '2 1/2', '3', '3 1/2', '4', '4 1/2', '5', '6', '7', '8',
                                                             '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
                                                             '19', '20 or more']),
        required=True)


class ChewDetailForm(SubstanceDetailForm):
    name = 'How many times did you chew? (consider number of pinches or dips)'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'chew'
    chew = forms.ChoiceField(
        label="Chew/Dip",
        choices=make_choices('pinch/dip', 'pinches/dips'),
        required=True)


class CigarsDetailForm(SubstanceDetailForm):
    name = 'How many cigars did you smoke?'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'cigars'
    cigars = forms.ChoiceField(
        label="Cigars",
        choices=make_choices('cigar', 'cigars', ['----', '1/4 or less', '1/2', '3/4', '1', '1 1/2', '2', '2 1/2', '3',
                                                 '3 1/2', '4', '4 1/2', '5', '6', '7', '8', '9',
                                                 '10 or more']),
        required=True)


class HookahDetailForm(SubstanceDetailForm):
    name = 'How many hookah drags/puffs did you have?'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'hookah'
    hookah = forms.ChoiceField(
        label="Hookah",
        choices=make_choices('drag/puff', 'drags/puffs',
                             ['----', '1/2 or less', '1', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4', '4 1/2'] +
                             [str(x) for x in range(5, 21)] + [str(x) for x in range(30, 80, 10)] + ['80 or more']),
        required=True)


class OtherTobaccoDetailForm(SubstanceDetailForm):
    name = 'Please answer the following questions about the other tobacco you used'
    show_condition_step = 'tobacco-drilldown'
    show_condition_field = 'other'
    other_tobacco_name = forms.CharField(
        label="Other form of tobacco",
        help_text="Please fill in type (e.g. dokha)",
        required=True)
    other_tobacco_quantity = forms.CharField(
        label="Amount of other tobacco",
        help_text="please fill in the potency, content, or amount of what you used with units "
                  "(i.e., mg, grams, ml, %, etc.)",
        required=True)


class CannabisDrilldownForm(DrilldownForm):
    name = 'What type of cannabis product did you use?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'cannabis'

    OPTIONS = [
        ("cannabis-study", mark_safe("<b>Cannabis</b> (Study Product)")),
        ("cannabis-non-study", mark_safe("<b>Cannabis</b> (Non-study Product)")),
    ]
    types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=OPTIONS
    )

    @classmethod
    def show(cls, wizard):
        # special impl because of the potential to use the GET param to enable/disable study options
        data = wizard.get_cleaned_data_for_step('substance-drilldown') or {}
        if wizard.request.session.get('study_cannabis'):
            return 'cannabis' in data.get('types') if data else False
        return False


class StudyCannabisDrilldownForm(DrilldownForm):
    name = 'What type of study cannabis product did you use?'
    show_condition_step = 'cannabis-drilldown'
    show_condition_field = 'cannabis-study'

    OPTIONS = [
        ("flower", mark_safe("<b>Study Cannabis Flower/Bud</b><br />"
                             "Includes using a pipe, bong, bubbler, joint, blunt, spliff, vaporizer, "
                             "etc."
                             )),
        ("edible", mark_safe("<b>Study Cannabis Edible/Ingested</b><br />"
                             "Includes eating a piece of chocolate bar, gummy, baked good, capsule, tincture, etc."
                             )),
    ]
    types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=OPTIONS
    )


class StudyCannabisFlowerDetailForm(SubstanceDetailForm):
    name = 'Study Cannabis - Flower'
    show_condition_step = 'studycannabis-drilldown'
    show_condition_field = 'flower'

    study_cannabis_flower_total_grams = forms.ChoiceField(
        label="Flower/bud amount",
        help_text=mark_safe("How many total grams of cannabis did you use (e.g., smoked)?\n"
                            "See <a href='https://s3.us-east-2.amazonaws.com/tbtllc-tlfb/Cannabis+Visual.pdf' "
                            "target='_blank'>this document</a> for help estimating."),
        choices=make_choices('gram', 'grams',
                             ['----', '0.05 or less', '0.10', '0.15', '0.20', '0.25 (1/4 gram)', '0.30',
                              '0.35', '0.40', '0.45', '0.50 (1/2 gram)', '0.55', '0.60', '0.65',
                              '0.70', '0.75 (3/4 gram)', '0.80', '0.85', '0.90', '0.95', '1.0', '1.1',
                              '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '2.0', '2.1',
                              '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '3.0', '3.1',
                              '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '4.0', '4.1',
                              '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9', '5', '6', '7',
                              '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                              '20 or more']),
        required=True)


class StudyCannabisEdibleDetailForm(SubstanceDetailForm):
    name = 'Study Cannabis - Edible/Ingested'
    show_condition_step = 'studycannabis-drilldown'
    show_condition_field = 'edible'

    study_cannabis_edible_thc = forms.ChoiceField(
        label="Edible/ingested THC",
        help_text="How many total THC milligrams (best guess) did you use consume (e.g., eat)?",
        choices=make_choices('mg THC', 'mg THC',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)
    study_cannabis_edible_cbd = forms.ChoiceField(
        label="Edible/ingested CBD",
        help_text="How many total CBD milligrams (best guess) did you use consume (e.g., eat)?:",
        choices=make_choices('mg CBD', 'mg CBD',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)


class NonStudyCannabisDrilldownForm(DrilldownForm):
    name = 'What type of non-study cannabis product did you use?'

    OPTIONS = [
        ("flower", mark_safe("<b>Non-study Cannabis Flower/Bud</b><br />"
                             "Includes using a pipe, bong, bubbler, joint, blunt, spliff, vaporizer, "
                             "etc."
                             )),
        ("edible", mark_safe("<b>Non-study Cannabis Edible/Ingested</b><br />"
                             "Includes eating a piece of chocolate bar, gummy, baked good, capsule, tincture, etc."
                             )),
        ("concentrate", mark_safe("<b>Non-study Cannabis Concentrate</b><br />"
                                  "Includes shatter, wax, vape pen cartridges, disposable vape pen, etc.")),
        ("other", mark_safe("<b>Other Non-study Cannabis</b><br />"
                            "Includes topical creams, topical body oils, transdermal patches, vaginal suppositories, personal lubricant, bath bombs, etc.")),
    ]
    types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=OPTIONS
    )

    @classmethod
    def show(cls, wizard):
        # special impl because of the potential to use the GET param to enable/disable study options
        if wizard.request.session.get('study_cannabis'):
            data = wizard.get_cleaned_data_for_step('cannabis-drilldown') or {}
            return 'cannabis-non-study' in data.get('types') if data else False
        else:
            data = wizard.get_cleaned_data_for_step('substance-drilldown') or {}
            return 'cannabis' in data.get('types') if data else False


class NonStudyCannabisFlowerDetailForm(SubstanceDetailForm):
    name = 'Non-study Cannabis - Flower'
    show_condition_step = 'nonstudycannabis-drilldown'
    show_condition_field = 'flower'

    non_study_cannabis_flower_total_grams = forms.ChoiceField(
        label="Flower/bud amount",
        help_text=mark_safe("How many total grams of cannabis did you use (e.g., smoked)?\n"
                            "See <a href='https://s3.us-east-2.amazonaws.com/tbtllc-tlfb/Cannabis+Visual.pdf' "
                            "target='_blank'>this document</a> for help estimating."),
        choices=make_choices('gram', 'grams',
                             ['----', '0.05 or less', '0.10', '0.15', '0.20', '0.25 (1/4 gram)', '0.30',
                              '0.35', '0.40', '0.45', '0.50 (1/2 gram)', '0.55', '0.60', '0.65',
                              '0.70', '0.75 (3/4 gram)', '0.80', '0.85', '0.90', '0.95', '1.0', '1.1',
                              '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '2.0', '2.1',
                              '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '3.0', '3.1',
                              '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '4.0', '4.1',
                              '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9', '5', '6', '7',
                              '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                              '20 or more']),
        required=True)
    non_study_cannabis_flower_or_bud_thc = forms.ChoiceField(
        label="Flower/bud THC",
        help_text="What was the flower THC potency (best guess, %, 0-35)",
        choices=make_choices('% THC', '% THC',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '4', '5', '6', '7', '8',
                              '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35 or more']),
        required=True)
    non_study_cannabis_flower_or_bud_cbd = forms.ChoiceField(
        label="Flower/bud CBD",
        help_text="What was the flower CBD potency (best guess, %, 0-35)",
        choices=make_choices('% CBD', '% CBD',
                             ['----', 'Unknown', '1 or less', '1', '2', '3', '4', '5', '6', '7', '8',
                              '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35 or more']),
        required=True)


class NonStudyCannabisEdibleDetailForm(SubstanceDetailForm):
    name = 'Non-study Cannabis - Edible/Ingested'
    show_condition_step = 'nonstudycannabis-drilldown'
    show_condition_field = 'edible'

    non_study_cannabis_edible_thc = forms.ChoiceField(
        label="Edible/ingested THC",
        help_text="How many total THC milligrams (best guess) did you use consume (e.g., eat)?",
        choices=make_choices('mg THC', 'mg THC',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)
    non_study_cannabis_edible_cbd = forms.ChoiceField(
        label="Edible/ingested CBD",
        help_text="How many total CBD milligrams (best guess) did you use consume (e.g., eat)?:",
        choices=make_choices('mg CBD', 'mg CBD',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)


class NonStudyCannabisConcentrateDetailForm(SubstanceDetailForm):
    name = 'Non-study Cannabis - Concentrate'
    show_condition_step = 'nonstudycannabis-drilldown'
    show_condition_field = 'concentrate'

    non_study_cannabis_concentrate = forms.ChoiceField(
        label="Cannabis concentrate",
        help_text="How many dabs/drags/hits did you do?",
        choices=make_choices('dab/drag/hit', 'dabs/drags/hits', ['----', '1 or less', '2', '3', '4', '5', '6', '7', '8',
                                                                 '9', '10', '11', '12', '13', '14', '15', '16', '17',
                                                                 '18', '19', '20', '25', '30', '35', '40 or more']),
        required=True)
    non_study_cannabis_concentrate_thc = forms.ChoiceField(
        label="Cannabis concentrate THC",
        help_text="What was the concentrate THC potency (best guess, %, 0-100)?",
        choices=make_choices('% THC', '% THC',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                              '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35',
                              '40', '45', '50', '55', '60', '65', '70', '75', '80', '85', '90',
                              '95 or more']),
        required=True)
    non_study_cannabis_concentrate_cbd = forms.ChoiceField(
        label="Cannabis concentrate CBD",
        help_text="What was the concentrate CBD potency (best guess, %, 0-100)",
        choices=make_choices('% CBD', '% CBD',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                              '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35',
                              '40', '45', '50', '55', '60', '65', '70', '75', '80', '85', '90',
                              '95 or more']),
        required=True)


class NonStudyCannabisOtherDetailForm(SubstanceDetailForm):
    name = 'Non-study Cannabis - Other'
    show_condition_step = 'nonstudycannabis-drilldown'
    show_condition_field = 'other'

    non_study_cannabis_topical_patch = forms.ChoiceField(
        label="Non-study cannabis topical/patch",
        help_text="“Includes topical creams, topical body oils, transdermal patches, bath bombs, etc.”",
        choices=[
            ('', 'No'),
            ('Yes', 'Yes'),
        ],
        required=False
    )
    non_study_other_cannabis_name = forms.CharField(
        label='Other non-study cannabis name',
        help_text="Please fill in type of cannabis used. Include vaginal suppositories, personal lubricant, etc.",
        required=False)

    def clean(self):
        if not (self.cleaned_data['non_study_cannabis_topical_patch'] or
                self.cleaned_data['non_study_other_cannabis_name']):
            msg = forms.ValidationError("You must pick one of the options")
            self.add_error(None, msg)


class StudyRemovedCannabisDrilldownForm(DrilldownForm):
    name = 'What type of cannabis product did you use?'

    OPTIONS = [
        ("flower", mark_safe("<b>Cannabis Flower/Bud</b><br />"
                             "Includes using a pipe, bong, bubbler, joint, blunt, spliff, vaporizer, "
                             "etc."
                             )),
        ("edible", mark_safe("<b>Cannabis Edible/Ingested</b><br />"
                             "Includes eating a piece of chocolate bar, gummy, baked good, capsule, tincture, etc."
                             )),
        ("concentrate", mark_safe("<b>Cannabis Concentrate</b><br />"
                                  "Includes shatter, wax, vape pen cartridges, disposable vape pen, etc.")),
        ("other", mark_safe("<b>Other Cannabis</b><br />"
                            "Includes topical creams, topical body oils, transdermal patches, vaginal suppositories, personal lubricant, bath bombs, etc.")),
    ]
    types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=OPTIONS
    )

    @classmethod
    def show(cls, wizard):
        # special impl because of the potential to use the GET param to enable/disable study options
        if wizard.request.session.get('study_removed'):
            data = wizard.get_cleaned_data_for_step('substance-drilldown') or {}
            return 'cannabis-studyremoved' in data.get('types') if data else False

class StudyRemovedCannabisFlowerDetailForm(SubstanceDetailForm):
    name = 'Cannabis - Flower'
    show_condition_step = 'studyremovedcannabis-drilldown'
    show_condition_field = 'flower'

    non_study_cannabis_flower_total_grams = forms.ChoiceField(
        label="Flower/bud amount",
        help_text=mark_safe("How many total grams of cannabis did you use (e.g., smoked)?\n"
                            "See <a href='https://s3.us-east-2.amazonaws.com/tbtllc-tlfb/Cannabis+Visual.pdf' "
                            "target='_blank'>this document</a> for help estimating."),
        choices=make_choices('gram', 'grams',
                             ['----', '0.05 or less', '0.10', '0.15', '0.20', '0.25 (1/4 gram)', '0.30',
                              '0.35', '0.40', '0.45', '0.50 (1/2 gram)', '0.55', '0.60', '0.65',
                              '0.70', '0.75 (3/4 gram)', '0.80', '0.85', '0.90', '0.95', '1.0', '1.1',
                              '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '2.0', '2.1',
                              '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '3.0', '3.1',
                              '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '4.0', '4.1',
                              '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9', '5', '6', '7',
                              '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                              '20 or more']),
        required=True)
    non_study_cannabis_flower_or_bud_thc = forms.ChoiceField(
        label="Flower/bud THC",
        help_text="What was the flower THC potency (best guess, %, 0-35)",
        choices=make_choices('% THC', '% THC',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '4', '5', '6', '7', '8',
                              '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35 or more']),
        required=True)
    non_study_cannabis_flower_or_bud_cbd = forms.ChoiceField(
        label="Flower/bud CBD",
        help_text="What was the flower CBD potency (best guess, %, 0-35)",
        choices=make_choices('% CBD', '% CBD',
                             ['----', 'Unknown', '1 or less', '1', '2', '3', '4', '5', '6', '7', '8',
                              '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35 or more']),
        required=True)

class StudyRemovedCannabisEdibleDetailForm(SubstanceDetailForm):
    name = 'Cannabis - Edible/Ingested'
    show_condition_step = 'studyremovedcannabis-drilldown'
    show_condition_field = 'edible'

    non_study_cannabis_edible_thc = forms.ChoiceField(
        label="Edible/ingested THC",
        help_text="How many total THC milligrams (best guess) did you use consume (e.g., eat)?",
        choices=make_choices('mg THC', 'mg THC',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)
    non_study_cannabis_edible_cbd = forms.ChoiceField(
        label="Edible/ingested CBD",
        help_text="How many total CBD milligrams (best guess) did you use consume (e.g., eat)?:",
        choices=make_choices('mg CBD', 'mg CBD',
                             ['----', 'Unknown', '1 or less', '1 1/2', '2', '2 1/2', '3', '3 1/2', '4',
                              '4 1/2', '5', '6', '7', '8', '9', '10', '15', '20', '25',
                              '30', '35', '40', '45', '50', '60', '70', '80', '90', '100',
                              '125', '150', '175', '200 or more']),
        required=True)





class StudyRemovedCannabisConcentrateDetailForm(SubstanceDetailForm):
    name = 'Cannabis - Concentrate'
    show_condition_step = 'studyremovedcannabis-drilldown'
    show_condition_field = 'concentrate'

    non_study_cannabis_concentrate = forms.ChoiceField(
        label="Cannabis concentrate",
        help_text="How many dabs/drags/hits did you do?",
        choices=make_choices('dab/drag/hit', 'dabs/drags/hits', ['----', '1 or less', '2', '3', '4', '5', '6', '7', '8',
                                                                 '9', '10', '11', '12', '13', '14', '15', '16', '17',
                                                                 '18', '19', '20', '25', '30', '35', '40 or more']),
        required=True)
    non_study_cannabis_concentrate_thc = forms.ChoiceField(
        label="Cannabis concentrate THC",
        help_text="What was the concentrate THC potency (best guess, %, 0-100)?",
        choices=make_choices('% THC', '% THC',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                              '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35',
                              '40', '45', '50', '55', '60', '65', '70', '75', '80', '85', '90',
                              '95 or more']),
        required=True)
    non_study_cannabis_concentrate_cbd = forms.ChoiceField(
        label="Cannabis concentrate CBD",
        help_text="What was the concentrate CBD potency (best guess, %, 0-100)",
        choices=make_choices('% CBD', '% CBD',
                             ['----', 'Unknown', '1 or less', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                              '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
                              '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35',
                              '40', '45', '50', '55', '60', '65', '70', '75', '80', '85', '90',
                              '95 or more']),
        required=True)


class StudyRemovedCannabisOtherDetailForm(SubstanceDetailForm):
    name = 'Cannabis - Other'
    show_condition_step = 'studyremovedcannabis-drilldown'
    show_condition_field = 'other'

    non_study_cannabis_topical_patch = forms.ChoiceField(
        label="Cannabis topical/patch",
        help_text="“Includes topical creams, topical body oils, transdermal patches, bath bombs, etc.”",
        choices=[
            ('', 'No'),
            ('Yes', 'Yes'),
        ],
        required=False
    )
    non_study_other_cannabis_name = forms.CharField(
        label='Other cannabis name',
        help_text="Please fill in type of cannabis used. Include vaginal suppositories, personal lubricant, etc.",
        required=False)

    def clean(self):
        if not (self.cleaned_data['non_study_cannabis_topical_patch'] or
                self.cleaned_data['non_study_other_cannabis_name']):
            msg = forms.ValidationError("You must pick one of the options")
            self.add_error(None, msg)




class PrescriptionDrilldownForm(DrilldownForm):
    name = 'What type of prescription drugs did you use (for medical OR recreational purposes)?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'prescription-drugs'

    OPTIONS = [
        ("opioids", mark_safe("<b>Opioids</b> - Includes: <ul>"
                              "<li>Codeine, Tramadol (e.g., ConZip)</li>"
                              "<li>Fentanyl (e.g., Duragesic, Fentora, Actiq)</li>"
                              "<li>Oxymorphone (Opana)</li>"
                              "<li>Morphine (Avinza, Duramorph)</li>"
                              "<li>Hydrocodone (Vicodin, Lortab)</li>"
                              "<li>Hydrocodone Extended Release (Hysingla ER, Zohydro ER)</li>"
                              "<li>Oxycodone (Percocet, OxyContin)</li>"
                              "<li>Hydromorphone (Dilaudid)</li>"
                              "</ul>"
                              )),
        ("sleepmedication", mark_safe("<b>Sleep Medication</b> - Includes: <ul>"
                                      "<li>Eszopiclone (Lunesta and generic)</li>"
                                      "<li>Ramelteon (Rozerem and generic)</li>"
                                      "<li>Zaleplon (Sonata and generic)</li>"
                                      "<li>Zolpidem (Ambien, Ambien CR, Edluar, ZolpiMist, and generic)</li>"
                                      "</ul>"
                                      )),
        ("musclerelaxants", mark_safe("<b>Muscle Relaxants</b> - Includes: <ul>"
                                      "<li>Methocarbamol (Robaxin)</li>"
                                      "<li>Carisoprodol (Soma)</li>"
                                      "<li>Cyclobenzaprine (Amrix, Fexmid)</li>"
                                      "</ul>"
                                      )),
        ("nonsteroidal", mark_safe("<b>Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)</b> - Includes: <ul>"
                                   "<li>Celecoxib (Celebrex)</li>"
                                   "<li>Diclofenac (Voltaren)</li>"
                                   "</ul>"
                                   )),
        ("nervepain", mark_safe("<b>Nerve Pain Medication</b> - Includes: <ul>"
                                "<li>Cyclobenzaprine (Flexeril, Amrix, Fexmid)</li>"
                                "<li>Gabapentin (Neurontin, Gralise, Horizant)</li>"
                                "<li>Duloxetine (Cymbalta, Irenka)</li>"
                                "<li>Pregabalin (Lyrica)</li>"
                                "<li>Milnacipran (Savella)</li>"
                                "</ul>"
                                )),
        ("adhd", mark_safe("<b>ADHD Medication</b> - Includes: Adderall, Ritalin, etc.")),
        ("other", mark_safe("<b>Other Medication</b> - Includes: Suboxone, etc.")),
    ]
    types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=OPTIONS
    )


class OpioidsDetailForm(SubstanceDetailForm):
    name = 'Opioids'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'opioids'

    opioids = forms.ChoiceField(
        label="Opioids",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    opioid_dosage = forms.CharField(
        label="Opioid Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MethadoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Methadone'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'methadone'

    methadone = forms.ChoiceField(
        label="Methadone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    methadone_dosage = forms.CharField(
        label="Methadone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MeperidineDetailForm(SubstanceDetailForm):
    name = 'Recreational Meperidine (Demerol)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'meperidine'

    meperidine = forms.ChoiceField(
        label="Meperidine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    meperidine_dosage = forms.CharField(
        label="Meperidine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class SuboxoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Suboxone'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'suboxone'

    suboxone = forms.ChoiceField(
        label="Suboxone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    suboxone_dosage = forms.CharField(
        label="Suboxone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class CodeineDetailForm(SubstanceDetailForm):
    name = 'Recreational Codeine, Tramadol (e.g., ConZip)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'codeine'

    codeine = forms.ChoiceField(
        label="Codeine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    codeine_dosage = forms.CharField(
        label="Codeine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class FentanylDetailForm(SubstanceDetailForm):
    name = 'Recreational Fentanyl (e.g., Duragesic, Fentora, Actiq)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'fentanyl'

    fentanyl = forms.ChoiceField(
        label="Fentanyl",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    fentanyl_dosage = forms.CharField(
        label="Fentanyl Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class OxymorphoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Oxymorphone (Opana)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'oxymorphone'

    oxymorphone = forms.ChoiceField(
        label="Oxymorphone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    oxymorphone_dosage = forms.CharField(
        label="Oxymorphone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MorphineDetailForm(SubstanceDetailForm):
    name = 'Recreational Morphine (Avinza, Duramorph)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'morphine'

    morphine = forms.ChoiceField(
        label="Morphine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    morphine_dosage = forms.CharField(
        label="Morphine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class HydrocodoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Hydrocodone (Vicodin, Lortab)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'hydrocodone'

    hydrocodone = forms.ChoiceField(
        label="Hydrocodone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydrocodone_dosage = forms.CharField(
        label="Hydrocodone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class OxycodoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Oxycodone (Percocet, OxyContin)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'oxycodone'

    oxycodone = forms.ChoiceField(
        label="Oxycodone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    oxycodone_dosage = forms.CharField(
        label="Oxycodone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class HydrocodoneERDetailForm(SubstanceDetailForm):
    name = 'Recreational Hydrocodone Extended Release (Hysingla ER, Zohydro ER)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'hydrocodoneER'

    hydrocodoneER = forms.ChoiceField(
        label="Hydrocodone ER",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydrocodoneER_dosage = forms.CharField(
        label="Hydrocodone ER Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class HydromorphoneDetailForm(SubstanceDetailForm):
    name = 'Recreational Hydromorphone (Dilaudid)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'hydromorphone'

    hydromorphone = forms.ChoiceField(
        label="Hydromorphone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydromorphone_dosage = forms.CharField(
        label="Hydromorphone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class OtherOpiodDetailForm(SubstanceDetailForm):
    name = 'What type of other opioids did you use recreationally?'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'other-opiod'

    other_opiod = forms.CharField(
        label='Other Opioid Names',
        help_text="Please fill in name/type of other opioid and how much of this substance was used (please include amount of pills and dosage)",
        required=True)


class MedicalMethadoneDetailForm(SubstanceDetailForm):
    name = 'Medical Methadone'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'methadone-medical'

    methadone_medical = forms.ChoiceField(
        label="Methadone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    methadone_medical_dosage = forms.CharField(
        label="Methadone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalMeperidineDetailForm(SubstanceDetailForm):
    name = 'Medical Meperidine (Demerol)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'meperidine-medical'

    meperidine_medical = forms.ChoiceField(
        label="Meperidine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    meperidine_medical_dosage = forms.CharField(
        label="Meperidine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalSuboxoneDetailForm(SubstanceDetailForm):
    name = 'Medical Suboxone'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'suboxone-medical'

    suboxone_medical = forms.ChoiceField(
        label="Suboxone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    suboxone_medical_dosage = forms.CharField(
        label="Suboxone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalCodeineDetailForm(SubstanceDetailForm):
    name = 'Medical Codeine, Tramadol (e.g., ConZip)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'codeine-medical'

    codeine_medical = forms.ChoiceField(
        label="Codeine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    codeine_medical_dosage = forms.CharField(
        label="Codeine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalFentanylDetailForm(SubstanceDetailForm):
    name = 'Medical Fentanyl (e.g., Duragesic, Fentora, Actiq)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'fentanyl-medical'

    fentanyl_medical = forms.ChoiceField(
        label="Fentanyl",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    fentanyl_medical_dosage = forms.CharField(
        label="Fentanyl Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalOxymorphoneDetailForm(SubstanceDetailForm):
    name = 'Medical Oxymorphone (Opana)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'oxymorphone-medical'

    oxymorphone_medical = forms.ChoiceField(
        label="Oxymorphone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    oxymorphone_medical_dosage = forms.CharField(
        label="Oxymorphone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalMorphineDetailForm(SubstanceDetailForm):
    name = 'Medical Morphine (Avinza, Duramorph)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'morphine-medical'

    morphine_medical = forms.ChoiceField(
        label="Morphine",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    morphine_medical_dosage = forms.CharField(
        label="Morphine Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalHydrocodoneDetailForm(SubstanceDetailForm):
    name = 'Medical Hydrocodone (Vicodin, Lortab)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'hydrocodone-medical'

    hydrocodone_medical = forms.ChoiceField(
        label="Hydrocodone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydrocodone_medical_dosage = forms.CharField(
        label="Hydrocodone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalOxycodoneDetailForm(SubstanceDetailForm):
    name = 'Medical Oxycodone (Percocet, OxyContin)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'oxycodone-medical'

    oxycodone_medical = forms.ChoiceField(
        label="Oxycodone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    oxycodone_medical_dosage = forms.CharField(
        label="Oxycodone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalHydrocodoneERDetailForm(SubstanceDetailForm):
    name = 'Medical Hydrocodone Extended Release (Hysingla ER, Zohydro ER)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'hydrocodoneER-medical'

    hydrocodoneER_medical = forms.ChoiceField(
        label="Hydrocodone ER",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydrocodoneER_medical_dosage = forms.CharField(
        label="Hydrocodone ER Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalHydromorphoneDetailForm(SubstanceDetailForm):
    name = 'Medical Hydromorphone (Dilaudid)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'hydromorphone-medical'

    hydromorphone_medical = forms.ChoiceField(
        label="Hydromorphone",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    hydromorphone_medical_dosage = forms.CharField(
        label="Hydromorphone Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalOtherOpiodDetailForm(SubstanceDetailForm):
    name = 'What type of other opioids did you use for medical reasons?'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'other-opiod-medical'

    other_opiod_medical_name = forms.CharField(
        label='Other Opioid Names',
        help_text="Please fill in name/type of other opioid and how much of this substance was used (please include amount of pills and dosage)",
        required=True)
    # other_opiod_medical = forms.ChoiceField(
    #     label="Other Opioid Quantity",
    #     help_text="How many prescription pills/tablets did you use (total number of pills)?",
    #     choices=make_choices('pill', 'pills'),
    #     required=True)
    # other_opiod_medical_dosage = forms.CharField(
    #     label="Other Opioid Dosage",
    #     widget=TextInput(attrs={'placeholder': 'mg'}),
    #     help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
    #               "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
    #     required=True)


class SleepMedicationDetailForm(SubstanceDetailForm):
    name = 'Sleep Medication'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'sleepmedication'

    sleep_medication = forms.ChoiceField(
        label="Sleep Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    sleep_medication_dosage = forms.CharField(
        label="Sleep Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MuscleRelaxantsDetailForm(SubstanceDetailForm):
    name = 'Muscle Relaxants'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'musclerelaxants'

    muscle_relaxants = forms.ChoiceField(
        label="Muscle Relaxants",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    muscle_relaxants_dosage = forms.CharField(
        label="Muscle Relaxants Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class NonSteroidalAntiInflammatoryDrugsDetailForm(SubstanceDetailForm):
    name = 'Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'nonsteroidal'

    nsaids = forms.ChoiceField(
        label="Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nsaids_dosage = forms.CharField(
        label="NSAIDs Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class NervePainMedicineDetailForm(SubstanceDetailForm):
    name = 'Nerve Pain Medicine'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'nervepain'

    nerve_pain_medicine = forms.ChoiceField(
        label="Nerve Pain Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nerve_pain_medicine_dosage = forms.CharField(
        label="Nerve Pain Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class AdhdMedicineDetailForm(SubstanceDetailForm):
    name = 'ADHD Medication'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'adhd'

    adhd_medicine = forms.ChoiceField(
        label="ADHD medication (e.g., Adderall, Ritalin)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    adhd_medicine_dosage = forms.CharField(
        label="ADHD Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class OtherMedicationDetailForm(SubstanceDetailForm):
    name = 'Other Medication'
    show_condition_step = 'prescription-drilldown'
    show_condition_field = 'other'

    other_medicine_name = forms.CharField(
        label="Other Medication Name",
        help_text="Please fill in other medication name/type (e.g., suboxone)",
        required=True)
    other_medicine = forms.ChoiceField(
        label="Other Medication Quantity",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    other_medicine_dosage = forms.CharField(
        label="Other Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)


class MedicalSleepMedicationDetailForm(SubstanceDetailForm):
    name = 'Medical Sleep Medication'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'sleepmedication-medical'

    sleep_medication_medical = forms.ChoiceField(
        label="Sleep Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    sleep_medication_medical_dosage = forms.CharField(
        label="Sleep Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalMuscleRelaxantsDetailForm(SubstanceDetailForm):
    name = 'Medical Muscle Relaxants'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'musclerelaxants-medical'

    muscle_relaxants_medical = forms.ChoiceField(
        label="Muscle Relaxants",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    muscle_relaxants_medical_dosage = forms.CharField(
        label="Muscle Relaxants Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalNonSteroidalAntiInflammatoryDrugsDetailForm(SubstanceDetailForm):
    name = 'Medical Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'nonsteroidal-medical'

    nsaids_medical = forms.ChoiceField(
        label="Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nsaids_medical_dosage = forms.CharField(
        label="NSAIDs Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalNervePainMedicineDetailForm(SubstanceDetailForm):
    name = 'Medical Nerve Pain Medicine'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'nervepain-medical'

    nerve_pain_medicine_medical = forms.ChoiceField(
        label="Nerve Pain Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nerve_pain_medicine_medical_dosage = forms.CharField(
        label="Nerve Pain Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalAdhdMedicineDetailForm(SubstanceDetailForm):
    name = 'Medical ADHD Medication'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'adhd-medical'

    adhd_medicine_medical = forms.ChoiceField(
        label="ADHD medication (e.g., Adderall, Ritalin)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    adhd_medicine_medical_dosage = forms.CharField(
        label="ADHD Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class MedicalOtherMedicationDetailForm(SubstanceDetailForm):
    name = 'Other Medication taken for medical purposes'
    show_condition_step = 'prescription-medical-drilldown'
    show_condition_field = 'other-medical'

    other_medicine_medical_name = forms.CharField(
        label="Other Medication Name",
        help_text="Please fill in other medication name/type (e.g., suboxone)",
        required=True)
    other_medicine_medical = forms.ChoiceField(
        label="Other Medication Quantity",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    other_medicine_dosage = forms.CharField(
        label="Other Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalSleepMedicationDetailForm(SubstanceDetailForm):
    name = 'Recreational Sleep Medication'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'sleepmedication-recreational'

    sleep_medication_recreational = forms.ChoiceField(
        label="Sleep Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    sleep_medication_recreational_dosage = forms.CharField(
        label="Sleep Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalMuscleRelaxantsDetailForm(SubstanceDetailForm):
    name = 'Recreational Muscle Relaxants'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'musclerelaxants-recreational'

    muscle_relaxants_recreational = forms.ChoiceField(
        label="Muscle Relaxants",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    muscle_relaxants_recreational_dosage = forms.CharField(
        label="Muscle Relaxants Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalNonSteroidalAntiInflammatoryDrugsDetailForm(SubstanceDetailForm):
    name = 'Recreational Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'nonsteroidal-recreational'

    nsaids_recreational = forms.ChoiceField(
        label="Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nsaids_recreational_dosage = forms.CharField(
        label="NSAIDs Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalNervePainMedicineDetailForm(SubstanceDetailForm):
    name = 'Recreational Nerve Pain Medicine'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'nervepain-recreational'

    nerve_pain_medicine_recreational = forms.ChoiceField(
        label="Nerve Pain Medication",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    nerve_pain_medicine_recreational_dosage = forms.CharField(
        label="Nerve Pain Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalAdhdMedicineDetailForm(SubstanceDetailForm):
    name = 'Recreational ADHD Medication'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'adhd-recreational'

    adhd_medicine_recreational = forms.ChoiceField(
        label="ADHD medication (e.g., Adderall, Ritalin)",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    adhd_medicine_recreational_dosage = forms.CharField(
        label="ADHD Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)

class RecreationalOtherMedicationDetailForm(SubstanceDetailForm):
    name = 'Other Medication for recreational purposes'
    show_condition_step = 'prescription-recreational-drilldown'
    show_condition_field = 'other-recreational'

    other_medicine_recreational_name = forms.CharField(
        label="Other Medication Name",
        help_text="Please fill in other medication name/type (e.g., suboxone)",
        required=True)
    other_medicine_recreational = forms.ChoiceField(
        label="Other Medication Quantity",
        help_text="How many prescription pills/tablets did you use (total number of pills)?",
        choices=make_choices('pill', 'pills'),
        required=True)
    other_medicine_dosage = forms.CharField(
        label="Other Medication Dosage",
        widget=TextInput(attrs={'placeholder': 'mg'}),
        help_text="Please fill in the typical number of milligrams (mg) per pill/tablet "
                  "(i.e., 2.5 mg/pill, 200 mg/pill, 1000 mg/pill, etc.)",
        required=True)


class IllegalDrugsDetailForm(SubstanceDetailForm):
    name = 'What type of illegal drugs did you use?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'illegal-drugs'

    cocaine = forms.BooleanField(label='Cocaine', required=False)
    amphetamine = forms.BooleanField(label='Amphetamine', required=False)
    methamphetamine = forms.BooleanField(label='Methamphetamine', required=False)
    mdma = forms.BooleanField(label='MDMA', required=False)
    heroin = forms.BooleanField(label='Heroin', required=False)
    lsd = forms.BooleanField(label='LSD', required=False)
    mushrooms = forms.BooleanField(label='Mushrooms', required=False)
    peyote = forms.BooleanField(label='Peyote', required=False)
    ecstasy = forms.BooleanField(label='Ecstasy', required=False)
    other_illegal_drugs = forms.CharField(
        label='Other drugs',
        help_text="Please fill in name/type of other drugs",
        required=False)

    def clean(self):
        if not list([v for k, v in self.cleaned_data.items() if v]):
            msg = forms.ValidationError("You must pick one of the options")
            self.add_error(None, msg)


class OtherDetailForm(SubstanceDetailForm):
    name = 'What type of other substances did you use?'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'other'

    other_substances = forms.CharField(
        label='Other substance names',
        help_text="Please fill in name/type of other substances and how much of this substance was used. i.e: any recreational use of prescription drugs (please include amount of pills and dosage), 1 hit of salvia, 1 g kratom, 5 mg synthetic cannabis (K2, spice), etc.",
        required=True)

class NoneDetailForm(SubstanceDetailForm):
    name = 'Please Click Submit if you did not use any substances on this day.'
    show_condition_step = 'substance-drilldown'
    show_condition_field = 'none'


OtherDetailFormSet = formset_factory(OtherDetailForm, extra=1)
OtherDetailFormSet.name = 'What type of other substances did you use?'
OtherDetailFormSet.show_condition_step = 'substance-drilldown'
OtherDetailFormSet.show_condition_field = 'other'
OtherDetailFormSet.show = OtherDetailForm.show
