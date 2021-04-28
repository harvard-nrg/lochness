This documentation discusses how to organize data under a Mediaflux namespace and how they can be downloaded
by `lochness` module.


Mediaflux Remote Data
---------------------

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


