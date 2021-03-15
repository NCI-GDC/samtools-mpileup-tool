#!/usr/bin/env python3
"""
Multithreading Samtools mpileup
@author: Shenglai Li
"""

import argparse
import concurrent.futures
import logging
import os
import pathlib
import shlex
import subprocess
import sys
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from textwrap import dedent
from types import SimpleNamespace
from typing import IO, Any, Callable, Generator, List, NamedTuple, Optional

from samtools_mpileup_tool import __version__

logger = logging.getLogger(__name__)

DI = SimpleNamespace(subprocess=subprocess, futures=concurrent.futures,)


class PopenReturn(NamedTuple):
    stderr: str
    stdout: str


CMD_STR = dedent(
    """
    {samtools}
    mpileup
    -f
    {reference_path}
    -q
    {min_mq}
    -B
    -r
    {region}
    {normal_bam}
    {tumor_bam}
    -o
    {output}.mpileup
    """
).strip()


def setup_logger():
    """
    Sets up the logger.
    """
    logger_format = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    logger.setLevel(level=logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(logger_format, datefmt="%Y%m%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def subprocess_commands_pipe(cmd: str, timeout: int = 3600, di=DI) -> PopenReturn:
    """run pool commands"""

    output = di.subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        output_stdout, output_stderr = output.communicate(timeout=timeout)
    except Exception:
        output.kill()
        _, output_stderr = output.communicate()
        raise ValueError(output_stderr.decode())

    if output.returncode != 0:
        raise ValueError(output_stderr.decode())

    return PopenReturn(stdout=output_stdout.decode(), stderr=output_stderr.decode())


def tpe_submit_commands(
    cmds: List[Any], thread_count: int, fn: Callable = subprocess_commands_pipe, di=DI,
) -> list:
    """Run commands on multiple threads.

    Stdout and stderr are logged on function success.
    Exception logged on function failure.
    Accepts:
        cmds (List[str]): List of inputs to pass to each thread.
        thread_count (int): Threads to run
        fn (Callable): Function to run using threads, must accept each element of cmds
    Returns:
        list of commands which raised exceptions
    Raises:
        None
    """
    exceptions = []
    with di.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = {executor.submit(fn, cmd): cmd for cmd in cmds}
        for future in di.futures.as_completed(futures):
            cmd = futures[future]
            try:
                result = future.result()
                logger.info(result.stdout)
                logger.info(result.stderr)
            except Exception as e:
                exceptions.append(cmd)
    return exceptions


def yield_bed_regions(intervals_file: str) -> Generator[str, None, None]:
    """Yield region string from BED file."""
    with open(intervals_file, "r") as fh:
        for line in fh:
            chrom, start, end, *_ = line.strip().split()
            interval = "{}:{}-{}".format(chrom, int(start) + 1, end)
            yield interval


def get_file_size(filename: pathlib.Path) -> int:
    """ Gets file size """
    return filename.stat().st_size


def yield_formatted_commands(
    samtools: str,
    reference_path: str,
    min_mq: str,
    normal_bam: str,
    tumor_bam: str,
    interval_bed_path: str,
) -> Generator[str, None, None]:
    """Yield commands for each BED interval."""
    for region in yield_bed_regions(interval_bed_path):
        cmd = CMD_STR.format(
            samtools=samtools,
            reference_path=reference_path,
            min_mq=min_mq,
            region=region,
            normal_bam=normal_bam,
            tumor_bam=tumor_bam,
            output=region.replace(":", "-"),
        )
        yield cmd


def setup_parser():
    """
    Loads the parser.
    """
    parser = argparse.ArgumentParser(
        "Internal multithreading samtools mpileup calling."
    )
    parser.add_argument("--version", action="version", version=__version__)
    # Required flags.
    parser.add_argument("-f", "--reference_path", required=True, help="Reference path.")
    parser.add_argument(
        "-r", "--interval_bed_path", required=True, help="Interval bed file."
    )
    parser.add_argument("-t", "--tumor_bam", required=True, help="Tumor bam file.")
    parser.add_argument("-n", "--normal_bam", required=True, help="Normal bam file.")
    parser.add_argument(
        "-c", "--thread_count", type=int, required=True, help="Number of thread."
    )
    parser.add_argument("-m", "--min_mq", type=int, required=True, help="min MQ.")
    parser.add_argument("--samtools", default="/usr/local/bin/samtools", required=False)

    return parser


def process_argv(argv: Optional[List] = None) -> namedtuple:
    """Processes argv into namedtuple."""

    parser = setup_parser()

    if argv:
        args, unknown_args = parser.parse_known_args(argv)
    else:
        args, unknown_args = parser.parse_known_args()

    args_dict = vars(args)
    args_dict['extras'] = unknown_args
    run_args = namedtuple('RunArgs', list(args_dict.keys()))
    return run_args(**args_dict)


def run(run_args):
    """Main script logic.
    Creates commands for each BED region and executes in multiple threads.
    """

    run_commands = list(
        yield_formatted_commands(
            run_args.samtools,
            run_args.reference_path,
            run_args.min_mq,
            run_args.normal_bam,
            run_args.tumor_bam,
            run_args.interval_bed_path,
        )
    )
    # Start Queue
    exceptions = tpe_submit_commands(run_commands, run_args.thread_count)
    if exceptions:
        for e in exceptions:
            logger.error(e)
        raise ValueError("Exceptions raised during processing.")

    # Check and merge outputs
    p = pathlib.Path('.')
    outputs = list(p.glob("*.mpileup"))

    # Sanity check
    if len(run_commands) != len(outputs):
        logger.error("Number of output files not expected")

    return


def main(argv=None) -> int:
    exit_code = 0

    argv = argv or sys.argv
    args = process_argv(argv)
    setup_logger()

    try:
        run(args)
    except Exception as e:
        logger.exception(e)
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    # CLI Entrypoint.
    retcode = 0

    try:
        retcode = main()
    except Exception as e:
        retcode = 1
        logger.exception(e)

    sys.exit(retcode)


# __END__
