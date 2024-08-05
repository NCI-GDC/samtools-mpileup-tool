# GDC Samtools mpileup
![Version badge](https://img.shields.io/badge/samtools-1.1-<COLOR>.svg)

Original samtools: https://www.htslib.org/

## How to build

https://docs.docker.com/engine/reference/builder/

The docker images are tested under multiple environments. The most tested ones are:
* Docker version 19.03.2, build 6a30dfc
* Docker version 18.09.1, build 4c52b90
* Docker version 18.03.0-ce, build 0520e24
* Docker version 17.12.1-ce, build 7390fc6

## For external users
The repository has only been tested on GDC data and in the particular environment GDC is running in. Some of the reference data required for the workflow production are hosted in [GDC reference files](https://gdc.cancer.gov/about-data/data-harmonization-and-generation/gdc-reference-files "GDC reference files"). For any questions related to GDC data, please contact the GDC Help Desk at support@nci-gdc.datacommons.io.

There is a production-ready CWL example at https://github.com/NCI-GDC/samtools-mpileup-cwl which uses the docker images that are built from the `Dockerfile`s in this repo.

To use docker images directly or with other workflow languages, we recommend to build and use either vanilla samtools or multi-threading samtools mpileup.

To run multi-threading samtools mpileup:

```
[INFO] [20200121 22:20:53] [multi_samtools_mpileup] - --------------------------------------------------------------------------------
[INFO] [20200121 22:20:53] [multi_samtools_mpileup] - multi_samtools_mpileup_p3.py
[INFO] [20200121 22:20:53] [multi_samtools_mpileup] - Program Args: /mnt/SCRATCH/githubs/samtools_mpileup_tool/docker/multi_mpileup/multi_mpileup.py -h
[INFO] [20200121 22:20:53] [multi_samtools_mpileup] - --------------------------------------------------------------------------------
usage: Internal multithreading samtools mpileup calling. [-h] -f
                                                         REFERENCE_PATH -r
                                                         INTERVAL_BED_PATH -t
                                                         TUMOR_BAM -n
                                                         NORMAL_BAM -c
                                                         THREAD_COUNT -m
                                                         MIN_MQ

optional arguments:
  -h, --help            show this help message and exit
  -f REFERENCE_PATH, --reference_path REFERENCE_PATH
                        Reference path.
  -r INTERVAL_BED_PATH, --interval_bed_path INTERVAL_BED_PATH
                        Interval bed file.
  -t TUMOR_BAM, --tumor_bam TUMOR_BAM
                        Tumor bam file.
  -n NORMAL_BAM, --normal_bam NORMAL_BAM
                        Normal bam file.
  -c THREAD_COUNT, --thread_count THREAD_COUNT
                        Number of thread.
  -m MIN_MQ, --min_mq MIN_MQ
                        min MQ.
```

## For GDC users

See https://github.com/NCI-GDC/gdc-somatic-variant-calling-workflow.
