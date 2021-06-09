import LAMP
import logging
import lochness
import os
import lochness.net as net
import sys
import json
import lochness.tree as tree
from io import BytesIO
from pathlib import Path
from typing import Tuple, List

logger = logging.getLogger(__name__)


@net.retry(max_attempts=5)
def sync(Lochness: 'lochness.config',
         subject: 'subject.metadata',
         dry: bool = False):
    '''Sync mindlamp data

    To do:
    - Currently the mindlamp participant id is set by mindlamp, when the
      participant object is created. API can download all list of participant
      ids, but there is no mapping of which id corresponds to which subject.
    - Above information has to be added to the metadata.csv file.
    - Add ApiExceptions
    '''
    logger.debug(f'exploring {subject.study}/{subject.id}')
    deidentify = deidentify_flag(Lochness, subject.study)
    logger.debug(f'deidentify for study {subject.study} is {deidentify}')

    # get keyring for mindlamp
    api_url, access_key, secret_key = mindlamp_projects(Lochness,
                                                        subject.mindlamp)

    # connect to mindlamp API sdk
    # LAMP.connect(access_key, secret_key, api_url)
    LAMP.connect(access_key, secret_key)

    # Extra information for future version
    # study_id, study_name = get_study_lamp(LAMP)
    # subject_ids = get_participants_lamp(LAMP, study_id)

    subject_id = subject.mindlamp[f'mindlamp.{subject.study}'][0]

    # pull data from mindlamp
    activity_dicts = get_activity_events_lamp(LAMP, subject_id)
    sensor_dicts = get_sensor_events_lamp(LAMP, subject_id)

    # set destination folder
    # dst_folder = tree.get('mindlamp', subject.general_folder)
    dst_folder = tree.get('mindlamp',
                          subject.protected_folder,
                          processed=False,
                          BIDS=Lochness['BIDS'])

    # store both data types
    for data_name, data_dict in zip(['activity', 'sensor'],
                                    [activity_dicts, sensor_dicts]):
        dst = os.path.join(
                dst_folder,
                f'{subject_id}_{subject.study}_{data_name}.json')

        jsonData = json.dumps(
            data_dict,
            sort_keys=True, indent='\t', separators=(',', ': '))

        content = jsonData.encode()

        if not Path(dst).is_file():
            lochness.atomic_write(dst, content)
        else:  # compare existing json to the new json
            crc_src = lochness.crc32(content.decode('utf-8'))
            crc_dst = lochness.crc32file(dst)
            if crc_dst != crc_src:
                logger.warn(f'file has changed {dst}')
                lochness.backup(dst)
                logger.debug(f'saving {dst}')
                lochness.atomic_write(dst, content)


def deidentify_flag(Lochness, study):
    ''' get study specific deidentify flag with a safe default '''
    value = Lochness.get('mindlamp', dict()) \
                    .get(study, dict()) \
                    .get('deidentify', False)
    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return False
    return value


def mindlamp_projects(Lochness: 'lochness.config',
                      mindlamp_instance: 'subject.mindlamp.item'):
    '''get mindlamp api_url and api_key for a phoenix study'''
    Keyring = Lochness['keyring']

    key_name = list(mindlamp_instance.keys())[0]  # mindlamp.StudyA
    # Assertations
    # check for mandatory keyring items
    # if 'mindlamp' not in Keyring['lochness']:
        # raise KeyringError("lochness > mindlamp not found in keyring")

    if key_name not in Keyring:
        raise KeyringError(f"{mindlamp_instance} not found in keyring")

    if 'URL' not in Keyring[key_name]:
        raise KeyringError(f"{mindlamp_instance} > URL not found in keyring")

    if 'ACCESS_KEY' not in Keyring[key_name]:
        raise KeyringError(f"{mindlamp_instance} > ACCESS_KEY "
                            "not found in keyring")

    if 'SECRET_KEY' not in Keyring[key_name]:
        raise KeyringError(f"{mindlamp_instance} > SECRET_KEY "
                            "not found in keyring")

    api_url = Keyring[key_name]['URL'].rstrip('/')
    access_key = Keyring[key_name]['ACCESS_KEY']
    secret_key = Keyring[key_name]['SECRET_KEY']

    return api_url, access_key, secret_key


class KeyringError(Exception):
    pass


def get_study_lamp(lamp: LAMP) -> Tuple[str, str]:
    '''Return study id and name

    Assert there is only single study under the authenticated MindLamp.

    Key arguments:
        lamp: authenticated LAMP object.

    Returns:
        (study_id, study_name): study id and study objects, Tuple.
    '''
    study_objs = lamp.Study.all_by_researcher('me')['data']
    assert len(study_objs) == 1, "There are more than one MindLamp study"
    study_obj = study_objs[0]
    return study_obj['id'], study_obj['name']


def get_participants_lamp(lamp: LAMP, study_id: str) -> List[str]:
    '''Return subject ids for a study

    Key arguments:
        lamp: authenticated LAMP object.
        study_id: MindLamp study id, str.

    Returns:
        subject_ids: participant ids, list of str.
    '''
    subject_objs = lamp.Participant.all_by_study(study_id)['data']
    subject_ids = [x['id'] for x in subject_objs]

    return subject_ids


def get_activities_lamp(lamp: LAMP, subject_id: str) -> List[dict]:
    '''Return list of activities for a subject

    Key arguments:
        lamp: authenticated LAMP object.
        subject_id: MindLamp subject id, str.

    Returns:
        activity_dicts: activity records, list of dict.
    '''
    activity_dicts = lamp.Activity.all_by_participant(subject_id)['data']

    return activity_dicts


def get_sensors_lamp(lamp: LAMP, subject_id: str) -> List[dict]:
    '''Return list of sensors for a subject

    Key arguments:
        lamp: authenticated LAMP object.
        subject_id: MindLamp subject id, str.

    Returns:
        sensor_dicts: activity records, list of dict.
    '''
    sensor_dicts = lamp.Sensor.all_by_participant(subject_id)['data']

    return sensor_dicts


def get_activity_events_lamp(lamp: LAMP, subject_id: str) -> List[dict]:
    '''Return list of activity events for a subject

    Key arguments:
        lamp: authenticated LAMP object.
        subject_id: MindLamp subject id, str.

    Returns:
        activity_events_dicts: activity records, list of dict.
    '''
    activity_events_dicts = lamp.ActivityEvent.all_by_participant(subject_id)['data']

    return activity_events_dicts


def get_sensor_events_lamp(lamp: LAMP, subject_id: str) -> List[dict]:
    '''Return list of sensor events for a subject

    Key arguments:
        lamp: authenticated LAMP object.
        subject_id: MindLamp subject id, str.

    Returns:
        activity_dicts: activity records, list of dict.
    '''
    sensor_event_dicts = lamp.SensorEvent.all_by_participant(subject_id)['data']

    return sensor_event_dicts
