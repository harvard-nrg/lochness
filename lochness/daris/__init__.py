import os
import yaml
import lochness
import logging
import zipfile
import shutil
from pathlib import Path
import tempfile as tf
import collections as col
import lochness.net as net
import lochness.tree as tree

yaml.SafeDumper.add_representer(
    col.OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
logger = logging.getLogger(__name__)


def daris_download(daris_uid: str, latest_pull_mtime: float,
                   token: str, project_cid: str,
                   url: str, dst_zipfile: str) -> None:
    '''Download data from DaRIS using curl'''

    # filters for curl
    curl_filters = [
        f"xpath(mf-dicom-patient/id)='{daris_uid}'",
        "xpath(mf-dicom-series/modality)='MR'",
        f"mtime>='{latest_pull_mtime}'"
        ]

    curl_filter = ' and '.join(curl_filters)

    curl_command = f'curl -G -o ' \
                   f'{dst_zipfile} ' \
                   f'--data-urlencode "module=download" ' \
                   f'--data-urlencode "_token={token}" ' \
                   f'--data-urlencode "cid={project_cid}" ' \
                   f'--data-urlencode "filter={curl_filter}" ' \
                   f'"{url}/daris/dicom.mfjp"'

    os.popen(curl_command).read()


@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    logger.debug(f'exploring {subject.study}/{subject.id}')

    for alias, daris_uids in iter(subject.daris.items()):
        Keyring = Lochness['keyring'][alias]
        token = Keyring['TOKEN']
        url = Keyring['URL']
        project_cid = Keyring['PROJECT_CID']

        for daris_uid in daris_uids:
            dirname = tree.get('mri',
                               subject.protected_folder,
                               processed=False)
            dst_zipfile = os.path.join(dirname, 'tmp.zip')
            timestamp_loc = os.path.join(dirname, '.latest_pull_timestamp')

            # load the time of the lastest data pull from daris
            # estimated from the mtime of the zip file downloaded
            if Path(timestamp_loc).is_file():
                latest_pull_mtime = load_latest_pull_timestamp(timestamp_loc)
            else:
                latest_pull_mtime = 0

            if not dry:
                tmpdir = tf.mkdtemp(dir=dirname, prefix='.')
                os.chmod(tmpdir, 0o0755)

                # execute the curl command
                logger.info(f'Downloading from DaRIS for {daris_uid}')
                daris_download(daris_uid, latest_pull_mtime,
                               token, project_cid,
                               url, dst_zipfile)

                with zipfile.ZipFile(dst_zipfile, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                nfiles_in_dirs = []
                for root, dirs, files in os.walk(tmpdir):
                    for directory in dirs:
                        os.chmod(os.path.join(root, directory), 0o0755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o0755)
                    nfiles_in_dirs.append(len(files))

                # if there is any new file downloaded save timestamp
                if any([x > 1 for x in nfiles_in_dirs]):
                    logger.info(f'New MRI file downloaded for {daris_uid}')
                    save_latest_pull_timestamp(dst_zipfile, timestamp_loc)

                shutil.copytree(tmpdir, dirname, dirs_exist_ok=True)
                os.remove(dst_zipfile)


def save_latest_pull_timestamp(pulled_zipfile: str,
                               timestamp_loc: str):
    '''Create lastest pull timestamp based on the pulled zip file'''
    fname = Path(pulled_zipfile)

    with open(timestamp_loc, 'w') as f:
        f.write(str(fname.stat().st_mtime))


def load_latest_pull_timestamp(timestamp_loc: str):
    '''Load lastest pull timestamp saved in a hidden file'''
    with open(timestamp_loc, 'r') as f:
        latest_pull_mtime = f.read().strip()

    return float(latest_pull_mtime)
