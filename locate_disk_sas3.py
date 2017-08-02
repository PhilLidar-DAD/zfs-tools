#!/usr/bin/env python2

import argparse
import logging
import os
import os.path
import subprocess
import sys

CONTROLLER_ID = '0'
# DEVNULL = open(os.devnull, 'w')

_version = '0.6.2'
print os.path.basename(__file__) + ': v' + _version
_logger = logging.getLogger(__name__)
_LOG_LEVEL = logging.DEBUG
SAS2IRCU = 'sas3ircu'


def locate_disk(serial_no, action):

    _logger.info('Locating slot bay of disk with serial no: %s and turning \
the LED %s', serial_no, action)
    _logger.info('%s, %s', serial_no, action)

    # Get enclosure and slot id
    enclosure, slot = slot_map[serial_no.replace('-', '')]

    # Turn slot bay LED on/off depending on action
    if action == 'on':
        locate = subprocess.Popen([SAS2IRCU, CONTROLLER_ID, 'locate',
                                   enclosure + ':' + slot, 'on'])
        locate.wait()
    elif action == 'on60':
        locate = subprocess.Popen([SAS2IRCU, CONTROLLER_ID, 'locate',
                                   enclosure + ':' + slot, 'on', 'Wait', '60'])
        locate.wait()
    elif action == 'off':
        locate = subprocess.Popen([SAS2IRCU, CONTROLLER_ID, 'locate',
                                   enclosure + ':' + slot, 'off'])
        locate.wait()
    else:
        _logger.error('Unknown action. Exiting.')


def all_disks(action):

    # For each disk
    for serial_no in slot_map.viewkeys():
        # Locate disk and turn slot bay LED on/off
        locate_disk(serial_no, action)
        # _logger.warn('Testing!')
        # break


def _parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version=_version)
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-a', '--action', default='on', required=True)
    parser.add_argument('-sn', '--serial_no', default=None)
    parser.add_argument('-f', '--file_list', default=None)
    args = parser.parse_args()
    return args


def _setup_logging(args=None):
    # Setup logging
    _logger.setLevel(_LOG_LEVEL)
    formatter = logging.Formatter('%(message)s')

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

# Setup logging
_setup_logging()

# Display controller, volume and physical device info
dev_list = subprocess.check_output([SAS2IRCU, CONTROLLER_ID, 'display'])
enclosure = -1
slot = -1
slot_map = {}
for line in dev_list.split('\n'):
    tokens = line.strip().split(' ')
    if 'Enclosure #' in line:
        enclosure = tokens[-1]
    elif 'Slot #' in line:
        slot = tokens[-1]
    elif 'Serial No' in line:
        slot_map[tokens[-1]] = tuple([enclosure, slot])

if __name__ == '__main__':

    # Parse arguments
    args = _parse_arguments()

    # Setup logging
    _setup_logging(args)

    if args.serial_no is None:
        # Turn all slot bays LED on/off
        _logger.info('Turning all slot bays LED %s', args.action)
        all_disks(args.action)

    elif not args.file_list is None:
        fl_path = os.path.abspath(args.file_list)
        if os.path.isfile(fl_path):
            _logger.info('Serial no list file found: %s...', fl_path)
            with open(fl_path, 'r') as open_file:
                for line in open_file:
                    sn = line.strip()
                    if sn:
                        locate_disk(sn, args.action)

    elif not args.serial_no is None:
        # Locate slot bay of disk with the given serial no and turn the LED
        # on/off
        locate_disk(args.serial_no, args.action)
    else:
        _logger.error('Unknown program state. Exiting!')
