"""
Multithreading Samtools mpileup

@author: Shenglai Li
"""

import os
import sys
import time
import glob
import shlex
import ctypes
import string
import logging
import argparse
import threading
import subprocess
from signal import SIGKILL
from functools import partial
from concurrent.futures import ThreadPoolExecutor


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


def subprocess_commands_pipe(cmd, logger, shell_var=False, lock=threading.Lock()):
    """run pool commands"""
    libc = ctypes.CDLL("libc.so.6")
    pr_set_pdeathsig = ctypes.c_int(1)

    def child_preexec_set_pdeathsig():
        """
        preexec_fn argument for subprocess.Popen,
        it will send a SIGKILL to the child once the parent exits
        """

        def pcallable():
            return libc.prctl(pr_set_pdeathsig, ctypes.c_ulong(SIGKILL))

        return pcallable

    try:
        output = subprocess.Popen(
            shlex.split(cmd),
            shell=shell_var,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=child_preexec_set_pdeathsig(),
        )
        output.wait()
        with lock:
            logger.info("Running command: %s", cmd)
    except BaseException as e:
        output.kill()
        with lock:
            logger.error("command failed %s", cmd)
            logger.exception(e)
    finally:
        output_stdout, output_stderr = output.communicate()
        with lock:
            logger.info(output_stdout.decode("UTF-8"))
            logger.info(output_stderr.decode("UTF-8"))

def tpe_submit_commands(cmds, thread_count, logger, shell_var=False):
    """run commands on number of threads"""
    with ThreadPoolExecutor(max_workers=thread_count) as e:
        for cmd in cmds:
            e.submit(
                partial(subprocess_commands_pipe, logger=logger, shell_var=shell_var),
                cmd,
            )


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
        "-o",
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
    kwargs = vars(args)

    # Start Queue
    tpe_submit_commands(list(cmd_template(kwargs)), kwargs["thread_count"], logger)

    # Check outputs
    outputs = glob.glob("*.mpileup")
    assert len(outputs) == len(
        get_region(kwargs["interval_bed_path"])
    ), "Missing output!"


if __name__ == "__main__":
    # CLI Entrypoint.
    start = time.time()
    logger_ = setup_logger()
    logger_.info("-" * 80)
    logger_.info("multi_samtools_mpileup_p3.py")
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
