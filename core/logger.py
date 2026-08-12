# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import pathlib

# Python 3.13 removed the private logging._acquireLock()/_releaseLock() wrapper
# functions that haggis.logs.add_logging_level() still calls internally (the
# underlying logging._lock it wrapped is still present). Back-fill them so
# custom level registration below keeps working; harmless no-op on older
# Python where haggis's own functions already exist.
if not hasattr(logging, '_acquireLock'):
    logging._acquireLock = logging._lock.acquire
if not hasattr(logging, '_releaseLock'):
    logging._releaseLock = logging._lock.release

from haggis import logs

def init(args=None):
    logginglevel = logging.INFO

    #To Enable debug logging level (ewwwwww.....)
    if args.debug:
        logginglevel = logging.DEBUG
 
    dircheck = pathlib.Path.exists(pathlib.Path.cwd().joinpath('logs'))
    if dircheck != True:
        print('Making Log Directory...')
        pathlib.Path.mkdir(pathlib.Path.cwd().joinpath('logs'))

    #This level is for development purpose; a little more information in key spots without the debug annoyance.
    dev_level = 15
    dev_label = 'DEV'
    logs.add_logging_level(dev_label, dev_level)
    if args.dev:
        logginglevel = logging.DEV

    #This is for displaying slash commands information for tracing info!
    command_level = 19
    command_label = 'COMMAND'
    
    logs.add_logging_level(command_label, command_level)
    if args.command:
        logginglevel = logging.COMMAND
    
    logging.basicConfig(level=logginglevel, format='%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers = [logging.StreamHandler(sys.stdout),
                        TimedRotatingFileHandler(pathlib.Path.as_posix(pathlib.Path.cwd().joinpath('logs')) + '/log','midnight',atTime=datetime.datetime.min.time(),backupCount= 4,encoding='utf-8',utc=True)])
  
        