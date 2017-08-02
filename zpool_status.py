#!/usr/local/bin/python

import argparse
# import locate_disk
import logging
import os
import pprint
import subprocess
import sys

_version = "0.3.1"
print os.path.basename(__file__) + ": v" + _version
_logger = logging.getLogger(__name__)
_LOG_LEVEL = logging.DEBUG


def _parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version",
                        version=_version)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    # parser.add_argument("-lr", "--locate_resilvering", action="store_true")
    parser.add_argument("pool_name")
    args = parser.parse_args()
    return args


def _setup_logging(args=None):
    # Setup logging
    _logger.setLevel(_LOG_LEVEL)
#     formatter = logging.Formatter("[%(asctime)s] %(filename)s \
# (%(levelname)s,%(lineno)d) : %(message)s")
    formatter = logging.Formatter("%(message)s")

    # Check verbosity for console
    if args and args.verbose >= 1:
        _CONS_LOG_LEVEL = logging.DEBUG
    elif args:
        _CONS_LOG_LEVEL = logging.INFO
    else:
        _CONS_LOG_LEVEL = logging.WARN

    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_CONS_LOG_LEVEL)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

if __name__ == "__main__":

    # Parse arguments
    args = _parse_arguments()

    # Setup logging
    _setup_logging(args)

    # Get GPTID<->/dev/da* mapping
    glabel_status = subprocess.check_output(["glabel", "status"])
    gptids = {}
    # disks = set()
    for line in glabel_status.split("\n")[1:-1]:
        tokens = line.strip().split()
        gptids[tokens[0].strip()] = tokens[-1].strip()
        # disks.add(tokens[-1].strip())

    ls_devda = subprocess.check_output(["ls /dev/da*"], shell=True)
    # gptids = {}
    disks = set()
    for line in ls_devda.split("\n")[1:-1]:
        if not 'p' in line:
            tokens = line.strip().split()
            # print tokens
            # continue
            # gptids[tokens[0].strip()] = tokens[-1].strip()
            disks.add(tokens[0])
    # pprint.pprint(disks)
    # exit(1)

    # if args.locate_resilvering:
    #     _logger.info("Turn off all slot bay LEDs first...")
    #     locate_disk.all_disks("off")

    # Get current zpool status
    zpool_status = subprocess.check_output(["zpool", "status", args.pool_name])
    for line in zpool_status.split("\n"):
        if "gptid/" in line and not "/gptid/" in line:
            for gptid in gptids.viewkeys():
                if gptid in line:
                    _logger.info(line.replace(gptid, gptids[gptid] +
                                              " " * (len(gptid) - len(gptids[gptid]))))
                    # if args.locate_resilvering:
                    #     # Find serial no
                    #     cmd = ["smartctl", "-i", "/dev/" + gptids[gptid][:-2]]
                    #     _logger.debug(" ".join(cmd))
                    #     smartctl = subprocess.check_output(cmd)
                    #     serial_no = None
                    #     for l2 in smartctl.split("\n"):
                    #         if "Serial Number:" in l2:
                    #             serial_no = l2.split()[-1]
                    #     if serial_no is None:
                    #         _logger.error(
                    #             "Cannot find serial number! Exiting.")
                    #         exit(1)
                    #     # Locate disk and turn its slot bay LED on
                    #     locate_disk.locate_disk(serial_no, "on")

                    diskname = '/dev/' + gptids[gptid][:-2]
                    # _logger.info(diskname)
                    disks.discard(diskname)
                    # exit(1)
                    break
        else:
            _logger.info(line)

    _logger.info("Unreferenced disks:\n%s", pprint.pformat(disks))
