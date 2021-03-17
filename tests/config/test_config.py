import lochness.config
import tempfile
import lochness.box.mclean as box_mclean
import re
import string

def create_config():
    config_string = b'''keyring_file: ~/.lochness.enc
phoenix_root: ~/PHOENIX
pid: /tmp/lochness.pid
stderr: /tmp/lochness.stderr
stdout: /tmp/lochness.stdout
poll_interval: 86400
ssh_user: kc244
ssh_host: rgs09.research.partners.org
sender: kevincho@bwh.harvard.edu
beiwe:
    backfill_start: 2017-10-01T00:00:00
box:
    mclean: 
        base: codmtg
        delete_on_success: False
        file patterns: 
            actigraphy: 
                   - vendor: Philips
                     product: Actiwatch 2
                     pattern:  '.*\.csv'
                   - vendor: Activinsights
                     product: GENEActiv
                     pattern:  'GENEActiv/.*(\.csv|\.bin)'
                     compress:  True
            mri_eye:
                   - vendor: SR Research
                     product: EyeLink 1000
                     pattern: '.*\.mov'
            behav_qc:
                   - vendor: CNL Lab
                     product: unknown
                     pattern: '.*'
            physio:
                   - vendor: BIOPAC
                     product: AcqKnowledge
                     pattern: '.*\.acq'
            offsite_interview:
                   - vendor: Zoom
                     product: ZoomVideoConference
                     pattern: '.*/zoom_0\.mp4'
                     protect: True
            onsite_interview:
                   - vendor: Amir Zadeh (CMU)
                     product: Recorder.exe
                     pattern: '.*'
                     protect: True
                   - vendor: Zoom
                     product: unknown
                     pattern: '.*(\.MOV|\.WAV)$'
                     protect: True
    otherStudy: 
        base: codmtg2
        delete_on_success: False
        file patterns: 
            actigraphy: 
                   - vendor: Philips
                     product: Actiwatch 2
                     pattern:  '.*\.csv'
                   - vendor: Activinsights
                     product: GENEActiv
                     pattern:  'GENEActiv/.*(\.csv|\.bin)'
                     compress:  True
redcap:
    phoenix_project:
        deidentify: True
hdd:
    module_name:
        base: /PHOENIX
admins:
    - kevincho@bwh.harvard.edu
notify:
    __global__:
        - kevincho@bwh.harvard.edu


'''
    fp = tempfile.TemporaryFile()

    fp.write(config_string)
    fp.seek(0)
    return config_string, fp


def test_return_box_patterns_str_template():
    '''Test including the box file patterns in the config.yaml'''
    config_string, fp = create_config()
    cfg = lochness.config._read_config_file(fp)

    if 'box' in cfg.keys():
        print(cfg['box'])
        for example_study_name, example_study_dict in cfg['box'].items():
            print(example_study_name)
            example_study_dict['file patterns'] = \
                    lochness.config._return_box_patterns_str_template(
                        example_study_dict['file patterns'])

            for var in example_study_dict['file patterns'].keys():
                config_example = example_study_dict\
                        ['file patterns'][var][0]['pattern'].template
                orig_example = box_mclean.CONFIG[var][0]['pattern'].template
                assert config_example == orig_example
                print('pass')

