import os
import re
import lochness
import logging
import requests
import lochness.net as net
import lochness.tree as tree

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
    for alias,icognition_ids in iter(subject.icognition.items()):
        base,user,password = credentials(Lochness, alias)
        with requests.Session() as s:
            for label in icognition_ids:
                # login
                url = '{0}/admin/application/login/login.php'.format(base)
                data = {
                    'username': user,
                    'password': password
                }
                r = s.post(url, data=data, verify=False)
                if r.status_code != requests.codes.OK:
                    raise iCognitionError('login url {0} responded {1}'.format(r.url, r.status_code))
                # get subject data
                params = {
                    'id': label
                }
                url = '{0}/admin/application/download/csvdata.php'.format(base)
                r = s.get(url, params=params, stream=True, verify=False)
                if r.status_code == requests.codes.NOT_FOUND:
                    logger.info('no icognition data for label={0}'.format(subject.id))
                    continue 
                if r.status_code != requests.codes.OK:
                    raise iCognitionError('data url {0} responded {1}'.format(r.url, r.status_code))
                # get the filename to save from content-disposition header
                if 'content-disposition' not in r.headers:
                    raise iCognitionError('no content-disposition in response from url {0}'.format(r.url))
                fname = re.findall('filename="(.+)"', r.headers['content-disposition'])
                if len(fname) != 1 or not fname[0]:
                    raise iCognitionError('filename expected in content-disposition: {0}'.format(fname))
                fname = fname[0]
                # verify response content integrity
                content = r.content
                content_len = r.raw._fp_bytes_read # you need the number bytes read before any decoding
                if 'content-length' not in r.headers:
                    logger.warn('server did not return a content-length header, can\'t verify response integrity')
                else:
                    expected_len = int(r.headers['content-length'])
                    if content_len != expected_len:
                        raise iCognitionError('content length {0} does not match expected length {1}'.format(content_len, expected_len))
                # save the file atomically
                dst = tree.get('cogassess', subject.general_folder, BIDS=Lochness['BIDS'])
                dst = os.path.join(dst, fname)
                if os.path.exists(dst):
                    return
                logger.debug('saving icognition response content to {0}'.format(dst))
                if not dry:
                    lochness.atomic_write(dst, content)

class iCognitionError(Exception):
    pass

def credentials(Lochness, alias):
    '''get url and credentials from keyring for alias'''
    try:
        url = Lochness['keyring'][alias]['URL']
        user = Lochness['keyring'][alias]['USERNAME']
        password = Lochness['keyring'][alias]['PASSWORD']
    except KeyError as e:
        raise lochness.KeyringError('KeyError alias={0}, key={1}'.format(alias, e))
    return url.strip('/'),user,password

