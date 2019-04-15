Lochness: Sync data from all over the cloud to a local directory
===============================================================
lochness provides a single command line tool (daemon) to periodically poll
and download data from various data archives into a local directory. Out of
the box there is support for pulling data from Beiwe, XNAT, REDCap, Dropbox,
external hard drives, and more, but extending lochness to support other services
is also [fairly simple](#extending-lochness) too.

lochness has been tested with Python 2.7 and 3 on macOS and Linux.

## Table of contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Setup](#setup)
4. [Basic usage](#basic-usage)
5. [Extending lochness](#extending-lochness)
6. [Usage for specific data archives](#usage-for-specific-data-archives)

## Installation
Just use `pip`

```bash
pip install lochness
```

The following will setup a conda environment with lochness and all of its
requirements:

```bash
conda create --name lochness-env python=3.7 six dropbox pyyaml paramiko requests
source activate lochness-env
pip install lochness
```

You'll also need a keyring and configuration file too. Keep reading.

## Setup

Connecting to various external data sources (Beiwe, XNAT, Dropbox, etc.) often
requires a myriad of connection details e.g., URLs, usernames, passwords, API
tokens, etc. Lochness will only read these pieces of information from an
encrypted JSON file that we refer to as the _keyring_. Here's an example of a
decrypted keyring file

```json
{
  "lochness": {
    "SECRETS": {
      "StudyA": "quick brown fox jumped over lazy dog"
    }
  },
  "beiwe.neuroinfo": {
    "URL": "https://beiwe.neuroinfo.org",
    "ACCESS_KEY": "...",
    "SECRET_KEY": "..."
  }
}
```

This file must be encrypted using a passphrase. At the moment, lochness only
supports encrypting and decrypting files using the
[cryptease](https://github.com/harvard-nrg/cryptease) library. This library
should be installed automatically when you install lochness, but you can
install it separately on any other machine as well. Here is how you would use
`cryptease` to encrypt the keyring file

```bash
$ crypt.py --encrypt ~/.lochness.json --output-file ~/.lochness.enc
```

I'll leave it up to you to decide on which device you want to encrypt this
file. I would recommend at least using a separate, secure
(e.g., not multi-tennant) computer/device and to immediately discard the
decrypted version. You should only ever need to move around the encrypted
version of this file.

### phoenix
lochness will download your data into a directory structure informally known as
PHOENIX. You can initialize the directory structure manually, or use the
`phoenix-generator.py` command line tool. Simply provide a study name using
the `-s|--study` argument and a filesystem location

```bash
phoenix-generator.py --study StudyA ./PHOENIX
```

The above command will generate the following directory tree

```bash
PHOENIX/
├── GENERAL
│   └── StudyA
│       └── StudyA_metadata.csv
└── PROTECTED
    └── StudyA
```

All file types that are not encrypted at rest by lochness will be saved under
the `GENERAL` folder and all encrypted file will be saved under the `PROTECTED`
folder.

Now let's talk about the `StudyA_metadata.csv` file, which is crucial.

### metadata files
The lochness command line tool `sync.py` is primarily driven off the PHOENIX
metadata files. These files are used to link each PHOENIX Subject ID to the
corresponding IDs found within each external data source. The metadata files
should be stored as plain `csv` under each PHOENIX study directory, as shown
above. The minimal contents of each metadata file should look like this

| Active | Subject ID | Consent    | Beiwe                        |
|--------|------------|------------|------------------------------|
|   1    | ABCDE      | 1970-01-01 | beiwe.neuroinfo:5e2311:abcde |
|   0    | VWXYZ      | 1972-12-01 | beiwe.neuroinfo:5e2311:vwxyz |

This document reflects that the PHOENIX Subject `ABCDE` has Beiwe data located
within the `beiwe.neuroinfo` Beiwe instance under the Study ID `5e2311` and
Participant ID `abcde`.

> Note that in the above case the connection details for `beiwe.neuroinfo` will
> be pulled from the encrypted [keyring file](#setup). Therefore it is very
> important that instance names used in a metadata file match a keyring index.

The metadata file can contain other columns as well, one column for each
external data source. The following data sources are supported out of the box

| Column Name   | General Format             | Example                           |
|---------------|----------------------------|-----------------------------------|
| Beiwe         | Instance:Project:ID        | beiwe.neuroinfo:5e2311:abcede     |
| XNAT          | Instance:Project:Subject   | xnat.xnatastic:myproject:abcde    |
| OnlineScoring | Instance:ID                | onlinescoring:abcde               |
| iCogniton     | Instance:ID                | mytimedtest:abcde                 |
| REDCap        | Instance:ID                | redcapdemo:abcde                  |
| Dropbox       | Instance:ID                | nrg:ABCDE                         |

Again, the `Instance` token shown above is used to lookup the connection details
credentials within the encrypted [keyring file](#setup). It is important to make
sure that the names match.

### configuration file
You start lochness using the `sync.py` command line tool. That tool uses a
configuration file which cuts down on the number of command line arguments
you need to memorize. An example configuration file is available within this
repository under `etc/config.yaml`. You must specify the path to your custom
configuration file using the `-c|--config` argument.

| Configuration keyword | What it does |
| --------------------- | ------------ |
| keyring_file          | (required) path to keyring file |
| phoenix_root          | (required) path to PHOENIX directory structure |
| ssh_user              | (optional?) Used for connecting to hdd (and maybe other things?) |
| ssh_host              | (optional?) Used for connecting to hdd (and maybe other things?) |
| sender                | (required?) Used to send email notifications: `smtplib.SMTP('localhost').sendmail(sender,...)` |
| beiwe                 | (optional) Section to configure beiwe options |
| dropbox               | (optional) Section to configure dropbox options by study |
| redcap                | (optional) Section to configure redcap options by study |
| admins                | (required?) Used to retrieve emails for notifications about lochness metadata errors or exceeded retry errors |
| notify                | (required?) Used to retrieve emails for notifications |

```yaml
notify:
  StudyA:
    username1@email.com
  StudyB:
    username2@email.com
  __global__:
    admin1@email.com
```

## Basic usage
Using the `sync.py` command line tool, data can be downloaded from various
sources. You can choose which sources by providing the `--source` argument

```bash
sync.py -c config.yml --source beiwe
```

You will be prompted for the password you used to encrypt the _keyring_ file.
You may also use the environment variable `NRG_KEYRING_PASS` to store the
encryption password.

Use `--help` to view additional sources, arguments, and other information

```bash
sync.py --help
```

## Extending lochness
If you look at one of the simpler modules e.g., `lochness/beiwe/__init__.py`
you will see that you only need to define a module containing a single `sync`
function that accepts three arguments: `Lochness`, `subject`, and `dry`

```python
import logging

logger = logging.getLogger(__name__)

def sync(Lochness, subject, dry=False):
  ...
```

You should assume that when lochness calls your module's `sync` function, the
`Lochness` argument will contain the user's keyring and all application
[configuration](#configuration-file), the `subject` argument will contain
everything parsed from the [metadata file](#metadata-files) for the current
subject, and the `dry` argument will contain wether or not the user passed
the `--dry` flag on the command line. You may want to use that parameter for
development and debugging purposes.

Once you've defined your own module, you need to import it and add it to the
`SOURCES` dict located within `sync.py`.

### helper functions
There are some general purpose helper functions at your disposal. The
`lochness` module contains functions such as `atomic_save` for saving files
without the risk of a partially written file, `lochness.net` contains a
decorator for automatically retrying a function call if an HTTP request raises
an exception, and `lochness.functools` contains a decorator for adding
memoization to a function that accepts mutable arguments.

## Usage for specific data archives

### Beiwe

For each beiwe instance you will pull data from, add the name of the beiwe
instance to the _keyring_ file. Under this section, add the keys described in
the [mano documentation: Initial setup](https://github.com/harvard-nrg/mano#initial-setup).

```json
{
  "beiwe.neuroinfo": {
    "URL": "https://beiwe.neuroinfo.org",
    "USERNAME": "...",
    "PASSWORD": "...",
    "ACCESS_KEY": "...",
    "SECRET_KEY": "..."
  }
}
```

You may add the flag `backfill_start` to the configuration file under the
`beiwe` section. Details about backfilling may be found in the
[mano documentation](https://github.com/harvard-nrg/mano#backfill).
If you do not add the flag, `backfill_start` defaults to 2015-10-01T00:00:00.

```yaml
beiwe:
  backfill_start: 2018-06-01T00:00:00
```

### XNAT

For each xnat instance you wish to pull data from, add the following to the
_keyring_ file:
 * its url
 * the username and password with access to the appropriate projects

```json
{
  "xnat.instance": {
    "URL": "https://xnatinstance.org",
    "USERNAME": "...",
    "PASSWORD": "..."
  }
}
```

No keys modifying XNAT data exist for the lochness configuration file.

### REDCap
For each study, add an entry in the _keyring_ under `lochness` in the `REDCAP`
section mapping the name of a redcap instance to a list of project names in that
REDCap instance to pull data from. Additionally, add an entry in the _keyring_
for each redcap instance with its url and one api token for each project in that
redcap instance.

```json
{
  "lochness": {
    "REDCAP": {
      "StudyA": {
        "redcapdemo": [
          "Project 1",
          "Project 2"
        ]
      }
    }
  },
  "redcapdemo": {
    "URL":"https://redcapdemo.url/redcap",
    "API_TOKEN": {
      "Project 1": "...",
      "Project 2": "..."
    }
  }
}
```

For each study, you may add an entry like the one below in the configuration
file indicating that data from REDCap should be deidentified before being
pulled. Not specifying this flag will result in all data being pulled from
REDCap, regardless of whether it contains PID.

```yaml
redcap:
  StudyA:
    deidentify: True
```

### Dropbox
Unfortunately, the process lochness uses to download data from Dropbox is the most complicated. 5 possible names for dropbox instances exist: `dropbox.baker`, `dropbox.cbsn`, `dropbox.mclean`, `dropbox.multisense`, and `dropbox.nrg`. Each name is associated with a module in `lochness.dropbox`. These modules define `sync` functions and should be consulted for the appropriate Dropbox folder structure. Note that a lochness project may have any subset (including the empty set) of the 5 possible names.

For each dropbox instance, add a section containing `API_TOKEN` to the _keyring_ file. I also strongly suggest adding user and description entries indicating whether the API token is associated with an app or the home directory.

```json
{
  "dropbox.mclean": {
    "API_TOKEN": "...",
    "user": "sguthrie",
    "description": "home folder"
  }
}
```

For each dropbox instance, you may add the flag `delete_on_success` to indicate
the data from Dropbox should be deleted from Dropbox after it has been
downloaded and its `content_hash` has been checked to be the same as the Dropbox
`content_hash`. By default, `delete_on_success` is set to False. This feature is
useful if the user wishes to save space on Dropbox. For each study, you may also
add the flag `base`, which is prepended to the path searched for data in for
`dropbox.cbsn` and `dropbox.mclean`. I believe that the `base` flag will not
have any effect for dropbox instances `dropbox.baker`, `dropbox.multisense`, and
`dropbox.nrg`.

```yaml
dropbox:
  mclean:
    base: /PHOENIX_PULL
    delete_on_success: True
```
