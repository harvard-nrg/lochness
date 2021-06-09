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

For the most recent DPACC-lochness install and debugging, see `Installation
<../../README.md#installation>`_.


Setup from a template
------------
See `Setup from a template
<../..//README.md#Setup-from-a-template>`_.


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

