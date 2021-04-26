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



    /projects/proj-5070_prescient-1128.4.380/
    ├── BWH
    │   ├── all_BWH_actigraphy
    │   ├── all_phone
    │   └── surveys
    ├── McLean
    │   ├── all_actigraphy
    │   ├── phone
    │   └── surveys_McLean
    └── MGH
        ├── actigraphy
        ├── phone
        └── surveys

As shown above, data folder names at the third level are arbitrary i.e. `all_BWH_actigraphy`, `all_actigraphy`, `actigraphy`. 
We shall note them in a configuration file accordingly later.


So the following remotes have 
`/projects/proj-5070_prescient-1128.4.380/` in their base locations.



For the examples, we have chosen *actigraphy* and *survey* data but the organization can 
be applied to other data types e.g. *phone*, *mri*, *eeg* etc. 


directories are arbitrary. What this means is that 
we have put *actigraphy* data in `mflux_dummy_data/all_BWH_actigraphy` directory but *survey* data 
directly under the namespace folder `all_surveys`

<details><summary>/projects/proj-5070_prescient-1128.4.380/mflux_dummy_data/all_BWH_actigraphy</summary>

```
all_BWH_actigraphy/
├── 01234
│   ├── accel
│   │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
│   ├── GENEActiv
│   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│   └── GENEActivQC
│       └── BLS-F6VVM-GENEActivQC-day22to51.csv
├── 01235
│   ├── accel
│   │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
│   ├── GENEActiv
│   │   ├── F6VVM__052281_2020-02-07\ 09-19-15.bin
│   │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
│   └── GENEActivQC
│       └── BLS-F6VVM-GENEActivQC-day22to51.csv
└── 01236
    ├── accel
    │   └── BLS-F6VVM-actigraphy_GENEActiv_accel_activityScores_hourly-day1to51.csv
    ├── GENEActiv
    │   ├── 2020-02-07\ 09-19-15.bin
    │   └── F6VVM__052281_2020-02-07\ 09-19-15.csv
    └── GENEActivQC
        └── BLS-F6VVM-GENEActivQC-day22to51.csv
```

</details>



<details><summary>/projects/proj-5070_prescient-1128.4.380/all_surveys</summary>

```
all_BWH_surveys/
├── 01234
│   ├── BLS-7NE49-redcapclinical-day1to882.csv
│   ├── BLS-7NE49-redcapclinical-day1to946.csv
│   ├── BLS-7NE49-redcapdemographics-day-1443to1378.csv
│   ├── BLS-7NE49-redcapdemographics-day-1443to946.csv
│   ├── BLS-7NE49-redcapwatch_swap-day1to946.csv
│   └── processed
│       ├── F6VVM.12_month_Longitudinal_Imaging_in_SZ_and_BP_Scales.json
│       ├── F6VVM.CORE_SCID.json
│       └── F6VVM.Ongur_Lab_Database.json
└── 01236
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

