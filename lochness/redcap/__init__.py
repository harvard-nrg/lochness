import os
import sys
import re
import json
import lochness
import logging
import requests
import lochness.net as net
import collections as col
import lochness.tree as tree

logger = logging.getLogger(__name__)


@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    logger.debug(f'exploring {subject.study}/{subject.id}')
    deidentify = deidentify_flag(Lochness, subject.study)
    logger.debug(f'deidentify for study {subject.study} is {deidentify}')

    for redcap_instance, redcap_subject in iterate(subject):
        for redcap_project, api_url, api_key in redcap_projects(
                Lochness, subject.study, redcap_instance):
            _debug_tup = (redcap_instance, redcap_project, redcap_subject)

            print(_debug_tup)

            sys.exit()
            record_query = {
                'token': api_key,
                'content': 'record',
                'format': 'json',
                'records': redcap_subject
            }

            if deidentify:
                # get fields that aren't identifiable and narrow record query
                # by field name
                metadata_query = {
                    'token': api_key,
                    'content': 'metadata',
                    'format': 'json'
                }

                content = post_to_redcap(api_url, metadata_query, _debug_tup)
                metadata = json.loads(content)
                field_names = []
                for field in metadata:
                    if field['identifier'] != 'y':
                        field_names.append(field['field_name'])
                record_query['fields'] = ','.join(field_names)

            # post query to redcap
            content = post_to_redcap(api_url, record_query, _debug_tup)

            # check if response body is nothing but a sad empty array
            if content.strip() == '[]':
                logger.info(f'no redcap data for {redcap_subject}')
                continue
            # process the response content
            _redcap_project = re.sub(r'[\W]+', '_', redcap_project.strip())

            # default location to protected folder
            dst_folder = tree.get('surveys', subject.protected_folder)
            fname = f'{redcap_subject}.{_redcap_project}.json'
            dst = os.path.join(dst_folder, fname)

            if not dry:
                if not os.path.exists(dst):
                    logger.debug(f'saving {dst}')
                    lochness.atomic_write(dst, content)
                else:
                    # responses are not stored atomically in redcap
                    crc_src = lochness.crc32(content.decode('utf-8'))
                    crc_dst = lochness.crc32file(dst)
                    if crc_dst != crc_src:
                        logger.warn(f'file has changed {dst}')
                        lochness.backup(dst)
                        logger.debug(f'saving {dst}')
                        lochness.atomic_write(dst, content)


class REDCapError(Exception):
    pass


def redcap_projects(Lochness, phoenix_study, redcap_instance):
    '''get redcap api_url and api_key for a phoenix study'''
    Keyring = Lochness['keyring']
    # check for mandatory keyring items
    if 'REDCAP' not in Keyring['lochness']:
        raise KeyringError("lochness > REDCAP not found in keyring")
    if redcap_instance not in Keyring:
        raise KeyringError(f"{redcap_instance} not found in keyring")
    if 'URL' not in Keyring[redcap_instance]:
        raise KeyringError(f"{redcap_instance} > URL not found in keyring")
    if 'API_TOKEN' not in Keyring[redcap_instance]:
        raise KeyringError(f"{redcap_instance} > API_TOKEN "
                           "not found in keyring")

    api_url = Keyring[redcap_instance]['URL'].rstrip('/') + '/api/'

    # check for soft keyring items
    if phoenix_study not in Keyring['lochness']['REDCAP']:
        logger.debug(f'lochness > REDCAP > {phoenix_study}'
                     'not found in keyring')
        return
    if redcap_instance not in Keyring['lochness']['REDCAP'][phoenix_study]:
        logger.debug(f'lochness > REDCAP > {phoenix_study} '
                     f'> {redcap_instance} not found in keyring')
        return

    # begin generating project,api_url,api_key tuples
    for project in Keyring['lochness']['REDCAP']\
            [phoenix_study][redcap_instance]:
        if project not in Keyring[redcap_instance]['API_TOKEN']:
            raise KeyringError(f"{redcap_instance} > API_TOKEN > {project}"
                               "not found in keyring")
        api_key = Keyring[redcap_instance]['API_TOKEN'][project]
        yield project, api_url, api_key


def post_to_redcap(api_url, data, debug_tup):
    r = requests.post(api_url, data=data, stream=True, verify=False)
    if r.status_code != requests.codes.OK:
        raise REDCapError(f'redcap url {r.url} responded {r.status_code}')
    content = r.content

    # you need the number bytes read before any decoding
    content_len = r.raw._fp_bytes_read

    # verify response content integrity
    if 'content-length' not in r.headers:
        logger.warn('server did not return a content-length header, '
                    f'can\'t verify response integrity for {debug_tup}')
    else:
        expected_len = int(r.headers['content-length'])
        if content_len != expected_len:
            raise REDCapError(
                    f'content length {content_len} does not match '
                    f'expected length {expected_len} for {debug_tup}')
    return content


class KeyringError(Exception):
    pass


def deidentify_flag(Lochness, study):
    ''' get study specific deidentify flag with a safe default '''
    value = Lochness.get('redcap', dict()) \
                    .get(study, dict()) \
                    .get('deidentify', False)
    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return False
    return value


def iterate(subject):
    '''generator for redcap instance and subject'''
    for instance, ids in iter(subject.redcap.items()):
        for id_inst in ids:
            yield instance, id_inst
