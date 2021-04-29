Mediaflux and lochness
----------------------

This documentation discusses how to organize data under a Mediaflux namespace and how they can be downloaded
by `lochness` module. In a nutshell:

* Individual sites will upload their data to Mediaflux following a predefined structure
* The central controller of those sites will need to install `lochness` module and generate a folder hierarchy to 
pull their data from Mediaflux
* Some Mediaflux login credentials, the predefined structure, and the folder hierarchy are defined via three files--
keyring, configuration, and metadata

**NOTE** Click on any arrow you find in this document to see their content.

<details><summary></summary>

`How's your day going? Thanks anyway!`

</details>

**NOTE** `STUDY` and `SITE` words are used interchangeably in this document.

Table of Contents
=================

  * [Mediaflux and lochness](#mediaflux-and-lochness)
  * [Mediaflux remote](#mediaflux-remote)
  * [Install lochness](#install-lochness)
  * [Generate PHOENIX directory](#generate-phoenix-directory)
  * [Configuration file](#configuration-file)
  * [Keyring file](#keyring-file)
  * [Metadata file](#metadata-file)
  * [Appendix](#appendix)


---

Mediaflux remote
----------------

In the following, we show how data should be organized in Mediaflux remote so `lochness` module recognizes them 
and can download them. A user can upload data only under a namespace in Mediaflux. The top level directory is the 
namespace. After that, each site should have a folder where all its data can be stored:

```
namespace/
├── SITE_A
│   ├── datatype_1
│   │   ├── sub001
│   │   │   ├── hello.csv
│   │   │   ├── pattern_1
│   │   │   │   └── anything
│   │   │   │       ├── everything.csv
│   │   │   │       ├── nothing.txt
│   │   │   │       └── something.bin
│   │   │   └── pattern_2
│   │   │       ├── everything.csv
│   │   │       ├── nothing.txt
│   │   │       └── something.bin
│   │   └── sub002
│   │       ├── hello.csv
│   │       ├── pattern_1
│   │       │   └── anything
│   │       │       ├── everything.csv
│   │       │       ├── nothing.txt
│   │       │       └── something.bin
│   │       └── pattern_2
│   │           ├── everything.csv
│   │           ├── nothing.txt
│   │           └── something.bin
│   └── datatype_2
│       ├── sub001
│       │   ├── hello.csv
│       │   ├── pattern_1
│       │   │   └── anything
│       │   │       ├── everything.csv
│       │   │       ├── nothing.txt
│       │   │       └── something.bin
│       │   └── pattern_2
│       │       ├── everything.csv
│       │       ├── nothing.txt
│       │       └── something.bin
│       └── sub002
│           ├── hello.csv
│           ├── pattern_1
│           │   └── anything
│           │       ├── everything.csv
│           │       ├── nothing.txt
│           │       └── something.bin
│           └── pattern_2
│               ├── everything.csv
│               ├── nothing.txt
│               └── something.bin
```
<details><summary>└── SITE_B</summary>

```
    ├── datatype_1
    │   ├── sub001
    │   │   ├── pattern_1
    │   │   │   └── anything
    │   │   │       ├── everything.csv
    │   │   │       ├── nothing.txt
    │   │   │       └── something.bin
    │   │   └── pattern_2
    │   │       ├── everything.csv
    │   │       ├── nothing.txt
    │   │       └── something.bin
    │   └── sub002
    │       ├── pattern_1
    │       │   └── anything
    │       │       ├── everything.csv
    │       │       ├── nothing.txt
    │       │       └── something.bin
    │       └── pattern_2
    │           ├── everything.csv
    │           ├── nothing.txt
    │           └── something.bin
    └── datatype_2
        ├── sub001
        │   ├── pattern_1
        │   │   └── anything
        │   │       ├── everything.csv
        │   │       ├── nothing.txt
        │   │       └── something.bin
        │   └── pattern_2
        │       ├── everything.csv
        │       ├── nothing.txt
        │       └── something.bin
        └── sub002
            ├── pattern_1
            │   └── anything
            │       ├── everything.csv
            │       ├── nothing.txt
            │       └── something.bin
            └── pattern_2
                ├── everything.csv
                ├── nothing.txt
                └── something.bin
```

</details>


In the above, names of entities inside `pattern_*/` folder is arbitrary. We shall show how to capture their 
arbitrariness in a configuration file later so the `lochness` module is able to recognize and download them. 

In the following, we show a more specific example with fictitious names. For the example, we have chosen 
*actigraphy*, *phone*, and *survey* data but the organization can be applied to other data types e.g. *mri*, *eeg* etc.

```
/projects/proj-5070_prescient-1128.4.380/
├── BWH
│   ├── all_BWH_actigraphy
│   │   ├── 01234
│   │   │   ├── accel
│   │   │   │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
│   │   │   ├── GENEActiv
│   │   │   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│   │   │   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│   │   │   └── GENEActivQC
│   │   │       └── BLS-F6VVM-GENEActivQC-day22to51.csv
│   │   └── 01235
│   │       ├── accel
│   │       │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
│   │       ├── GENEActiv
│   │       │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│   │       │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│   │       └── GENEActivQC
│   │           └── BLS-F6VVM-GENEActivQC-day22to51.csv
│   ├── all_phone
│   │   ├── 01235
│   │   │   ├── processed
│   │   │   │   ├── accel
│   │   │   │   ├── audioRecordings
│   │   │   │   ├── gps
│   │   │   │   ├── power
│   │   │   │   ├── surveyAnswers
│   │   │   │   └── surveyTimings
│   │   │   └── raw
│   │   │       └── rsl54vij
│   │   └── 01236
│   │       ├── processed
│   │       │   ├── accel
│   │       │   ├── audioRecordings
│   │       │   ├── gps
│   │       │   ├── power
│   │       │   ├── surveyAnswers
│   │       │   └── surveyTimings
│   │       └── raw
│   │           └── rsl54vij
│   └── surveys
│       ├── 01236
│       │   ├── BLS-7NE49-redcapclinical-day1to882.csv
│       │   ├── BLS-7NE49-redcapclinical-day1to946.csv
│       │   ├── BLS-7NE49-redcapdemographics-day-1443to1378.csv
│       │   ├── BLS-7NE49-redcapdemographics-day-1443to946.csv
│       │   ├── BLS-7NE49-redcapwatch_swap-day1to946.csv
│       │   └── processed
│       │       ├── F6VVM.12_month_Longitudinal_Imaging_in_SZ_and_BP_Scales.json
│       │       ├── F6VVM.CORE_SCID.json
│       │       └── F6VVM.Ongur_Lab_Database.json
│       └── 01237
│           ├── BLS-7NE49-redcapclinical-day1to882.csv
│           ├── BLS-7NE49-redcapclinical-day1to946.csv
│           ├── BLS-7NE49-redcapdemographics-day-1443to1378.csv
│           ├── BLS-7NE49-redcapdemographics-day-1443to946.csv
│           ├── BLS-7NE49-redcapwatch_swap-day1to946.csv
│           └── processed
│               ├── F6VVM.12_month_Longitudinal_Imaging_in_SZ_and_BP_Scales.json
│               ├── F6VVM.CORE_SCID.json
│               └── F6VVM.Ongur_Lab_Database.json
```
<details><summary>└── MGH</summary>

```
    ├── all_BWH_actigraphy
    │   ├── 01234
    │   │   ├── accel
    │   │   │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
    │   │   ├── GENEActiv
    │   │   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
    │   │   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
    │   │   └── GENEActivQC
    │   │       └── BLS-F6VVM-GENEActivQC-day22to51.csv
    │   └── 01235
    │       ├── accel
    │       │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
    │       ├── GENEActiv
    │       │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
    │       │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
    │       └── GENEActivQC
    │           └── BLS-F6VVM-GENEActivQC-day22to51.csv
    ├── all_phone
    │   ├── 01235
    │   │   ├── processed
    │   │   │   ├── accel
    │   │   │   ├── audioRecordings
    │   │   │   ├── gps
    │   │   │   ├── power
    │   │   │   ├── surveyAnswers
    │   │   │   └── surveyTimings
    │   │   └── raw
    │   │       └── rsl54vij
    │   └── 01236
    │       ├── processed
    │       │   ├── accel
    │       │   ├── audioRecordings
    │       │   ├── gps
    │       │   ├── power
    │       │   ├── surveyAnswers
    │       │   └── surveyTimings
    │       └── raw
    │           └── rsl54vij
    └── surveys
        ├── 01236
        │   ├── BLS-7NE49-redcapclinical-day1to882.csv
        │   ├── BLS-7NE49-redcapclinical-day1to946.csv
        │   ├── BLS-7NE49-redcapdemographics-day-1443to1378.csv
        │   ├── BLS-7NE49-redcapdemographics-day-1443to946.csv
        │   ├── BLS-7NE49-redcapwatch_swap-day1to946.csv
        │   └── processed
        │       ├── F6VVM.12_month_Longitudinal_Imaging_in_SZ_and_BP_Scales.json
        │       ├── F6VVM.CORE_SCID.json
        │       └── F6VVM.Ongur_Lab_Database.json
        └── 01237
            ├── BLS-7NE49-redcapclinical-day1to882.csv
            ├── BLS-7NE49-redcapclinical-day1to946.csv
            ├── BLS-7NE49-redcapdemographics-day-1443to1378.csv
            ├── BLS-7NE49-redcapdemographics-day-1443to946.csv
            ├── BLS-7NE49-redcapwatch_swap-day1to946.csv
            └── processed
                ├── F6VVM.12_month_Longitudinal_Imaging_in_SZ_and_BP_Scales.json
                ├── F6VVM.CORE_SCID.json
                └── F6VVM.Ongur_Lab_Database.json
```

</details>

A couple of notes about the above symbolic and specific examples:

* Here are two equivalences:

    1. 
        * `namespace/SITE_A/datatype_1/sub001/*.csv`
        * `/projects/proj-5070_prescient-1128.4.380/BWH/surveys/01236/*.csv`
    2. 
        * `namespace/SITE_A/datatype_1/sub001/pattern_1/*.csv`
        * `/projects/proj-5070_prescient-1128.4.380/BWH/all_BWH_actigraphy/01236/accel/*.csv`

* There can be any number of directories inside `namespace/SITE_A/datatype_1/sub001/` e.g.
    * zero: `/projects/proj-5070_prescient-1128.4.380/BWH/surveys/01236/*.csv`
    * one: `/projects/proj-5070_prescient-1128.4.380/BWH/all_BWH_actigraphy/01236/GENEActiv/*.bin`
    * three: `/projects/proj-5070_prescient-1128.4.380/BWH/all_phone/01235/raw/rsl54vij/gps/2019-12-19\ 19_00_00.csv.lock`

Their patterns just have to be appropriately defined in a configuration file so the `lochness` module is able to 
recognize and download them.

* `datatype_*` folder names are arbitrary e.g. `all_BWH_actigraphy`, `all_phone`, `surveys`. Again, we shall note them 
in a configuration file accordingly later.

---

Install lochness
----------------

> pip install git+https://https://github.com/PREDICT-DPACC/lochness.git


Generate PHOENIX directory
--------------------------

`lochness` module will download Mediaflux remote data into a directory hierarchy informally known as `PHOENIX`. 
You can read more about it [here](http://docs.neuroinfo.org/lochness/en/latest/quick_start.html#phoenix). However, the `PHOENIX` directory hierarchy needs to be initialized manually as follows: 

> phoenix-generator.py --study BWH ./PHOENIX

The above command will generate the following directory structure:

    PHOENIX/
    ├── GENERAL
    │   └── BWH
    │       └── BWH_metadata.csv
    └── PROTECTED
        └── BWH


---

Now that we have remote data available and local directory set up, we shall define some parameters via three files to 
download remote data:

* Configuration
* Keyring
* Metadata  

Configuration file
------------------

Various parameters of the configuration file are described in detail [here](http://docs.neuroinfo.org/lochness/en/latest/configuration_file.html). 
For completeness of this documentation, a relevant snippet is provided below: 

> config.yml

    keyring_file: /home/tb571/.lochness.enc
    phoenix_root: /home/tb571/PHOENIX
    pid: /home/tb571/lochness.pid
    stderr: /home/tb571/lochness.stderr
    stdout: /home/tb571/lochness.stdout
    poll_interval: 20
    mediaflux:
        bwh:
            namespace: /projects/proj-5070_prescient-1128.4.380/BWH
            file_patterns:
            actigraphy:
                - vendor: Philips
                  product: Actiwatch 2
                  data_dir: all_BWH_actigraphy
                  pattern: 'accel/*csv'
                  protect: True
                - vendor: Activinsights
                  product: GENEActiv
                  data_dir: all_BWH_actigraphy
                  pattern: 'GENEActiv/*bin,GENEActiv/*csv'
                - vendor: Insights
                  product: GENEActivQC
                  data_dir: all_BWH_actigraphy
                  pattern: 'GENEActivQC/*csv'
            phone:
                - data_dir: all_phone
                  pattern: 'processed/accel/*csv'
    
    notify:
        __global__:
            - tbillah@bwh.harvard.edu

The above snippet contains only `mediaflux` subsection but you may have other subsections e.g. `xnat`, `redcap` etc. 
Please continue reading below to learn about parameters in the `mediaflux` subsection. However, the above configuration 
will download remote data into the following `PHOENIX` structure:

<details><summary>PHOENIX/</summary>

```
├── GENERAL
│   └── BWH
│       ├── BWH_metadata.csv
│       ├── sub01234
│       │   ├── actigraphy
│       │   │   ├── GENEActiv
│       │   │   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│       │   │   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│       │   │   └── GENEActivQC
│       │   │       └── BLS-F6VVM-GENEActivQC-day22to51.csv
│       │   └── phone
│       │       └── processed
│       │           └── accel
│       │               ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to43.csv
│       │               ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to51.csv
│       │               └── BLS-F6VVM-phone_accel_activityScores_hourly-day1to79.csv
│       ├── sub01235
│       │   ├── actigraphy
│       │   │   ├── GENEActiv
│       │   │   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│       │   │   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│       │   │   └── GENEActivQC
│       │   │       └── BLS-F6VVM-GENEActivQC-day22to51.csv
│       │   └── phone
│       │       └── processed
│       │           └── accel
│       │               ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to43.csv
│       │               ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to51.csv
│       │               └── BLS-F6VVM-phone_accel_activityScores_hourly-day1to79.csv
│       └── sub01236
│           ├── actigraphy
│           │   ├── GENEActiv
│           │   │   ├── 2020-02-07\ 09-19-15.bin
│           │   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│           │   └── GENEActivQC
│           │       └── BLS-F6VVM-GENEActivQC-day22to51.csv
│           └── phone
│               └── processed
│                   └── accel
│                       ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to43.csv
│                       ├── BLS-F6VVM-phone_accel_activityScores_hourly-day1to51.csv
│                       └── BLS-F6VVM-phone_accel_activityScores_hourly-day1to79.csv
└── PROTECTED
    └── BWH
        ├── sub01234
        │   └── actigraphy
        │       └── accel
        │           └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
        ├── sub01235
        │   └── actigraphy
        │       └── accel
        │           └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
        └── sub01236
            └── actigraphy
                └── accel
                    └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv

```

</details>

How the magic happened is described later ^_^

Keyring file
------------

Details about the `keyring_file` are explained [here](http://docs.neuroinfo.org/lochness/en/latest/quick_start.html#setup) 
and [here](http://docs.neuroinfo.org/lochness/en/latest/data_sources.html). In short, define a file like below and encrypt it:

> ~/.lochness.json

    {
        "lochness": {
            "SECRETS": {
                "BWH":""
            }
        },
        "mediaflux.bwh": {
            "HOST": "mediaflux.researchsoftware.unimelb.edu.au",
            "PORT": "443",
            "TRANSPORT": "https",
            "TOKEN":
            "DOMAIN": "",
            "USER": "",
            "PASSWORD": ""
        }
    }
     
> crypt.py --encrypt ~/.lochness.json -o ~/.lochness.enc

The output `~/.lochness.enc` has been specified as the `keyring_file` in the aforementioned configuration file. 
In the above, the site name is `BWH` that we used for `PHOENIX` directory generation. Since there is no value for 
`lochness.SECRETS.BWH`, downloaded data will not be encrypted. Remote name of the data is `mediaflux.bwh` that appeared 
as:

    mediaflux:
        bwh:
            ...

in the aforementioned configuration file and must exist in the `BWH_metadata.csv` file.

Metadata file
-------------

Previously created `BWH_metadata.csv` will contain fictitious values. You must insert a `Mediaflux` column in it with 
`Subject ID`s you want to download from Mediaflux remote.

    Active,Consent,Subject ID,Mediaflux,XNAT
    1,2017-02-09,sub01234,mediaflux.bwh:01234,xnat:HCPEP-BWH:01234
    1,2017-02-09,sub01235,mediaflux.bwh:01235,xnat:HCPEP-BWH:01235
    1,2017-02-09,sub01236,mediaflux.bwh:01236,xnat:HCPEP-BWH:01236

Rows in the `Mediaflux` column are of pattern `mediaflux.{SITE}:{ID}`. The remote `ID` can be different from that 
of the local `Subject ID` e.g. `01234` and `sub01234` respectively. You just have to make sure that the remote `ID`s exist 
in your Mediaflux remote at a certain depth as characterized by `sub001` and `sub002` in the aforementioned [examples](#mediaflux-remote).
Finally, the `Subject ID`s name the local folders:

<details><summary>Expand</summary>

    PHOENIX/
    ├── GENERAL
    │   └── BWH
    │       ├── BWH_metadata.csv
    │       ├── sub01234
    │       ├── sub01235
    │       └── sub01236
    └── PROTECTED
        └── BWH
            ├── sub01234
            ├── sub01235
            └── sub01236

</details>

    
while the `datatype_1 (actigraphy)` and `datatype_2 (phone)` used in the configuration file name the folders inside 
each `Subject ID` folders:

<details><summary>Expand</summary>

    PHOENIX/
    ├── GENERAL
    │   └── BWH
    │       ├── BWH_metadata.csv
    │       ├── sub01234
    │       │   ├── actigraphy
    │       │   └── phone
    │       ├── sub01235
    │       │   ├── actigraphy
    │       │   └── phone
    │       └── sub01236
    │           ├── actigraphy
    │           └── phone
    └── PROTECTED
        └── BWH
            ├── sub01234
            │   └── actigraphy
            ├── sub01235
            │   └── actigraphy
            └── sub01236
                └── actigraphy

</details>


Appendix
--------

* The remote name `mediaflux.bwh` from `BWH_metadata.csv` appears in `~/.lochness.json` and exists as:

    ```
    mediaflux:
        bwh:
            ...
    ```

    in `config.yml` file.

* Mediaflux remote location of a file is constructed from `config.yml` and `BWH_metadata.csv` as: 

    `namespace/SITE/data_dir/ID/pattern`
    
    (remember that rows under `Mediaflux` column have values like `mediaflux.{SITE}:{ID}`)

* Local destination is constructed as:

    `PHOENIX_ROOT/GENERAL/SITE/Subject ID/datatype/pattern`
    
    or
    
    `PHOENIX_ROOT/PROTECTED/SITE/Subject ID/datatype/pattern` when `protect: True`
    
    (remember that value of `Subject ID` can be different from `ID` in `mediaflux.{SITE}:{ID}` under `Mediaflux` column)
    
    <details><summary>Example remote-local mapping</summary>
    
    * Remote
        ```
        namespace/SITE/data_dir/ID/pattern
        /projects/proj-5070_prescient-1128.4.380/BWH/all_BWH_actigraphy/01236/accel/*.csv
        ```
    
    * Local
        ```
        PHOENIX_ROOT/PROTECTED/SITE/Subject ID/datatype/pattern
        PHOENIX/PROTECTED/BWH/sub01236/actigraphy/accel/BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
        ```
    
    </details>

* A pattern must include an asterisk (`*`).

* If there are data with multiple patterns in one `data_dir`, they can be specified via comma separated strings against 
`pattern`:
    ```
    actigraphy:
        - vendor: Philips
          product: Actiwatch 2
          data_dir: all_BWH_actigraphy
          pattern: 'GENEActiv/*bin,GENEActiv/*csv'
    ```

* Files for pulling data of multiple sites all together

    <details><summary>.lochness.json</summary>
    
        {
            "lochness": {
                "SECRETS": {
                    "BWH":"",
                    "MGH":""
                }
            },
            "mediaflux.bwh": {
                "HOST": "mediaflux.researchsoftware.unimelb.edu.au",
                "PORT": "443",
                "TRANSPORT": "https",
                "TOKEN":
                "DOMAIN": "",
                "USER": "",
                "PASSWORD": ""
            },
            "mediaflux.mgh": {
                "HOST": "mediaflux.researchsoftware.unimelb.edu.au",
                "PORT": "443",
                "TRANSPORT": "https",
                "TOKEN":
                "DOMAIN": "",
                "USER": "",
                "PASSWORD": ""
            }
        }
    
    </details>    
        
    <details><summary>config.yml</summary>
    
        keyring_file: /home/tb571/.lochness.enc
        phoenix_root: /home/tb571/PHOENIX
        pid: /home/tb571/lochness.pid
        stderr: /home/tb571/lochness.stderr
        stdout: /home/tb571/lochness.stdout
        poll_interval: 20
        mediaflux:
            bwh:
                namespace: /projects/proj-5070_prescient-1128.4.380/BWH
                file_patterns:
                actigraphy:
                    - vendor: Insights
                      product: GENEActivQC
                      data_dir: all_BWH_actigraphy
                      pattern: 'GENEActivQC/*csv'
                phone:
                    - data_dir: all_phone
                      pattern: 'processed/accel/*csv'
                      
            mgh:
                namespace: /projects/proj-5070_prescient-1128.4.380/MGH
                file_patterns:
                actigraphy:
                    - vendor: Insights
                      product: GENEActivQC
                      data_dir: all_BWH_actigraphy
                      pattern: 'GENEActivQC/*csv'
                phone:
                    - data_dir: all_phone
                      pattern: 'processed/accel/*csv'
        
        notify:
            __global__:
                - tbillah@bwh.harvard.edu
    
    </details>
    
    `BWH_metadata.csv` and `MGH_metadata.csv` must be in place as described [here](#metadata-file).