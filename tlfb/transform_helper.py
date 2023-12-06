import csv
import hashlib
import io
import logging
import re
import os
from redcap import Project
from datetime import timedelta
from raven.contrib.django.raven_compat.models import client
from tlfb.encrypttest import decrip

import requests
from dateutil.parser import parse

LOGGER = logging.getLogger(__name__)


# TODO: before running the code, change the url and API tokens to your orangization's corresponding url and API tokens
os.environ['API_URL'] = 'https://redcap.ucdenver.edu/api/'
os.environ['COHORT_KEY_TABLE_TOKEN'] = '[ YOUR SURVEY API TOKEN WITH PHONE AND FIRST LETTER ]'
os.environ['TLFB_TOKEN'] = '[ YOUR TLFB API TOKEN ]'


def transform_data(subid, timepoint, cohort, pid_number, data, with_header=True):
    dk = '9678365400123890'
    days = [k for k in data.keys()]
    days.sort()  # they are all like "2018-04-01" so lexical sort works fine

    num_days = len(days)
    if num_days > 30:
        # truncate days after 30. This shouldn't be happening with current configuration anyway but lets be safe
        days = days[0:30]
        last_date = parse(days[-1])
    else:
        last_date = parse(days[-1])
    for i in range(len(days), 30):
        days.append((last_date + timedelta(days=i + 1)).date().isoformat())

    key_data = get_subject_information(subid, timepoint)

    # cohort number decrypted from the url
    cohort_number = decrip(dk, cohort)

    key_table = {'': -1, '12345a': 1}

    if cohort_number in key_table:
        cohort_number = key_table[cohort_number]
    else:
        cohort_number = key_data['cohort']

    study = key_data["study"]
    # subid_number = key_data['subid']
    # five_digit_number = str(phone)

    transform = {
        # using last_date here as set above will make it the submission date, which should help keep these straight
        'pid': pid_number,
        'cohort': cohort_number,
        'subid': subid,
        'study': study,
        # 'five_digit': five_digit_number,
        'timepoint': timepoint,
        'pid_alc': pid_number,
        'pid_tob': pid_number,
        'pid_can': pid_number,
        'pid_rx': pid_number,
        'pid_illegal': pid_number,
        # 'five_digit_alc': five_digit_number,
        # 'five_digit_tob': five_digit_number,
        # 'five_digit_can': five_digit_number,
        # 'five_digit_rx': five_digit_number,
        # 'five_digit_illegal': five_digit_number,
        'cohort_alc': cohort_number,
        'cohort_tob': cohort_number,
        'cohort_can': cohort_number,
        'cohort_rx': cohort_number,
        'cohort_illegal': cohort_number,
    }

    for idx, day in enumerate(days):
        suffix = '_d' + str(idx + 1).zfill(2)
        substances = data.get(day, {}).get('substances', {})
        transform['subst_bin' + suffix] = ','.join([
            '1' if [x for x in substances.keys() if
                    x in ['beer', 'wine', 'shots', 'other_alcohol_name', 'other_alcohol_quantity']] else '0',
            '1' if [x for x in substances.keys() if
                    x in ['cigarettes', 'ecigs', 'chew', 'cigars', 'hookah', 'other_tobacco_name',
                          'other_tobacco_quantity']] else '0',
            '1' if [x for x in substances.keys() if
                    x in ['study_cannabis_flower_total_grams', 'study_cannabis_edible_thc',
                          'study_cannabis_edible_cbd']] else '0',
            '1' if [x for x in substances.keys() if
                    x in ['non_study_cannabis_flower_total_grams', 'non_study_cannabis_flower_or_bud_thc',
                          'non_study_cannabis_flower_or_bud_cbd', 'non_study_cannabis_edible_thc',
                          'non_study_cannabis_edible_cbd', 'non_study_cannabis_concentrate',
                          'non_study_cannabis_concentrate_thc', 'non_study_cannabis_concentrate_cbd',
                          'non_study_cannabis_topical_patch', 'non_study_other_cannabis_name',
                          'cannabis_concentrate','cannabis_concentrate_thc','cannabis_concentrate_cbd',
                          'cannabis_flower_or_bud', 'cannabis_flower_or_bud_cbd','cannabis_flower_or_bud_thc',
                          'cannabis_edible_thc','cannabis_edible_cbd']] else '0',
            '1' if [x for x in substances.keys() if
                    x in ['opioids', 'opioid_dosage',
                          'sleep_medication', 'sleep_medication_dosage',
                          'muscle_relaxants', 'muscle_relaxants_dosage',
                          'nsaids', 'nsaids_dosage',
                          'nerve_pain_medicine', 'nerve_pain_medicine_dosage',
                          'adhd_medicine', 'adhd_medicine_dosage',
                          'other_medicine_name', 'other_medicine', 'other_medicine_dosage']] else '0',
            '1' if [x for x in substances.keys() if
                    x in ['cocaine', 'amphetamine', 'methamphetamine', 'mdma', 'heroin',
                          'lsd', 'mushrooms', 'peyote', 'ecstasy', 'other_illegal_drugs']] else '0',
            '1' if [x for x in substances.keys() if x in ['other_substances']] else '0',
        ])

        transform['alc_beer_drinks' + suffix] = get_answer(substances, 'beer')
        transform['alc_wine_drinks' + suffix] = get_answer(substances, 'wine')
        transform['alc_hliq_drinks' + suffix] = get_answer(substances, 'shots')
        transform['alc_other_names' + suffix] = get_answer(substances, 'other_alcohol_quantity')
        transform['alc_other_drinks' + suffix] = get_answer(substances, 'other_alcohol_quantity')

        transform['tob_cigtts_amt' + suffix] = get_answer(substances, 'cigarettes')
        transform['tob_ecigs_amt' + suffix] = get_answer(substances, 'ecigs')
        transform['tob_chew_amt' + suffix] = get_answer(substances, 'chew')
        transform['tob_cigars_amt' + suffix] = get_answer(substances, 'cigars')
        transform['tob_hookah_amt' + suffix] = get_answer(substances, 'hookah')
        transform['tob_other_names' + suffix] = get_answer(substances, 'other_tobacco_name')

        transform['tob_other_amt' + suffix] = get_answer(substances, 'other_tobacco_quantity')
        transform['scan_flw_g' + suffix] = get_answer(substances, 'study_cannabis_flower_total_grams')
        transform['scan_edithc_mg' + suffix] = get_answer(substances, 'study_cannabis_edible_thc')
        transform['scan_edicbd_mg' + suffix] = get_answer(substances, 'study_cannabis_edible_cbd')
        transform['ncan_flw_g' + suffix] = get_answer(substances, 'non_study_cannabis_flower_total_grams')
        transform['ncan_flwthc_perc' + suffix] = get_answer(substances, 'non_study_cannabis_flower_or_bud_thc')
        transform['ncan_flwcbd_perc' + suffix] = get_answer(substances, 'non_study_cannabis_flower_or_bud_cbd')
        transform['ncan_edithc_mg' + suffix] = get_answer(substances, 'non_study_cannabis_edible_thc')
        transform['ncan_edicbd_mg' + suffix] = get_answer(substances, 'non_study_cannabis_edible_cbd')
        transform['ncan_dab_hits' + suffix] = get_answer(substances, 'non_study_cannabis_concentrate')
        transform['ncan_dabthc_perc' + suffix] = get_answer(substances, 'non_study_cannabis_concentrate_thc')
        transform['ncan_dabcbd_perc' + suffix] = get_answer(substances, 'non_study_cannabis_concentrate_cbd')
        transform['ncan_patch_noyes' + suffix] = get_answer(substances, 'non_study_cannabis_topical_patch')
        transform['ncan_other_names' + suffix] = get_answer(substances, 'non_study_other_cannabis_name')

        other_rx = get_answer(substances, 'other_medicine_name')

        transform['rx_all_names' + suffix] = (','.join(
            [x for x in substances.keys() if
             x in ['opioids', 'sleep_medication', 'muscle_relaxants', 'nsaids', 'nerve_pain_medicine', 'adhd_medicine'
                   ]])) + (',' + other_rx) if other_rx else ''

        transform['rx_opd_pills' + suffix] = get_answer(substances, 'opioids')
        transform['rx_opd_mgpp' + suffix] = get_answer(substances, 'opioid_dosage')
        transform['rx_sleep_pills' + suffix] = get_answer(substances, 'sleep_medication')
        transform['rx_sleep_mgpp' + suffix] = get_answer(substances, 'sleep_medication_dosage')
        transform['rx_mrelax_pills' + suffix] = get_answer(substances, 'muscle_relaxants')
        transform['rx_mrelax_mgpp' + suffix] = get_answer(substances, 'muscle_relaxants_dosage')
        transform['rx_nsaid_pills' + suffix] = get_answer(substances, 'nsaids')
        transform['rx_nsaid_mgpp' + suffix] = get_answer(substances, 'nsaids_dosage')
        transform['rx_nerv_pills' + suffix] = get_answer(substances, 'nerve_pain_medicine')
        transform['rx_nerv_mgpp' + suffix] = get_answer(substances, 'nerve_pain_medicine_dosage')
        transform['rx_adhd_pills' + suffix] = get_answer(substances, 'adhd_medicine')
        transform['rx_adhd_mgpp' + suffix] = get_answer(substances, 'adhd_medicine_dosage')
        transform['rx_other_names' + suffix] = get_answer(substances, 'other_medicine_name')
        transform['rx_other_pills' + suffix] = get_answer(substances, 'other_medicine')
        transform['rx_other_mgpp' + suffix] = get_answer(substances, 'other_medicine_dosage')
        other_illegal = get_answer(substances, 'other_illegal_drugs')
        illegal_drugs = [x for x in substances.keys() if
                         x in ['cocaine', 'amphetamine', 'methamphetamine', 'mdma', 'heroin', 'lsd', 'mushrooms',
                               'peyote', 'ecstasy']]

        if other_illegal:
            illegal_drugs.append(other_illegal)
        transform['illegal_all_names' + suffix] = ','.join(illegal_drugs)
        transform['illegal_other_names' + suffix] = get_all_others(substances)

    aggregate_data = {
        # STUDY CANNABIS
        # FLOWER
        'summ_total_scan_flw_g': get_agg(transform, ['scan_flw_g']),
        'summ_total_scan_flw_d': get_multikey_days(transform, ['scan_flw_g']),
        'summ_avg_scan_flw_gpd' : get_average(transform, ['scan_flw_g']),

        # EDIBLE
        'summ_total_scan_edithc_mg': get_agg(transform, ['scan_edithc_mg']),
        'summ_total_scan_edicbd_mg': get_agg(transform, ['scan_edicbd_mg']),
        'summ_total_scan_edi_mg':  get_agg(transform, ['scan_edithc_mg','scan_edicbd_mg']),

        'summ_total_scan_edi_d': get_multikey_days(transform, ['scan_edithc_mg','scan_edicbd_mg']),
        'summ_avg_scan_edi_mgpd': get_average(transform, ['scan_edithc_mg','scan_edicbd_mg']),


        # NON-STUDY cannabis
        # FLOWER
        'summ_total_ncan_flw_g': get_agg(transform, ['ncan_flw_g']),
        'summ_total_ncan_flw_d': get_multikey_days(transform, ['ncan_flw_g']),
        'summ_avg_ncan_flw_gpd': get_average(transform, ['ncan_flw_g']),
        'summ_avg_ncan_flwthc_perc': get_average(transform, ['ncan_flwthc_perc']),
        'summ_avg_ncan_flwcbd_perc': get_average(transform, ['ncan_flwcbd_perc']),

        # EDIBLE
        'summ_total_ncan_edithc_mg': get_agg(transform, ['ncan_edithc_mg']),
        'summ_total_ncan_edicbd_mg': get_agg(transform, ['ncan_edicbd_mg']),
        'summ_total_ncan_edi_mg': get_agg(transform, ['ncan_edithc_mg','ncan_edicbd_mg']),

        'summ_total_ncan_edi_d': get_multikey_days(transform, ['ncan_edithc_mg','ncan_edicbd_mg']),
        'summ_avg_ncan_edi_mgpd': get_average(transform, ['ncan_edithc_mg','ncan_edicbd_mg']),

        # CONCENTRATE
        'summ_total_ncan_dab_hits': get_agg(transform, ['ncan_dab_hits']),
        'summ_total_ncan_dab_d': get_multikey_days(transform, ['ncan_dab_hits']),
        'summ_avg_ncan_dab_hitspd': get_average(transform, ['ncan_dab_hits']),

        'summ_avg_ncan_dabthc_perc': get_average(transform, ['ncan_dabthc_perc']),
        'summ_avg_ncan_dabcbd_perc': get_average(transform, ['ncan_dabcbd_perc']),
        'summ_total_ncan_patch_d': get_multikey_days(transform, ['ncan_patch_noyes']),


        # STUDY AND NON COMBINED
        # EDIBLE
        'summ_total_can_edi_mg': get_agg(transform, ['ncan_edithc_mg','scan_edithc_mg','ncan_edicbd_mg','scan_edicbd_mg']),
        'summ_total_can_edi_d': get_multikey_days(transform, ['ncan_edithc_mg','scan_edithc_mg','ncan_edicbd_mg','scan_edicbd_mg']),
        'summ_avg_can_edi_mgpd': get_average(transform, ['ncan_edithc_mg','scan_edithc_mg','ncan_edicbd_mg','scan_edicbd_mg']),

        # FLOWER
        'summ_total_can_flw_g': get_agg(transform, ['ncan_flw_g','scan_flw_g']),
        'summ_total_can_flw_d': get_multikey_days(transform, ['ncan_flw_g','scan_flw_g']),
        'summ_avg_can_flw_gpd': get_average(transform, ['ncan_flw_g','scan_flw_g']),


        # CANNABIS DAILY TOTALS
        'summ_total_scan_all_d': get_multikey_days(transform, ['scan']),
        'summ_total_ncan_all_d': get_multikey_days(transform, ['ncan']),
        'summ_total_can_all_d': get_multikey_days(transform, ['can']),


        # ALCOHOL
        'summ_total_canalc_d': get_multikey_same_days(transform, ['can', 'alc']),

        # ALL ALCOHOL
        'summ_total_alc_all_drinks': get_agg(transform, ['alc']),
        'summ_total_alc_all_d': get_multikey_days(transform, ['alc']),
        'summ_avg_alc_all_drinkspd': get_average(transform, ['alc']),


        # TOBACCO
        'summ_total_tob_cigtts_amt': get_agg(transform, ['tob_cigtts']),
        'summ_total_tob_ecigs_amt': get_agg(transform, ['tob_ecigs']),
        'summ_total_tob_chew_amt': get_agg(transform, ['tob_chew']),
        'summ_total_tob_cigars_amt': get_agg(transform, ['tob_cigars']),
        'summ_total_tob_hookah_amt': get_agg(transform, ['tob_hookah']),

        'summ_total_tob_cigtts_d': get_multikey_days(transform, ['tob_cigtts']),
        'summ_total_tob_ecigs_d':get_multikey_days(transform, ['tob_ecigs']),
        'summ_total_tob_chew_d':get_multikey_days(transform, ['tob_chew']),
        'summ_total_tob_cigars_d': get_multikey_days(transform, ['tob_cigars']),
        'summ_total_tob_hookah_d':get_multikey_days(transform, ['tob_hookah']),
        'summ_total_tob_all_d':get_multikey_days(transform, ['tob']),


        # RECREATIONAL
        'summ_total_rx_opd_mg': get_mg(transform, ['rx_opd']),
        'summ_total_rx_sleep_mg': get_mg(transform, ['rx_sleep']),
        'summ_total_rx_mrelax_mg': get_mg(transform, ['rx_mrelax']),
        'summ_total_rx_nsaid_mg': get_mg(transform, ['rx_nsaid']),
        'summ_total_rx_nerv_mg': get_mg(transform, ['rx_nerv']),
        'summ_total_rx_adhd_mg': get_mg(transform, ['rx_adhd']),
        'summ_total_rx_other_mg': get_mg(transform, ['rx_other']),

        'summ_total_rx_opd_d': get_multikey_days(transform, ['rx_opd']),
        'summ_total_rx_sleep_d': get_multikey_days(transform, ['rx_sleep']),
        'summ_total_rx_mrelax_d': get_multikey_days(transform, ['rx_mrelax']),
        'summ_total_rx_nsaid_d': get_multikey_days(transform, ['rx_nsaid']),
        'summ_total_rx_nerv_d': get_multikey_days(transform, ['rx_nerv']),
        'summ_total_rx_adhd_d': get_multikey_days(transform, ['rx_adhd']),
        'summ_total_rx_other_d': get_multikey_days(transform, ['rx_other']),
        'summ_total_rx_all_d': get_multikey_days(transform, ['rx']),

        # ILLEGAL
        'summ_total_illegal_all_d': get_multikey_days(transform, ['illegal']),
    }

    transform.update(aggregate_data)

    output = io.StringIO()
    writer = csv.writer(output)
    if with_header:
        writer.writerow(transform.keys())
    writer.writerow(transform.values())
    return output.getvalue()


def get_subject_information(subid, timepoint):
    key_data = {}
    try:
        key_table_project = Project(os.getenv('API_URL'), os.getenv('COHORT_KEY_TABLE_TOKEN'))
        records = key_table_project.export_records()
        # TODO: Add in code to assign your study id and cohort from your REDCAP Survey
    except:
        client.captureException()
        key_data['cohort'] = '-1'
        key_data['study'] = ''
    return key_data  # returns data from the key table


def export_transformed_data(output):
    sha = hashlib.sha1()
    sha.update(output.encode('utf-8'))
    r = requests.post(os.getenv('API_URL'), data={
        'token': os.getenv('TLFB_TOKEN'),
        'content': 'record',
        'format': 'csv',
        'type': 'flat',
        'overwriteBehavior': 'normal',
        'forceAutoNumber': 'false',
        'data': output,
        'returnContent': 'count',
        'returnFormat': 'json',
        'record_id': sha.hexdigest()[:16]
    })
    result = r.json()

    if result.get('count'):
        count = result.get('count')
        if count == 1:
            LOGGER.info('Successfully uploaded to storage')
        else:
            LOGGER.error('Storage returned an error: '+result)
    else:
        LOGGER.error('Storage returned an error: '+result)
    return False


def value_converter(raw_string):
    if raw_string.lower() == 'yes':
        return '1'
    value = raw_string.replace('1/2', '.5')
    value = value.replace('1/4', '.25')
    value = value.replace('3/4', '.75')
    value = value.replace('or more', '')
    value = value.replace('or less', '')
    value = value.replace(' ', '')
    value = re.sub("[\(\[].*?[\)\]]", "", value)  # some legacy responses are like "0.5 (1/2 gram)"
    value = re.sub(r'[a-zA-Z /,]+', '', value)  # remove characters and spaces and slashes and commas
    if value in  ['999','Unknown']:
         value = '-9999';
    if value in ['----']:
        value = '-8888'
    return value


def unknown_check(sum, value, first_agg_check = False):
    if first_agg_check:
        return  float(value)

    # will return -9999 or -8888 when the only values entered where unknown
    if sum in [-9999,-8888,-8989] and int(float(value)) in [-9999,-8888,-8989]:
        if sum in [-9999,-8888]:
            if sum == int(float(value)):
                sum = float(value)
            else:
                sum = float(-8989)
        else:
            sum = float(-8989)
    elif sum in [-9999,-8888,-8989]:
        sum = round(float(value), 10)
    elif sum not in [-9999,-8888,-8989] and int(float(value)) in [-9999,-8888]:
        pass
    else:
        sum = round(sum + float(value), 10)
    return sum


def get_answer(substances, substance_name):
    # return a string even if its not there
    val = substances.get(substance_name) or {}

    # this line is only to correct for variables that were created earlier and
    # don't have 'non_study' or 'study' as part of their name
    if not val and substance_name[:9] == 'non_study':
        if substance_name == 'non_study_cannabis_flower_total_grams':
            val = substances.get('cannabis_flower_or_bud') or {}
        else:
            val = substances.get(substance_name[10:]) or {}

    # gets the value of the answer
    if isinstance(val, str):
        return val
    if val:
        value = value_converter(val.get('answer', ''))
        return value
    return val.get('answer', '')


def get_agg(data, keys):
    sum = 0.0
    first_agg = True
    empty = True
    for key in keys:
        for k, v in data.items():
            # exclude alc_other, cann_other, etc. Also exclude rx_all_names
            if key in k and v and not any(x in k for x in ['other','names','pid','cohort']):  # e.g. if 'can' in 'cann_uflwr_d01'
                value = value_converter(v)
                if not value:
                    continue
                else:
                    empty = False
                try:
                    if key == 'cann' or key == 'can' or key == 'cans':
                        if not any(x in k for x in['flwrthc','flwrcbd','dabthc','dabcbd']):
                            sum = unknown_check(sum, value, first_agg)
                    elif key == 'rx':
                         if 'mg' not in k:
                             sum = unknown_check(sum, value, first_agg)
                    else:
                        sum = unknown_check(sum, value, first_agg)

                    if first_agg:
                        first_agg = False
                except:  # in some cases we have non-valid numbers...
                    LOGGER.error('Failed to convert "{}"'.format(value), extra={
                        'stack': True,
                    })
                    client.captureException()
                    continue

    # Don't want it filling in 0s if there was nothing to aggregate
    if empty:
        return ''
    elif sum in [-9999,-8888,-8989]:
        return str(int(sum))
    else:
        return str(sum)


def get_mg(data, keys):
    mg_sum = 0.0
    first_agg = True
    daylies = []
    for key in keys:
        for k, v in data.items():
            day = k[-4:]
            if key in k:
                if day not in daylies and not any(x in k for x in ['names','pid','cohort']):  # e.g. if 'can' in 'cann_uflwr_d01'
                    daylies.append(day)
                    pill_var = key+'_pills'+day
                    mg_var = key+'_mgpp'+day
                    if pill_var in data and data[pill_var] and mg_var in data and data[mg_var]:
                        if first_agg:
                            first_agg = False
                        try:
                            mg_sum += round(float(data[pill_var]) * float(data[mg_var]), 10)
                        except:  # in some cases we have non-valid numbers...
                            LOGGER.error('Failed to convert "{}"'.format(v), extra={
                                'stack': True,
                            })
                            client.captureException()
                            continue
                    else:
                        continue
    # Don't want it filling in 0s if there was nothing to aggregate
    if first_agg:
        return ''
    else:
        return str(mg_sum)


def get_multikey_days(data, keys, unknown=False):
    days = []
    for key in keys:
        for k, v in data.items():
            if key in k and not any(x in k for x in ['pid', 'cohort']) and v:  # "if v" should eliminate answers of 0 or empty string
                if k[-3:] not in days:
                    if unknown and v in ['-9999','-8888','999','----','Unknown']:
                        pass
                    else:
                        days.append(k[-3:])
    return len(days)

def get_multikey_same_days(data, keys):
    days = {}
    for key in keys:
        key_days = []
        for k, v in data.items():
            if key in k and not any(x in k for x in ['pid', 'cohort']) and v:
                if k[-3:] not in key_days:
                    key_days.append(k[-3:])
        days[key] = key_days
    same_days = key_days
    for k in keys:
        same_days = set(same_days) & set(days[k])
    return len(same_days)

def get_average(data, keys):
    sum = get_agg(data, keys)
    if sum == '':
        return sum

    day = get_multikey_days(data, keys, True)
    if float(sum) in [-9999,-8888,-8989]:
        return str(int(float(sum)))
    elif day:
        return str(round(float(sum)/float(day), 10))
    else:
        return '0.0'


def get_all_others(substances):
    other_drugs = []
    other_drugs.append(get_answer(substances, 'other_substances'))
    any_other = True
    i = 1
    while any_other:
        other_drug = get_answer(substances, 'other_substances'+ str(i))
        if other_drug == '':
            any_other = False
        else:
            other_drugs.append(other_drug)
            i += 1
    return ','.join(other_drugs)
