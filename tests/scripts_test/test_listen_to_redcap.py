import lochness

from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

import listen_to_redcap


# from lochness.redcap.data_trigger_capture import save_post_from_redcap
# from lochness.redcap.data_trigger_capture import back_up_db

# def test_save_post_from_redcap():
    # text_body = "redcap_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2F&project_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2Fredcap_v10.0.30%2Findex.php%3Fpid%3D26709&project_id=26709&username=kc244&record=1001_1&instrument=inclusionexclusion_checklist&inclusionexclusion_checklist_complete=0"
    # save_post_from_redcap(text_body, 'ha.csv')


# def test_save_post_from_redcap_no_redcap_post():
    # text_body = "hahahoho"
    # if 'redcap' in text_body:
        # save_post_from_redcap(text_body, 'ha.csv')
    # else:
        # print('no redcap post')

# def test_back_up_db():
    # back_up_db('ha.csv')
    # text_body = "redcap_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2F&project_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2Fredcap_v10.0.30%2Findex.php%3Fpid%3D26709&project_id=26709&username=kc244&record=1001_1&instrument=inclusionexclusion_checklist&inclusionexclusion_checklist_complete=0"
    # save_post_from_redcap(text_body, 'ha.csv')

    # back_up_db('ha.csv')

# # if __name__ == '__main__':
    # # from sys import argv

    # # if len(argv) == 2:
        # # run(port=int(argv[1]))
    # # else:
        # # run()
