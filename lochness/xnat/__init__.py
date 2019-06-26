import os
import yaml
import uuid
import yaxil
import lochness
import logging
import tempfile as tf
import collections as col
import lochness.net as net 
import lochness.tree as tree
import lochness.config as config

yaml.SafeDumper.add_representer(col.OrderedDict, yaml.representer.SafeRepresenter.represent_dict)

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
    for alias,xnat_uids in iter(subject.xnat.items()):
        Keyring = Lochness['keyring'][alias]
        auth = yaxil.XnatAuth(url=Keyring['URL'], username=Keyring['USERNAME'], 
                              password=Keyring['PASSWORD'])
        for xnat_uid in xnat_uids:
            for experiment in experiments(auth, xnat_uid):
                logger.info(experiment)
                dirname = tree.get('mri', subject.general_folder)
                dst = os.path.join(dirname, experiment.label)
                if os.path.exists(dst):
                    try:
                        check_consistency(dst, experiment)
                        continue
                    except ConsistencyError as e:
                        logger.warn(e)
                        message = 'A conflict was detected in study {0}'.format(subject.study)
                        lochness.notify(Lochness, message, study=subject.study)
                        #lochness.backup(dst)
                        continue
                message = 'downloading {PROJECT}/{LABEL} to {FOLDER}'
                logger.debug(message.format(PROJECT=experiment.project,
                                            LABEL=experiment.label,
                                            FOLDER=dst))
                if not dry:
                    tmpdir = tf.mkdtemp(dir=dirname, prefix='.')
                    os.chmod(tmpdir, 0o0755)
                    yaxil.download(auth, experiment.label, 
                                   project=experiment.project,
                                   scan_ids=['ALL'], out_dir=tmpdir, 
                                   in_mem=False, attempts=3)
                    logger.debug('saving .experiment file')
                    save_experiment_file(tmpdir, auth.url, experiment)
                    os.rename(tmpdir, dst)

def check_consistency(d, experiment):
    '''check that local data still matches data in xnat'''
    experiment_file = os.path.join(d, '.experiment')
    if not os.path.exists(experiment_file):
        raise ConsistencyError('file not found {0}'.format(experiment_file))
    with open(experiment_file, 'r') as fo:
        experiment_local = yaml.load(fo.read(), Loader=yaml.FullLoader)
    local_uid = experiment_local['id']
    remote_uid = experiment.id
    if local_uid != remote_uid:
        raise ConsistencyError('conflict detected {0} != {1}'.format(local_uid, remote_uid))

class ConsistencyError(Exception):
    pass

def save_experiment_file(d, url, experiment):
    '''save xnat experiment metadata to a file named .experiment'''
    experiment_file = os.path.join(d, '.experiment')
    blob = experiment._asdict()
    blob['source'] = url.rstrip('/') + '/'
    blob['uuid'] = str(uuid.uuid4())
    with tf.NamedTemporaryFile(dir=d, delete=False) as fo:
        content = yaml.safe_dump(blob, default_flow_style=False)
        fo.write(content.encode('utf-8'))
        fo.flush()
        os.fsync(fo.fileno())
    os.chmod(fo.name, 0o0644)
    os.rename(fo.name, experiment_file)

def experiments(auth, uid):
    '''generator for mr session ids'''
    try:
        project,subject = uid
        logger.info('searching xnat for {0}'.format(uid))
        xnat_subject = yaxil.subjects(auth, subject, project)
        xnat_subject = next(xnat_subject)
    except yaxil.exceptions.AccessionError as e:
        logger.info('no xnat subject registered for {0}'.format(uid))
        logger.warn('double check your xnat credentials')
        return
    except yaxil.exceptions.NoSubjectsError as e:
        logger.info('no xnat subject registered for {0}'.format(uid))
        return
    for experiment in yaxil.experiments(auth, subject=xnat_subject):
        yield experiment

