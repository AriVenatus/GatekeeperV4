# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import subprocess
import argparse
import hashlib
import pip
import threading
from threading import current_thread
import time
import pathlib


class Setup:
    def __init__(self):
        # Use action="store_true", then check the arg via "args.name" eg. "args.dev"
        parser = argparse.ArgumentParser(description='AMP Discord Bot')
        parser.add_argument('-token', help='Bypasse tokens validation check.', required=False, action="store_true")
        parser.add_argument('-super', help='This leaves AMP Super Admin role intact, use at your own risk.', required=False, action="store_true")
        parser.add_argument('-whitelist-only', dest='whitelist_only', required=False, action="store_true",
            help="Restrict the bot's AMP role on the main instance to the minimum needed for Discord-Role<->Whitelist "
                 "sync (no Instances.*/ADS.*/FileManager.*/LocalFileBackup.* access).")

        # All the args below are used for development purpose.
        parser.add_argument('-dev', help='Enable development print statments.', required=False, action="store_true")
        parser.add_argument('-command', help='Enable command usage print statements.', required=False, action="store_true")
        parser.add_argument('-discord', help='Disables Discord Intigration (used for testing)', required=False, action="store_false")
        parser.add_argument('-debug', help='Enables DEBUGGING level for logging', required=False, action="store_true")
        self.args = parser.parse_args()

        self.pip_install()

        # Custom Logger functionality.
        import logging
        from core import logger
        logger.init(self.args)
        self.logger = logging.getLogger()

        # Renaming Main Thread to "Gatekeeper"
        Gatekeeper = current_thread()
        Gatekeeper.name = 'Gatekeeper'

        self.logger.dev(f'Current Startup Args:{self.args}')

        self.logger.dev("**ATTENTION** YOU ARE IN DEVELOPMENT MODE** All features are not present and stability is not guaranteed!")

        if not self.args.discord:
            self.logger.critical("***ATTENTION*** Discord Intergration has been DISABLED!")

        # This sets up our SQLite Database!
        from core import DB
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DB_Config = self.DB.DBConfig
        self.logger.info(f'SQL Database Version: {self.DB.DBHandler.DB_Version} // SQL Database: {self.DB.DBHandler.SuccessfulDatabase}')

        # This connects and creates all our AMP related parts
        from core import AMP_Handler
        # Run AMP handler in a background thread. For normal bot runs we make it daemon so shutdown cannot hang.
        self.AMP_Thread = threading.Thread(target=AMP_Handler.AMP_init, name='AMP Handler', args=[self.args, ], daemon=self.args.discord)
        self.AMP_Thread.start()

        if self.args.discord:
            while (AMP_Handler.AMP_setup == False):
                time.sleep(.5)

            from core import discordBot
            try:
                discordBot.client_run(AMP_Handler.getAMPHandler().tokens)
            except (KeyboardInterrupt, SystemExit):
                self.logger.warning('Shutdown signal received, stopping Gatekeeper...')
            finally:
                AMP_Handler.request_shutdown()
                self.AMP_Thread.join(timeout=10)
                if self.AMP_Thread.is_alive():
                    self.logger.warning('AMP handler thread did not stop cleanly before process exit.')

    def python_ver_check(self):
        if not sys.version_info.major >= 3 and not sys.version_info.minor >= 10:
            self.logger.critical(f'Unable to Start Gatekeeper, Python Version is {sys.version_info.major + "." + sys.version_info.minor} we require Python Version >= 3.10')
            sys.exit(1)

    def pip_install(self):
        pip_version = pip.__version__.split('.')
        pip_v_major = int(pip_version[0])
        pip_v_minor = int(pip_version[1])

        if not (pip_v_major > 22 or (pip_v_major == 22 and pip_v_minor >= 1)):
            print(f'Unable to Start Gatekeeper, PIP Version is {pip.__version__}, we require PIP Version >= 22.1')
            return

        _current_path = pathlib.Path(__file__).parent.absolute()
        _requirements_path = _current_path.joinpath('requirements.txt')
        _marker_path = _current_path.joinpath('.pip_install.marker')
        _current_hash = hashlib.sha256(_requirements_path.read_bytes()).hexdigest()

        if _marker_path.exists() and _marker_path.read_text().strip() == _current_hash:
            return  # requirements.txt unchanged since last successful install; skip.

        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', f'{_requirements_path}'])
        _marker_path.write_text(_current_hash)


Start = Setup()
