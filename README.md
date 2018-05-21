Lochness: Sync data from all over the cloud to a local directory
===============================================================
lochness provides a single command line tool (daemon) to periodically poll 
and download data from various data archives into a local directory. Out of 
the box there is support for pulling data from Beiwe, XNAT, REDCap, Dropbox, 
external hard drives, and more, but extending lochness to support other services 
is also [fairly simple](#extending-lochness) too.

## Table of contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Setup](#setup)
4. [Basic usage](#basic-usage)
5. [Extending lochness](#extending-lochness)

## Requirements
lochness has been tested with Python 2.7 and 3 on macOS and Linux.

## Installation
Just use `pip`

```bash
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
PHOENIX. lochness ships with a simple command line tool `phoenix-generator.py` 
that can help you initialize the directory structure. For example, running the 
following command

```bash
phoenix-generator.py -s StudyA ./PHOENIX
```

will generate the following directory structure

```bash
PHOENIX/
├── GENERAL
│   └── StudyA
│       └── StudyA_metadata.csv
└── PROTECTED
    └── StudyA
```

All file types that are not encrypted by lochness at rest will be saved under 
the `GENERAL` folder and all encrypted file types will be saved under the 
`PROTECTED` folder.

Next, let's talk about the `StudyA_metadata.csv` file.

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

## Basic usage
Using the `sync.py` command line tool, data can be downloaded from various 
sources. You can choose which sources by providing the `--source` argument

```bash
sync.py -c config.yml --source beiwe
```

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

