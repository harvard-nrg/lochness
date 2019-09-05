The PHOENIX filesystem
======================
This guide is a description of the PHOENIX filesystem, not necessarily that of any 
particular software implementation that produces a PHOENIX filesystem.

GENERAL and PROTECTED folders
-----------------------------
At the root level of the PHOENIX file system, there are two subdirectories ``GENERAL`` and
``PROTECTED`` :: 

    PHOENIX
    ├── GENERAL
    └── PROTECTED

Data that are not encrypted at rest are stored under the ``GENERAL`` folder. Data that 
are encrypted at rest are stored under the ``PROTECTED`` folder.

.. note:: 
   Types of data that are encrypted at rest tend to include gps, onsite interviews, and 
   voice recordings.

Study folders
-------------
Under the ``GENERAL`` and ``PROTECTED`` folders are ``STUDY`` folders ::

    PHOENIX
    ├── GENERAL
    │   └── STUDY_A
    └── PROTECTED
        └── STUDY_A

.. note::
   Study folders should contain only letters, numbers, and underscores ``[A-Za-z0-9_]``.

study folder permissions
~~~~~~~~~~~~~~~~~~~~~~~~
Each ``STUDY`` folder is assigned the default permissions ``rwx------``. Individual user 
permissions are then added using POSIX.1e access control lists. To add read (``ls``) and 
execute (``cd``) permissions on the ``STUDY_A`` folder for user ``jdoe`` you would issue 
the following command ::

    setfacl -m u:jdoe:rx /PHOENIX/GENERAL/STUDY_A /PHOENIX/PROTECTED/STUDY_A

.. warning::
   Many but not all filesystems support POSIX.1e access control lists. For example, 
   some versions of `PANASAS <https://www.panasas.com>`_ do not support them at all, 
   while other filesystems, such as NFSv4, may use different tools and/or a modified 
   syntax than shown above.

Subject folders
---------------
Within each ``STUDY`` folder are individual ``SUBJECT`` folders. Subject names should be 
unique across PHOENIX ::

    PHOENIX
    ├── GENERAL
    │   └── STUDY_A
    │       └── SUBJECT_1
    └── PROTECTED
        └── STUDY_A
            └── SUBJECT_1

.. warning::
   While subject names *should* be unique across PHOENIX, this is not enforced 
   by Lochness in any way.

.. note::
   Subject names should contain only letters, numbers, and underscores ``[A-Za-z0-9_]``.    

Data type folders
-----------------
Within each ``SUBJECT`` folder, there are folders for each ``DATA TYPE`` ::

    PHOENIX
    ├── GENERAL
    │   └── STUDY_A
    │       └── SUBJECT_1
    │           └── DATA_TYPE
    └── PROTECTED
        └── STUDY_A
            └── SUBJECT_1
                └── DATA_TYPE

Some example ``DATA TYPE`` names include ``actigraphy``, ``mri``, ``phone``, and 
``surveys``.

.. note::
   Data type names should contain only letters, numbers, and underscores ``[A-Za-z0-9_]``.

Raw and processed folders
-------------------------
Within each ``DATA TYPE`` folder, there are folders for ``raw`` and ``processed`` 
data ::

    PHOENIX
    ├── GENERAL
    │   └── STUDY_A
    │       └── SUBJECT_1
    │           └── DATA_TYPE
    │               ├── raw
    │               └── processed
    └── PROTECTED
        └── STUDY_A
            └── SUBJECT_1
                └── DATA_TYPE
                    ├── raw
                    └── processed

raw
~~~
The ``raw`` folders are the bedrock of the PHOENIX filesystem. These folders are 
typically populated by data aggregation software. The user designated to run the 
data aggregation software should be the *only user* with write permissions on 
these folders. All other users should be granted **read-only** permissions.

processed
~~~~~~~~~
The ``processed`` folders are assigned the permissions ``rwxrwxrwxt`` which allows 
any user who has been granted access to the parent ``STUDY`` folder to write files. 
Because these folders use a `sticky bit <https://en.wikipedia.org/wiki/Sticky_bit>`_, 
only the owner of a file will be allowed to edit or delete their own files.

.. note::
   Folders must be named ``raw`` and ``processed`` in lowercase letters.

Product folders (optional)
--------------------------
Within each ``raw`` folder, there may be folders for each data capturing ``PRODUCT``. 
This allows for multiple data capturing products, which happen to capture the same 
*type* of data, to be clearly differentiated ::

    PHOENIX
    ├── GENERAL
    │   └── STUDY_A
    │       └── SUBJECT_1
    │           └── DATA_TYPE
    │               └── raw
    │                   └── PRODUCT
    │
    └── PROTECTED
        └── STUDY_A
            └── SUBJECT_1
                └── DATA TYPE
                    └── raw
                        └── PRODUCT

Some product names include ``Actiwatch2`` and ``GENEActiv``.

.. note::
   Product names should contain only letters, numbers, and underscores ``[A-Za-z0-9_]``.

Raw file integrity
------------------
As ``raw`` files are being downloaded from each data source, the file contents are stored 
within `hidden files <https://en.wikipedia.org/wiki/Hidden_file_and_hidden_directory>`_. 
These hidden files should be **ignored** by end users. The file will be renamed to a 
visible file name only after the file has been considered downloaded successfully. If the 
file contents can be verified using a checksum, numbers of bytes, or by some other means, 
the file will be verified before it is made visible.

Raw file naming convention
--------------------------
As a general rule, files will **always** preserve their original names or they will be assigned 
a name provided by the originating data source. Instances where a file name is not provided by 
the originating data source, an appropriately descriptive file name will be automatically 
generated.

Metadata files
--------------
In PHOENIX, all data for a subject are downloaded and organized under unique ``SUBJECT`` 
folders. To accomplish this, the data aggregation software must understand how to query 
for data belonging to the ``SUBJECT`` within each data source. This is achieved using 
``metadata files``. Each ``STUDY`` folder must contain a metadata file ::

    PHOENIX
    └── GENERAL
        └── STUDY_A
            └── STUDY_A_metadata.csv

The metadata file should be named with the study name followed by a ``_metadata.csv``
suffix. The data aggregator is largely driven off these PHOENIX metadata files. The 
minimal contents of a metadata file should look like this ::

    Active,Subject ID,Consent Date
    1,SUBJECT_1,2019-01-01

For convenience, here's the same file rendered as a table

+--------+------------+------------+
| Active | Subject ID | Consent    |
+========+============+============+
|   1    | SUBJECT_1  | 2019-01-01 |
+--------+------------+------------+

You must add additional columns to this file for each `supported data source <data_sources.html>`_ 
that you wish to pull data from.

.. seealso::
   You can read much more about the supported data sources on the 
   `data sources page <data_sources.html>`_.

For the sake of brevity, let's see what a metadata file looks like when we 
add a ``Beiwe`` column

+--------+------------+------------+----------------------------+
| Active | Subject ID | Consent    | Beiwe                      |
+========+============+============+============================+
|   1    | SUBJECT_1  | 2019-01-01 | beiwe.example:5e2311:abcde |
+--------+------------+------------+----------------------------+

This instructs the data aggregator that ``SUBJECT_1`` should have data in the 
Beiwe instance ``beiwe.example``, under the study ``5e2311``, under the patient 
``abcde``.

