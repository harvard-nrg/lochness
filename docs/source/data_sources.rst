Data sources
============
Lochness supports pulling data from a number of data sources. This page will 
show you how to configure these data sources both in the `keyring <quick_start.html#setup>`_ 
and in the PHOENIX `metadata files <phoenix.html#metadata-files>`_.

Beiwe
-----
For each Beiwe instance you will be pulling data from, add a new connection 
details section to the root of your ``keyring``. This name of this section 
can be whatever you like as long as it is valid JSON. Under your new section, 
you must add the ``URL``, ``ACCESS_KEY``, and ``SECRET_KEY`` fields ::

    {
      "beiwe.example": {
        "URL": "https://beiwe.example.org",
        "ACCESS_KEY": "...",
        "SECRET_KEY": "..."
      }
    }

metadata file entry
~~~~~~~~~~~~~~~~~~~
A valid metadata file entry for ``Beiwe`` should look as follows ::

    Active,...,Beiwe,...
    1,...,beiwe.example:STUDY:SUBJECT,...

The ``beiwe.example`` should be a valid ``keyring`` section name, ``STUDY`` 
should be the first few characters from the 24-character Study ID, and 
``SUBJECT`` should be a valid Beiwe subject.

.. attention::
   The ``STUDY`` component of the Beiwe metadata file entry should be the 
   Study ID, **not** the Study Name. You do not need to enter all 24 
   characters of the Study ID either. You only need enough characters 
   (e.g., the first 5 or so) to make it uniquely identifiable.

backfilling
~~~~~~~~~~~
There is always the chance that you're deploying Lochness well after you've 
started capturing data with Beiwe. Lochness will not attempt to download 
*all* of your data in one enormous payload. That could be on the order of 
many gigabytes and you will likely run into issues. Instead, Lochness will 
request your data in day or week-sized chunks from some starting point up to 
the current date. This process is called *backfilling*.

While Lochness will politely download your data in these digestible chunks, 
one detail it cannot easily predict is what date to start the backfill. The 
user is expected to set this using the ``backfill_start`` field within the 
Lochness configuration file. Please refer to the 
configuration file `backfill_start documentation <configuration_file.html#backfill-start>`_ 
for more details.

REDCap
------
To have Lochness download data from REDCap, you need a few things.

redcap keyring section
~~~~~~~~~~~~~~~~~~~~~~
First you need to create a section at the root of your ``keyring`` for your 
REDCap connection details. You can name this section whatever you like as 
long as it is valid JSON. Within this section you'll need to add a ``URL`` 
field and a subsection named ``API_TOKEN`` where you will store all of your 
REDCap Project API tokens ::

    {
      "redcap.demo": {
        "URL": "https://redcap.demo.org",
          "API_TOKEN": {
            "Project 1": "...",
            "Project 2": "..."
          }
      }
    }

.. note::
   To generate a REDCap Project API Token, use the ``API`` section under your
   REDCap Project Settings page. You must generate an API Token for each 
   project.

lochness keyring subsection
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Within the ``keyring`` file, add a ``REDCAP`` subsection to the primary 
``lochness`` section ::

    {
      "lochness": {
        "REDCAP": {
        }
    }

Within this new ``REDCAP`` section, add a subsection for each PHOENIX 
study name. In the following example, we'll assume the study name is 
``StudyA`` ::

    {
      "lochness": {
        "REDCAP": {
          "StudyA": {
          }
        }
      }
    }

Within the new ``StudyA`` section, create yet another section with the 
name of your REDCap keyring section (e.g., ``redcap.example``) followed 
by a list of REDCap projects you want Lochness to search and pull data 
from ::

    {
      "lochness": {
        "REDCAP": {
          "StudyA": {
            "redcap.example": [
              "Project 1",
              "Project 2"
            ]
          }
        }
      }
    }

metadata file entry
~~~~~~~~~~~~~~~~~~~
A valid metadata file entry should look as follows ::

    Active,...,REDCap,...
    1,...,redcap.example:SUBJECT,...

Where ``redcap.example`` would be a valid ``keyring`` section and ``SUBJECT`` 
would be a valid REDCap subject.

de-identification
~~~~~~~~~~~~~~~~~
For each PHOENIX study, you may add an entry to the Lochness configuration 
file indicating that data from REDCap should be *de-identified* before being
saved to the filesystem. Please refer to the 
`redcap configuration file documentation <configuration_file.html#redcap>`_  
for more details.

XNAT
----
For each XNAT instance you wish to pull data from, add a new connection 
details section to the root of your ``keyring``. The name of this section 
can be whatever you like as long as it's valid JSON. Within your new section, 
add the ``URL``, ``USERNAME``, and ``PASSWORD`` fields ::

    {
      "xnat.example": {
        "URL": "https://xnat.example.org",
        "USERNAME": "...",
        "PASSWORD": "..."
      }
    }

metadata file entry
~~~~~~~~~~~~~~~~~~~
A valid metadata file entry should look as follows ::

    Active,...,XNAT,...
    1,...,xnat.example:PROJECT:SUBJECT,...

Where ``xnat.example`` would be a valid ``keyring`` section, ``PROJECT`` would 
be a valid XNAT project, and ``SUBJECT`` would be a valid XNAT Subject.

.. attention::
   The ``SUBJECT`` component of this metadata entry should be a valid XNAT 
   Subject, not just a MR Session. All MR Sessions for that XNAT Subject 
   will be downloaded. 

Dropbox
-------
To have Lochness download data automatically from Dropbox, you need a few
things.

create access token
~~~~~~~~~~~~~~~~~~~
First, you need to create an Access Token using the
`Dropbox App Console <dropbox.com/developers/apps>`_. The token should be a
64-character alphanumeric string.

create keyring section
~~~~~~~~~~~~~~~~~~~~~~
Next, you need to create a new ``keyring`` section for your Dropbox instance. 
This section must be named ``dropbox.xxxxx`` where ``xxxxx`` can be any 
string that is both valid JSON *and* valid as a Python module name. Behind the 
scenes, Lochness will use this string to import a module. Within your new 
section, you must add your Dropbox Acsess Token to an ``API_TOKEN`` field ::

    {
      "dropbox.xxxxx": {
        "API_TOKEN": "..."
      }
    }

metadata file entry
~~~~~~~~~~~~~~~~~~~
A valid metadata file entry should look as follows ::

    Active,...,Dropbox,...
    1,...,dropbox.xxxxx:SUBJECT,...

Where ``dropbox.example`` would be a valid ``keyring`` section and ``SUBJECT`` 
would be a valid Subject folder name in Dropbox. This folder name does not 
necessarily have to match the PHOENIX subject.

delete on success
~~~~~~~~~~~~~~~~~
You can configure Lochness to delete files from Dropbox on successful download. 
For details, please refer to the 
`dropbox delete_on_success configuration file documentation <configuration_file.html#delete-on-success>`_

dropbox base
~~~~~~~~~~~~
You can configure Lochness to begin searching your Dropbox account starting from 
a specific subdirectory. For details, please refer to the
`dropbox base configuration file documentation <configuration_file.html#dropbox-base>`_.


Box
-------
To have Lochness download data automatically from Box, you need a few
things.

create access token
~~~~~~~~~~~~~~~~~~~
First, you need to get CLIENT_ID, CLIENT_SECRET and API Access Token from the 
app created on the `https://app.box.com/developers/console`. The token should be a
32-character alphanumeric string.

create keyring section
~~~~~~~~~~~~~~~~~~~~~~
Next, you need to create a new ``keyring`` section for your Box instance. 
This section must be named ``box.xxxxx`` where ``xxxxx`` can be any 
string that is both valid JSON *and* match `box` column values in the
metadata.csv. 
Behind the scenes, Lochness will use this string to import a module from 
`lochness.box`. Within your new section, you must add your Box CLIENT_ID,
CLIENT_SECRET and API_TOKEN  ::

    {
      "box.xxxxx": {
        "CLIENT_ID": "...",
        "CLIENT_SECRET": "...",
        "API_TOKEN": "..."
        }
    }

metadata file entry
~~~~~~~~~~~~~~~~~~~
A valid metadata file entry should look as follows ::

    Active,...,Box,...
    1,...,box.xxxxx:SUBJECT,...

Where ``box.xxxxx`` would be a valid ``keyring`` section and ``SUBJECT`` 
would be a valid Subject folder name in Box. This folder name does not 
necessarily have to match the PHOENIX subject.

delete on success
~~~~~~~~~~~~~~~~~
You can configure Lochness to delete files from Box on successful download. 
For details, please refer to the 
`box delete_on_success configuration file documentation <configuration_file.html#delete-on-success>`_

box base
~~~~~~~~~~~~
You can configure Lochness to begin searching your Box account starting from 
a specific subdirectory. For details, please refer to the
`box base configuration file documentation <configuration_file.html#box-base>`_.
