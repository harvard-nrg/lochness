import os
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
    logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
    deidentify = deidentify_flag(Lochness, subject.study)
    logger.debug('deidentify for study {0} is {1}'.format(subject.study, deidentify))
    for redcap_instance,redcap_subject in iterate(subject):
        for redcap_project,api_url,api_key in redcap_projects(Lochness, subject.study, redcap_instance):
            _debug_tup = (redcap_instance, redcap_project, redcap_subject)
            record_query = {
                'token': api_key,
                'content' : 'record',
                'format': 'json',
                'records': redcap_subject
            }
            if deidentify:
                # get fields that aren't identifiable and narrow record query by field name
                metadata_query = {
                    'token': api_key,
                    'content' : 'metadata',
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
                logger.info('no redcap data for {0}'.format(redcap_subject))
                continue
            # process the response content
            _redcap_project = re.sub('[\W]+', '_', redcap_project.strip())
            dst_folder = tree.get('surveys', subject.general_folder)
            fname = os.path.join(dst_folder, '{0}.{1}.json'.format(redcap_subject, _redcap_project))
            dst = os.path.join(dst_folder, fname)
            if not dry:
                if not os.path.exists(dst):
                    logger.debug('saving {0}'.format(dst))
                    lochness.atomic_write(dst, content)
                else:
                    # responses are not stored atomically in redcap
                    crc_src = lochness.crc32(content.decode('utf-8'))
                    crc_dst = lochness.crc32file(dst)
                    if crc_dst != crc_src:
                        logger.warn('file has changed {0}'.format(dst))
                        lochness.backup(dst)
                        logger.debug('saving {0}'.format(dst))
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
        raise KeyringError("{0} not found in keyring".format(redcap_instance))
    if 'URL' not in Keyring[redcap_instance]:
        raise KeyringError("{0} > URL not found in keyring".format(redcap_instance))
    if 'API_TOKEN' not in Keyring[redcap_instance]:
        raise KeyringError("{0} > API_TOKEN not found in keyring".format(redcap_instance))
    api_url = Keyring[redcap_instance]['URL'].rstrip('/') + '/api/'
    # check for soft keyring items
    if phoenix_study not in Keyring['lochness']['REDCAP']:
        logger.debug('lochness > REDCAP > {0} not found in keyring'.format(phoenix_study))
        return
    if redcap_instance not in Keyring['lochness']['REDCAP'][phoenix_study]:
        logger.debug('lochness > REDCAP > {0} > {1} not found in keyring'.format(phoenix_study, redcap_instance))
        return
    # begin generating project,api_url,api_key tuples
    for project in Keyring['lochness']['REDCAP'][phoenix_study][redcap_instance]:
        if project not in Keyring[redcap_instance]['API_TOKEN']:
            raise KeyringError("{0} > API_TOKEN > {1} not found in keyring".format(redcap_instance, project))
        api_key = Keyring[redcap_instance]['API_TOKEN'][project]
        yield project,api_url,api_key

def post_to_redcap(api_url, data, debug_tup):
    r = requests.post(api_url, data=data, stream=True, verify=False)
    if r.status_code != requests.codes.OK:
        raise REDCapError('redcap url {0} responded {1}'.format(r.url, r.status_code))
    content = r.content
    content_len = r.raw._fp_bytes_read # you need the number bytes read before any decoding
    # verify response content integrity
    if 'content-length' not in r.headers:
        logger.warn('server did not return a content-length header, can\'t verify response integrity for {0}'.format(debug_tup))
    else:
        expected_len = int(r.headers['content-length'])
        if content_len != expected_len:
            raise REDCapError('content length {0} does not match expected length {1} for {2}'.format(content_len, expected_len, debug_tup))
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
    for instance,ids in iter(subject.redcap.items()):
        for id in ids:
            yield instance,id
