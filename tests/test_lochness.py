import lochness
from lochness import config
from config.test_config import create_config
from mock_args import LochnessArgs, mock_load


def test_do():
    args = LochnessArgs()
    Lochness = mock_load(args.config, args.archive_base)

def test_read_phoenix_data():
    args = LochnessArgs()
    args.source = ['xnat', 'box']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject)

def test_read_phoenix_metadata():
    args = LochnessArgs()
    args.source = ['xnat', 'box', 'redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    config_string, fp = create_config()

    Lochness = mock_load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        # Subject(active=1,
                # study='StudyA', id='EXAMPLE', consent='1979-01-01',
                # beiwe=defaultdict(<class 'list'>,
                    # {'beiwe': [('5432', 'abcde')]}),
                # icognition={},
                # saliva={},
                # xnat=defaultdict(<class 'list'>,
                    # {'xnat.hcpep': [('HCPEP-BWH', '1001')]}),
                # redcap=defaultd ict(<class 'list'>,
                    # {'redcap.hcpep': ['1001_1']}),
                # dropbox={},
                # box=defaultdict(<class 'list'>,
                    # {'box.mclean': ['O1234']}),
                # general_folder='./PHOENIX/GENERAL/StudyA/EXAMPLE',
                # protected_folder='./PHOENIX/PROTECTED/StudyA/EXAMPLE')

        assert subject.study == 'StudyA'
        assert subject.general_folder == './PHOENIX/GENERAL/StudyA/EXAMPLE'
        assert list(subject.xnat.keys())[0] == 'xnat.hcpep'
        assert list(subject.xnat.values())[0][0][0] == 'HCPEP-BWH'


