import os
import io
import sys
import csv
import six
import zlib
import json
import pytz
import logging
import lochness
import itertools
import lochness.email
import datetime as dt
import tempfile as tf
import traceback as tb
import collections as col
import lochness.ssh as ssh

logger = logging.getLogger(__name__)

Subject = col.namedtuple('Subject', [
    'active',
    'study',
    'id',
    'consent',
    'beiwe',
    'icognition',
    'saliva',
    'xnat',
    'redcap',
    'dropbox',
    'general_folder',
    'protected_folder'
])

def read_phoenix_metadata(Lochness, studies=None):
    '''
    Read PHOENIX metadata file locally or remotely.
    '''
    # check for GENERAL folder
    general_folder = os.path.join(Lochness['phoenix_root'], 'GENERAL')
    protected_folder = os.path.join(Lochness['phoenix_root'], 'PROTECTED')
    # list studies (locally or remotely)
    if not studies:
        studies = lochness.listdir(Lochness, general_folder)
    # iterate over studies
    for study_name in studies:
        f = os.path.join(general_folder, study_name, '{0}_metadata.csv'.format(study_name))
        if not os.path.exists(f):
            logger.error('metadata file does not exist {0}'.format(f))
            continue
        logger.debug('reading metadata file {0}'.format(f))
        try:
            # iterate over rows in metadata file
            for subject in _subjects(Lochness, study_name, general_folder, 
                                     protected_folder, f):
                yield subject
        except StudyMetadataError as e:
            logger.error(e)
            lochness.email.metadata_error(Lochness, e.message)
            continue

def _subjects(Lochness, study, general_folder, protected_folder, metadata_file):
    meta_basename = os.path.basename(metadata_file)
    # read the study metadata fiile (local or remote)
    with lochness.openfile(Lochness, metadata_file, 'r') as fo:
        reader = csv.reader(fo)
        headers = next(reader)
        for values in reader:
            # quick sanity check of the current row
            if not values:
                continue
            if len(values) != len(headers):
                raise StudyMetadataError('bad row in metadata file for {0}'.format(meta_basename))
            # these columns are required
            row = dict(zip(headers, values))
            active = int(row['Active'].strip())
            consent = row['Consent'].strip()
            phoenix_id = row['Subject ID'].strip()
            # these columns are optional
            phoenix_study = row.get('Study', study).strip()
            saliva = dict()
            if 'Saliva' in row:
                saliva = _parse_saliva(row['Saliva'], phoenix_id)
            beiwe = dict()
            if 'Beiwe' in row:
                beiwe = _parse_beiwe(row['Beiwe'], phoenix_id)
            redcap = dict()
            if 'REDCap' in row:
                redcap = _parse_redcap(row['REDCap'], phoenix_id)
            xnat = dict()
            if 'XNAT' in row:
                xnat = _parse_xnat(row['XNAT'], phoenix_id)
            icognition = dict()
            if 'iCognition' in row:
                icognition = _parse_icognition(row['iCognition'], phoenix_id)
            onlinescoring = dict()
            if 'OnlineScoring' in row:
                onlinescoring = _parse_onlinescoring(row['OnlineScoring'], phoenix_id)
            dropbox = dict()
            if 'Dropbox' in row:
                dropbox = _parse_dropbox(row['Dropbox'], phoenix_id)
            # sanity check on very critical bits of information
            if not phoenix_id or not phoenix_study:
                raise StudyMetadataError('bad row in metadata file {0}'.format(meta_basename))
            general = os.path.join(general_folder, phoenix_study, phoenix_id)
            protected = os.path.join(protected_folder, phoenix_study, phoenix_id)
            subject = Subject(active, phoenix_study, phoenix_id, consent, beiwe,
                              icognition, saliva, xnat, redcap, dropbox,
                              general, protected)
            logger.debug('subject metadata blob:\n{0}'.format(json.dumps(subject._asdict(), indent=2)))
            yield subject

def _parse_saliva(value, default_id=None):
    '''helper function to parse a saliva value'''
    return [x.strip() for x in value.split(';') if x]

def _parse_dropbox(value, default_id=None):
    '''helper function to parse a dropbox value'''
    default = 'dropbox.cbsn:{ID}'.format(ID=default_id)
    return _simple_parser(value, default=default)
 
def _parse_xnat(value, default_id=None):
    '''helper function to parse a xnat value'''
    default = 'cbscentral:Buckner_P:{ID}'.format(ID=default_id)
    result = col.defaultdict(list)
    # split all values on semicolon
    items = [x.strip() for x in value.split(';') if x]
    # return nothing if the value was empty
    if not items:
        return result
    # use default if value was a single asterisk
    if len(items) == 1 and items[0].strip() == '*':
        logger.debug('falling back to default {0}'.format(default))
        items = [default]
    # split values on colon and return a dict structure
    for item in items:
        try:
            deployment,project,subject = item.split(':')
        except ValueError:
            raise StudyMetadataError('bad metadata value {0}'.format(item))
        result[deployment].append((project, subject))
    return result

def _parse_beiwe(value, default_id=None):
    '''helper function to parse a beiwe value'''
    result = col.defaultdict(list)
    # split all values on semicolon
    items = [x.strip() for x in value.split(';') if x]
    # return nothing if the value was empty
    if not items:
        return result
    # split values on colon and return a dict structure
    for item in items:
        try:
            deployment,study,user = item.split(':')
        except ValueError:
            raise StudyMetadataError('bad metadata value {0}'.format(item))
        result[deployment].append((study, user))
    return result
    
def _parse_redcap(value, default_id=None):
    '''helper function to parse a redcap metadata value'''
    default = 'redcap.rc:{ID}'.format(ID=default_id)
    return _simple_parser(value, default=default)

def _parse_icognition(value, default_id=None):
    '''helper function to parse an icognition metadata value'''
    default = 'mytimedtest:{ID}'.format(ID=default_id)
    return _simple_parser(value, default)

def _parse_onlinescoring(value, default_id=None):
    '''helper function to parse an onlinescoring metadata value'''
    default = 'onlinescoring:{ID}'.format(ID=default_id)
    return _simple_parser(value, default)

def _simple_parser(value, default=None):
    '''simple metadata value parser'''
    result = col.defaultdict(list)
    # split all values on semicolon
    items = [x.strip() for x in value.split(';') if x]
    # return nothing if the value was empty
    if not items:
        return result
    # use default if value was a single asterisk
    if len(items) == 1 and items[0].strip() == '*':
        logger.debug('falling back to default {0}'.format(default))
        items = [default]
    # split values on colon and return a dict structure
    for item in items:
        try:
            deployment,id = item.split(':')
        except ValueError:
            raise StudyMetadataError('bad metadata value {0}'.format(item))
        result[deployment].append(id)
    return result

class StudyMetadataNotFoundError(Exception):
    pass

class StudyMetadataError(Exception):
    pass

def openfile(Lochness, f, mode):
    '''open a file locally or fallback to sftp'''
    if os.path.exists(f):
        return open(f, mode)
    return ssh.open(Lochness, f, mode)

def listdir(Lochness, d):
    '''list a directory locally or fallback to sftp'''
    if os.path.exists(d):
        return os.listdir(d)
    return ssh.listdir(Lochness, d)

def attempt(f, Lochness, *args, **kwargs):
    '''attempt a function call'''
    if len(attempt.warnings) >= 5:
        lochness.email.attempts_error(Lochness, attempt)
        attempt.warnings = []
        #raise AttemptsError('too many attempt warnings')
    try:
        f(Lochness, *args, **kwargs)
    except Exception as e:
        logger.warn(e)
        logger.debug(tb.format_exc().strip())
        attempt.warnings.append(str(e))
attempt.warnings = []

class AttemptsError(Exception):
    pass

def configure_logging(logger, args):
    '''configure all the loggers for all things'''
    logging.getLogger('requests').setLevel(logging.WARN)
    logging.getLogger('dropbox').setLevel(logging.WARN)
    logging.getLogger('paramiko').setLevel(logging.WARN)
    logargs = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s'
    }
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('lochness').setLevel(logging.DEBUG)
        logging.getLogger('mano').setLevel(logging.DEBUG)
        logging.getLogger('yaxil').setLevel(logging.DEBUG)
    if args.log_file:
        logargs['filename'] = os.path.expanduser(args.log_file)
    logging.basicConfig(**logargs)

class KeyringError(Exception):
    pass

class SoftError(Exception):
    pass

def crc32(content, encoding='utf-8'):
    if isinstance(content, six.string_types):
        content = content.encode(encoding)
    return _crc32bin(io.BytesIO(content))

def crc32file(f):
    with open(f, 'rb') as fo:
        return _crc32bin(fo)

def _crc32bin(content, buffersize=4096):
    buffr = content.read(buffersize)
    crc = 0
    while len(buffr) > 0:
        crc = zlib.crc32(buffr, crc)
        buffr = content.read(buffersize)
    return format(crc & 0xFFFFFFFF, '08x')

def backup(f):
    '''
    Backup a file or directory to a .conflicts sub-directory 
    with an ISO 8601 timestamp appended to the file name.

    :param f: File or directory name to backup
    :type f: str
    '''
    dirname = os.path.dirname(f)
    basename = os.path.basename(f)
    conflict_dirname = os.path.join(dirname, '.conflicts')
    if not os.path.exists(conflict_dirname):
        makedirs(conflict_dirname, umask=0o5022)
    conflict_basename = '{0}-{1}'.format(basename, iso8601())
    conflict_dst = os.path.join(conflict_dirname, conflict_basename)
    logger.debug('renaming {0} to {1}'.format(f, conflict_dst))
    os.rename(f, conflict_dst)

def notify(Lochness, s, study=None):
    '''
    Send a notification. If study is passed, the notifcation recipients
    will include email addresses listed in the configuration file for 
    that study.

    :param Lochness: Lochness context
    :type Lochness: dict
    :param s: Message string
    :type s: str
    :param study: Study name
    :type study: str
    '''
    if 'notify' not in Lochness:
        raise NotificationError("no 'notify' section found in the configuration file")
    if 'sender' not in Lochness:
        raise NotificationError("no 'sender' section found in the configuration file")
    # schema validation would help here instead of making assumptions
    recipients = set()
    if study and study in Lochness['notify']:
        for address in Lochness['notify'][study]:
            recipients.add(address)
    if '__global__' in Lochness['notify']:
        for address in Lochness['notify']['__global__']:
            recipients.add(address)
    lochness.email.send(recipients, Lochness['sender'], 'lochness notification', s)

class NotificationError(Exception):
    pass

def makedirs(path, umask):
    '''
    Make a directory path (recursively) under a specific umask

    :param path: Path to create
    :type path: str
    :param umask: umask
    :type umask: int
    '''
    umask = os.umask(umask)
    os.makedirs(path)
    os.umask(umask)

def lchop(s, beginning):
    '''
    Remove a substring from beginning of string

    :param s: Input string
    :type s: str
    :param beginning: Substring to remove
    :type beginning: str
    :returns: Resulting string
    :rtype: str
    '''
    if s.startswith(beginning):
        return s[len(beginning):]
    return s

def iso8601(tz="UTC"):
    '''
    Get ISO 8601 timestamp as a string.
    
    :param tz: Timezone
    :type tz: str
    :returns: Timestamp
    :rtype: str
    '''
    return dt.datetime.now(pytz.timezone(tz)).isoformat()

def atomic_write(filename, content, overwrite=True, permissions=0o0644, encoding='utf-8'):
    '''
    Write a file atomically by writing the file content to a
    temporary location first, then renaming the file. 

    TODO: I rely pretty heavily on os.rename for ensuring file integrity and 
    consistency throughout PHOENIX, but os.rename does not silently overwrite 
    existing files on Windows natively. For now, the functionality provided 
    here can only be supported under Windows Subsystem for Linux (Windows 10 
    version 1607 and later) until a better solution exists.

    :param filename: Filename
    :type filename: str
    :param content: File content
    :type content: str
    :param overwrite: Overwrite
    :type overwrite: bool
    :param permissions: Octal permissions
    :type permissions: octal
    '''
    filename = os.path.expanduser(filename)
    if not overwrite and os.path.exists(filename):
        raise WriteError("file already exists: %s" % filename)
    dirname = os.path.dirname(filename)
    with tf.NamedTemporaryFile(dir=dirname, prefix='.', delete=False) as tmp:
        if isinstance(content, six.string_types):
            tmp.write(content.decode(encoding))
        else:
            tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.chmod(tmp.name, permissions)
    os.rename(tmp.name, filename)

def WriteError(Exception):
    pass

spinner = itertools.cycle(['-', '/', '|', '\\'])
'''
Use this to render a command-line spinning pinwheel cursor animation.
'''
