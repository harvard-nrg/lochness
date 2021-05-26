import lochness
from pathlib import Path
from lochness.keyring import print_keyring

import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from test_lochness import Lochness

def test_read_phoenix_data(Lochness):
    print_keyring(Lochness)
