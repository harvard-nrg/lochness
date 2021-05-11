Quick start
===========
Lochness provides a single command line tool (daemon) to periodically poll
and download data from various web services into a local directory. Out of
the box there is support for pulling data from a multitude of 
`data sources <data_sources.html>`_ including Beiwe, XNAT, REDCap, 
Dropbox, Box, Mediaflux, Daris, RPMS, external hard drives, and more.



Installation
------------
Just use ``pip`` ::

    pip install lochness


or for most recent DPACC-lochness ::

    pip install git+https://github.com/PREDICT-DPACC/lochness


for debugging ::

    cd ~
    git clone https://github.com/PREDICT-DPACC/lochness
    export PATH=${PATH}:~/lochness/scripts  # add to ~/.bashrc
    export PYTHONPATH=${PYTHONPATH}:~/lochness  # add to ~/.bashrc




Setup from a template
---------------------

Creating the template
~~~~~~~~~~~~~~~~~~~~~
Setting up lochness from scratch could be slightly confusing in the beginning.
Try using the `lochness_create_template.py` to create a starting point.

Create an example template to easily structure the lochness system ::

    # PREDICT
    lochness_create_template.py \
        --outdir /data/lochness_root \
        --studies BWH McLean \
        --sources redcap xnat box mindlamp \
        --email kevincho@bwh.harvard.edu \
        --poll_interval 43200 \
        --ssh_host erisone.partners.org \
        --ssh_user kc244

    # PRESCIENT
    lochness_create_template.py \
        --outdir /data/lochness_root \
        --studies BWH McLean \
        --sources RPMS daris mediaflux mindlamp \
        --email kevincho@bwh.harvard.edu \
        --poll_interval 43200 \
        --ssh_host erisone.partners.org \
        --ssh_user kc244 

    # For more options: lochness_create_template.py -h


Making edits to the template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Running one of the commands above will create the structure below ::

    /data/lochness_root/
    ├── 1_encrypt_command.sh
    ├── 2_sync_command.sh
    ├── PHOENIX
    │   ├── GENERAL
    │   │   ├── BWH
    │   │   │   └── BWH_metadata.csv
    │   │   └── McLean
    │   │       └── McLean_metadata.csv
    │   └── PROTECTED
    │       ├── BWH
    │       └── McLean
    ├── config.yml
    ├── lochness.json
    └── pii_convert.csv



1. Change information in `config.yml` and `lochness.json` as needed.


2. Either manually update the `PHOENIX/GENERAL/*/*_metadata.csv` or
   amend the field names in REDCap / RPMS sources correctly for lochness to
   automatically update the metadata files.

   Currently, lochness initializes the metadata using the following field names 
   in REDCap and RPMS. ::

   - `record_id1`: the record ID field name
   - `Consent`: the field name of the consent date
   - `beiwe_id`: the field name of the BEIWE ID.
   - `xnat_id`: the field name of the XNAT ID.
   - `dropbox_id`: the field name of the Dropbox ID.
   - `box_id`: the field name of the Box ID.
   - `mediaflux_id`: the field name of the Mediaflux ID.
   - `mindlamp_id`: the field name of the Mindlamp ID.
   - `daris_id`: the field name of the DaRIS ID.
   - `rpms_id`: the field name of the RPMS ID.


3. Encrypt the `lochness.json` by running ::

   bash 1_encrypt_command.sh


This encryption step creates a copy of encrypted keyrings to
`/data/lochness_root/.lochness.enc`. To protect the sensitive keyring
information in json, remove the `lochness.json` after running the encryption.


You can still extract keyring structure without sensitive information by running ::

   lochness_check_config.py -ke /data/lochness_root/.lochness.enc
   

4. Set up REDCap Data Entry Trigger if using REDCap. Please see below 
   "REDCap Data Entry Trigger capture" section.


5. Edit Personally identifiable information mapping table. Please seee below
   "Personally identifiable information removal from REDCap and RPMS data"::

    `/data/lochness_root/pii_convert.csv`


5. Run the `sync.py` or use the example command in `2_synch_command.sh`::

   bash 2_sync_command.sh


REDCap Data Entry Trigger capture
---------------------------------
If your sources include REDCap and you would like to configure lochness to 
only pull new REDCap data, "Data Entry Trigger" needs to be set up in REDCap.

In REDCap,
- "Project Setup"
- "Enable optional modules and customizations"
- "Additional customizations"
- check "Data Entry Trigger" and give address of the server including the port number. eg) http://pnl-t55-7.partners.org:9999


In order to use this functionality, the server where lochness is installed
should be able to receieve HTTP POST signal from REDCap server. Which means it
has to be either

- lochness server is inside the same firewall as REDCap server.
    Or
- lochness server has a open port that could listen to the REDCap POST signal.


After setting the "Data Entry Trigger" on REDCap settings, run below to update
the `/data/data_entry_trigger_db.csv` real-time::

    # please specify the same port defined in the REDCap settings
    listen_to_redcap.py --database_csv /data/data_entry_trigger_db.csv \
                        --port 9999


It would be useful to run `listen_to_redcap.py` in background, maybe inside a
`gnu screen` so it runs continuously without interference.



Personally identifiable information removal from REDCap and RPMS data
----------------------------------------------------------------------
A path of csv file can be provided, which has information about how to process
each PII fields. 

For example::

    #/data/personally_identifiable_process_mappings.csv

    pii_label_string | process
    -----------------|---------------
    address          | remove
    date             | change_date
    phone_number     | random_number
    patient_name     | random_string
    subject_name     | replace_with_subject_id

Any value from the field, with names that match to `pii_label_string` rows,
the labelled **PII processing method** will be used to process the raw values
to remove or replace the PIIs.



Manual Setup
------------
Connecting to various external `data sources <data_sources.html>`_
(Beiwe, XNAT, Dropbox, etc.) often requires a myriad of connection details 
e.g., URLs, usernames, passwords, API tokens, etc. Lochness will only read 
these pieces of information from an encrypted JSON file that we refer to as 
the *keyring*. Here's an example of a decrypted keyring file ::

    {
      "lochness": {
        "SECRETS": {
          "StudyA": "quick brown fox jumped over lazy dog"
        }
      },

      "beiwe.example": {
        "URL": "https://beiwe.example.org",
        "ACCESS_KEY": "...",
        "SECRET_KEY": "..."
      },

      "xnat.example": {
        "URL": "https://chpe-xnat.example.harvard.edu",
        "USERNAME": "...",
        "PASSWORD": "..."
      },

      "box.example": {
        "CLIENT_ID": "...",
        "CLIENT_SECRET": "...",
        "API_TOKEN": "..."
      },

      "mediaflux.example": {
        "HOST": "mediaflux.researchsoftware.unimelb.edu.au",
        "PORT": "443",
        "TRANSPORT": "https",
        "TOKEN": "...",
        "DOMAIN": "...",
        "USER": "...",
        "PASSWORD": "..."
      },

      "mindlamp.example": {
        "URL": "...",
        "ACCESS_KEY": "...",
        "SECRET_KEY": "..."
      },

      "daris.example": {
        "URL": "...",
        "TOKEN": "...",
        "PROJECT_CID": "..."
      },

      "rpms.example": {
        "RPMS_PATH": "..."
      }
    }


This file must be encrypted using a passphrase. At the moment, Lochness only
supports encrypting and decrypting files (including the keyring) using the
`cryptease <https://github.com/harvard-nrg/cryptease>`_ library. This library
should be installed automatically when you install Lochness, but you can
install it separately on another machine as well. Here is how you would use
``cryptease`` to encrypt the keyring file ::

    crypt.py --encrypt ~/.lochness.json --output-file ~/.lochness.enc

.. attention::
   I'll leave it up to you to decide on which device you want to encrypt this
   file. I will only recommend discarding the decrypted version as soon as 
   possible.


PHOENIX
~~~~~~~
Lochness will download your data into a directory structure informally known as
PHOENIX. For a detailed overview of PHOENIX, please read through the 
`PHOENIX documentation <phoenix.html>`_. You need to initialize the directory structure 
manually, or by using the provided ``phoenix-generator.py`` command line tool that will 
be installed with Lochness. To use the command line tool, simply provide a study name 
using the ``-s|--study`` argument and a base filesystem location ::

    phoenix-generator.py --study StudyA ./PHOENIX

The above command will generate the following directory tree ::

    PHOENIX/
    ├── GENERAL
    │   └── StudyA
    │       └── StudyA_metadata.csv
    └── PROTECTED
        └── StudyA


Basic usage
-----------
The primary command line utility for Lochness is ``sync.py``. When you invoke this 
tool, you will be prompted for the passphrase that you used to encrypt your 
`keyring <#setup>`_. To sidestep the password prompt, you can use an environment 
variable ``NRG_KEYRING_PASS``.


metadata files
~~~~~~~~~~~~~~
The ``sync.py`` tool is driven largely off the PHOENIX metadata files. For an 
in-depth look at these metadata files, please read the 
`metadata files section <phoenix.html#metadata-files>`_ from the PHOENIX documentation.


configuration file
~~~~~~~~~~~~~~~~~~
Before you can successfully run ``sync.py``, you need to provide the location 
to a configuration file using ``-c|--config`` ::

    sync.py -c /path/to/config.yaml

There is an example configuration file within the Lochness repository under 
``etc/config.yaml``. To learn more about what each configuration option 
means, please read the `configuration file documentation <configuration_file.html>`_.


data sources
~~~~~~~~~~~~
By default, Lochness will download data from *all* supported data sources. If 
you want to restrict Lochness to only download specific data sources, you can 
provide the ``--source`` argument ::

    sync.py -c config.yml --source beiwe
    sync.py -c config.yml --source xnat box


additional help
~~~~~~~~~~~~~~~
To see all of the command line arguments available, use the ``--help`` argument ::

    sync.py --help

