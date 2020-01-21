"""
Multithreading Samtools mpileup

@author: Shenglai Li
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import string
from functools import partial
from multiprocessing.dummy import Pool, Lock


def setup_logger():
    """
    Sets up the logger.
    """
    logger = logging.getLogger("multi_samtools_mpileup")
    logger_format = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    logger.setLevel(level=logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(logger_format, datefmt="%Y%m%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def do_pool_commands(cmd, logger, shell_var=True, lock=Lock()):
    """run pool commands"""
    try:
        output = subprocess.Popen(
            cmd, shell=shell_var, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output_stdout, output_stderr = output.communicate()
        with lock:
            logger.info("Samtools mpileup Args: %s", cmd)
            logger.info(output_stdout)
            logger.info(output_stderr)
    except BaseException:
        logger.error("command failed %s", cmd)
    return output.wait()


def multi_commands(cmds, thread_count, logger, shell_var=True):
    """run commands on number of threads"""
    pool = Pool(int(thread_count))
    output = pool.map(
        partial(do_pool_commands, logger=logger, shell_var=shell_var), cmds
    )
    return output


def get_region(intervals):
    """get region from intervals"""
    interval_list = []
    with open(intervals, "r") as fh:
        line = fh.readlines()
        for bed in line:
            blocks = bed.rstrip().rsplit("\t")
            intv = "{}:{}-{}".format(blocks[0], int(blocks[1]) + 1, blocks[2])
            interval_list.append(intv)
    return interval_list


def cmd_template(dct):
    """cmd template"""
    lst = [
        "samtools",
        "mpileup",
        "-f",
        "${REF}",
        "-q",
        "${MIN_MQ}",
        "-B",
        "-r",
        "${REGION}",
        "${NORMAL}",
        "${TUMOR}",
        ">",
        "${OUTPUT}.mpileup",
    ]
    template = string.Template(" ".join(lst))
    for interval in get_region(dct["interval_bed_path"]):
        cmd = template.substitute(
            dict(
                REF=dct["reference_path"],
                MIN_MQ=dct["min_mq"],
                REGION=interval,
                NORMAL=dct["normal_bam"],
                TUMOR=dct["tumor_bam"],
                OUTPUT=interval.replace(":", "-"),
            )
        )
        yield cmd


def get_args():
    """
    Loads the parser.
    """
    parser = argparse.ArgumentParser(
        "Internal multithreading samtools mpileup calling."
    )
    # Required flags.
    parser.add_argument(
        "-f",
        "--reference_path",
        required=True,
        help="Reference path."
    )
    parser.add_argument(
        "-r",
        "--interval_bed_path",
        required=True,
        help="Interval bed file."
    )
    parser.add_argument(
        "-t",
        "--tumor_bam",
        required=True,
        help="Tumor bam file."
    )
    parser.add_argument(
        "-n",
        "--normal_bam",
        required=True,
        help="Normal bam file."
    )
    parser.add_argument(
        "-c",
        "--thread_count",
        type=int,
        required=True,
        help="Number of thread."
    )
    parser.add_argument(
        "-m",
        "--min_mq",
        type=int,
        required=True,
        help="min MQ."
    )
    return parser.parse_args()


def main(args, logger):
    """main"""
    logger.info("Running Samtools mpileup")
    dct = vars(args)
    mpileup_cmds = list(cmd_template(dct))
    outputs = multi_commands(mpileup_cmds, dct["thread_count"], logger)
    if any(x != 0 for x in outputs):
        logger.error("Failed multi_samtools_mpileup")
    else:
        logger.info("Completed multi_samtools_mpileup")


if __name__ == "__main__":
    # CLI Entrypoint.
    start = time.time()
    logger_ = setup_logger()
    logger_.info("-" * 80)
    logger_.info("multi_samtools_mpileup.py")
    logger_.info("Program Args: %s", " ".join(sys.argv))
    logger_.info("-" * 80)

    args_ = get_args()

    # Process
    logger_.info(
        "Processing tumor and normal bam files %s, %s",
        os.path.basename(args_.tumor_bam),
        os.path.basename(args_.normal_bam),
    )
    main(args_, logger_)

    # Done
    logger_.info("Finished, took %s seconds", round(time.time() - start, 2))
