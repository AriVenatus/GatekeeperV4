# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import importlib
import logging
import os
import pathlib
import re
import sys
import threading
import time
import traceback
from argparse import Namespace
from types import SimpleNamespace

import requests

from core import AMP
from core import DB

# import utils
Handler = None
AMP_setup = False
AMP_shutdown_event = threading.Event()


def AMP_init(args: Namespace):
    global AMP_setup
    AMP_shutdown_event.clear()
    handler = getAMPHandler(args=args)
    handler.setup_AMPInstances()
    AMP_setup = True
    amp_server_instance_check()


def amp_server_instance_check():
    """Checks for new AMP Instances every 30 seconds.."""
    while not AMP_shutdown_event.is_set():
        handler = getAMPHandler()
        if handler is None:
            AMP_shutdown_event.wait(1)
            continue

        handler.logger.dev('Checking AMP Instance(s) Status...')
        try:
            handler._instanceValidation(main_amp=handler.AMP)
            handler.AMP._instance_ThreadManager()
        except Exception:
            handler.logger.error(f'AMP instance check loop exception: {traceback.format_exc()}')

        AMP_shutdown_event.wait(30)


def request_shutdown():
    """Request the AMP handler background loops to stop."""
    global AMP_setup
    AMP_shutdown_event.set()
    AMP_setup = False

    handler = Handler
    if handler is None:
        return

    try:
        handler.logger.info('Stopping AMP handler background loops...')
    except Exception:
        pass

    for server in list(handler.AMP_Instances.values()):
        if hasattr(server, "Console") and server.Console is not None:
            server.Console.console_thread_running = False


class AMPHandler:
    def __init__(self, args: Namespace):
        self.args = args
        self.logger = logging.getLogger()
        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.AMP2FA = False
        self.tokens = ''

        self.superUser = False

        self.SessionIDlist = {}

        # Shared across every AMPInstance (main + per-server) since they all talk to the
        # same AMP host -- reuses TCP/TLS connections instead of paying a fresh handshake
        # on every single CallAPI() call.
        self.http_session = requests.Session()

        self.AMP_Modules = {}
        self.AMP_Instances: dict[str, AMP.AMPInstance] = {}

        self.AMP_Console_Modules = {}
        self.AMP_Console_Threads = {}

        self.SuccessfulConnection = False
        # self.InstancesFound = False

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.val_settings()
        self.moduleHandler()

    def setup_AMPInstances(self):
        """Intializes the connection to AMP and creates AMP_Instance objects."""
        try:
            self.AMP = AMP.AMPInstance(Handler=self)
        except AMP.AMPInitError as e:
            # The main AMP instance (InstanceID == 0) failing to initialize is fatal -- there's
            # nothing else for Gatekeeper to do without it. This preserves the previous
            # effective behavior, where AMPInstance.__init__ called sys.exit(1) itself.
            self.logger.critical(f'***ATTENTION*** Failed to initialize the main AMP instance: {e}')
            sys.exit(1)
        self._instanceValidation(main_amp=self.AMP, startup=True)

        # This removes Super Admins from the bot user! Controlled through parser args!
        if not self.args.super and not self.args.dev:
            self.AMP.setAMPUserRoleMembership(self.AMP.AMP_UserID, self.AMP.super_AdminID, False)
            self.logger.warning(f'***ATTENTION*** Removing {self.tokens.AMPUser} from `Super Admins` Role!')
        elif self.args.super:
            self.logger.warning(
                f'***ATTENTION*** Gatekeeper was started with -super: {self.tokens.AMPUser} KEEPS the AMP '
                '`Super Admins` role, all Gatekeeper role/permission downgrade logic is skipped. '
                'This is NOT recommended for production -- restart without -super.'
            )
        elif self.args.dev:
            self.logger.warning(
                f'***ATTENTION*** Gatekeeper was started with -dev: {self.tokens.AMPUser} KEEPS the AMP '
                '`Super Admins` role for this session (dev-mode skips the downgrade).'
            )

    def get_AMP_instance_names(self, public: bool = False) -> dict[str, str]:
        """Creates a list of Instance Names/DisplayName or Friendly Name."""
        AMP_Instances_Names = {}
        for instanceID, server in list(self.AMP_Instances.items()):
            # If this is a "Public" Server Autocomplete or List/etc lets not SHOW our Hidden servers.
            if public and server.Hidden:
                continue

            # Using TargetName as a unique identifier for the server if they match names.
            if server.DisplayName != None:
                server_name = server.DisplayName

            else:
                if server.FriendlyName not in AMP_Instances_Names:
                    server_name = server.FriendlyName
                else:
                    server_name = server.InstanceName

            if hasattr(server, 'TargetName') and server.TargetName != None:
                server_name = f'({server.TargetName}) | ' + server_name
                # TargetName = f'({server.TargetName}) | '

            AMP_Instances_Names[instanceID] = server_name

        return AMP_Instances_Names

    def _load_tokens_from_env(self):
        """Builds a tokens-like namespace from environment variables (optionally loaded from a
        .env file via python-dotenv)."""
        try:
            from dotenv import load_dotenv
            load_dotenv()  # no-op if no .env present; never overrides already-exported env vars
        except ImportError:
            self.logger.dev('python-dotenv not available; relying on process environment only.')

        env_tokens = SimpleNamespace(
            token=os.getenv('GATEKEEPER_TOKEN', ''),
            AMPAuth=os.getenv('GATEKEEPER_AMP_AUTH', ''),
            AMPUser=os.getenv('GATEKEEPER_AMP_USER', ''),
            AMPPassword=os.getenv('GATEKEEPER_AMP_PASSWORD', ''),
            AMPurl=os.getenv('GATEKEEPER_AMP_URL', ''),
            SteamAPIKey=os.getenv('GATEKEEPER_STEAM_API_KEY', ''),
        )

        # token/AMPAuth/SteamAPIKey are legitimately optional per .env.template's own comments
        # (blank token = "testing AMP/DB only", blank AMPAuth = no 2FA, blank SteamAPIKey = feature disabled).
        required = {'AMPUser': env_tokens.AMPUser, 'AMPPassword': env_tokens.AMPPassword, 'AMPurl': env_tokens.AMPurl}
        if any(not v for v in required.values()):
            self.logger.dev(f'Env-var tokens incomplete, missing: {[k for k, v in required.items() if not v]}')
            return None

        self.logger.info('Loaded AMP credentials from environment variables / .env.')
        return env_tokens

    # Checks for Errors in Config
    def val_settings(self):
        """Validates the .env/environment-variable settings and 2FA."""
        self.logger.info('AMPHandler is validating your credentials...')
        reset = False

        tokens = self._load_tokens_from_env()

        if tokens is None:
            self.logger.critical(
                '**ERROR** Missing required environment variables (GATEKEEPER_AMP_USER, '
                'GATEKEEPER_AMP_PASSWORD, GATEKEEPER_AMP_URL). See .env.template.'
            )
            input("Press any Key to Exit")
            sys.exit(0)

        self.tokens = tokens
        if not tokens.AMPurl.startswith('http://') and not tokens.AMPurl.startswith('https://'):
            self.logger.critical('** Please verify your AMPurl. It either needs "http://" or "https://" depending on your AMP/Network setup. **')
            reset = True

        if tokens.AMPurl.endswith('/'):
            # self.logger.warning(f'** Please remove the forward slash at the end of {tokens.AMPurl} **, we temporarily did it for you. This may break things...')
            tokens.AMPurl = tokens.AMPurl[:-1]

        tokens.AMPAuth = tokens.AMPAuth.strip()
        if len(tokens.AMPAuth) == 0:
            self.AMP2FA = False
        elif len(tokens.AMPAuth) < 7:
            self.logger.critical('**ERROR** Please use your 2 Factor Generator Code (Should be over 25 characters long), not the 6 digit numeric generated code that expires with time.')
            reset = True
        else:
            self.AMP2FA = True

        if reset:
            input("Press any Key to Exit")
            sys.exit(0)

    def moduleHandler(self):
        """AMPs class Loader for specific server types."""
        self.logger.dev('AMPHandler moduleHandler loading modules...')
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('amp_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, script)
                        class_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(class_module)

                        # self.AMP_Modules[module_name] = getattr(class_module,f'AMP{module_name}')
                        # self.AMP_Console_Modules[module_name] = getattr(class_module,f'AMP{module_name}Console')
                        #!ATTENTION! This may change in the future. Depends on the table update.
                        for DIS in getattr(class_module, 'DisplayImageSources'):
                            self.AMP_Modules[DIS] = getattr(class_module, f'AMP{module_name}')
                            self.AMP_Console_Modules[DIS] = getattr(class_module, f'AMP{module_name}Console')

                        self.logger.dev(f'**SUCCESS** {self.name} Loading AMP Module **{module_name}**')

                    except Exception:
                        self.logger.error(f'**ERROR** {self.name} Loading AMP Module **{module_name}** - {traceback.format_exc()}')
                        continue

        except Exception:
            self.logger.error(f'**ERROR** {self.name} Loading AMP Module ** - File Not Found {traceback.format_exc()}')

    # NOTE: this parameter must NOT be named `AMP` -- that would shadow the module-level
    # `from core import AMP` for the whole function body, so `except AMP.AMPInitError` below
    # would evaluate an attribute on the AMPInstance object and raise AttributeError instead
    # of catching. It also can't be `amp_instance`, which is the loop variable further down.
    def _instanceValidation(self, main_amp: AMP.AMPInstance, startup: bool = False):
        """This checks if any new instances have been created since last check. If so, updates AMP_Instances and creates the object."""
        result = main_amp.getInstances()
        if not result or not isinstance(result, list):
            self.logger.critical(f'***ATTENTION*** Unable to retrieve AMP Instances (API call failed or returned unexpected data): {result}')
            time.sleep(30)
            return

        amp_instance_keys = list(self.AMP_Instances.keys())  # This could be empty on startup;
        available_instances = []
        # if len(result["result"][0]['AvailableInstances']) == 0:
        if len(result[0]['AvailableInstances']) == 0:
            self.logger.critical('***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)
            return

        for Target in result:
            # for Target in result["result"]:
            for amp_instance in Target['AvailableInstances']:  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']

                # This exempts the AMPTemplate Gatekeeper *hopefully* by looking at the url for the banner image; which should contain the word Gatekeeper in it.
                # This could fail if I ever design another service/template and store the display image in the same repo; unlikely though.
                if amp_instance['Module'] == 'ADS':
                    continue

                flag_reg = re.search("(gatekeeper)", amp_instance['DisplayImageSource'].lower())
                # If the flag exists and finds a match, lets continue
                if flag_reg != None and flag_reg.group():
                    continue

                # Creating a new list of Instances with just their IDs.
                available_instances.append(amp_instance['InstanceID'])

                if amp_instance['InstanceID'] in amp_instance_keys:
                    continue

                if not startup:
                    self.logger.info(f'Found a New AMP Instance since Startup; Creating AMP Object for {amp_instance["FriendlyName"]}')

                if amp_instance['DisplayImageSource'] in self.AMP_Modules:
                    name = str(self.AMP_Modules[amp_instance["DisplayImageSource"]]).split("'")[1]
                    image_source = amp_instance['DisplayImageSource']
                else:
                    name = "Generic"
                    image_source = "Generic"

                self.logger.dev(f'Loaded __{name}__ for {amp_instance["FriendlyName"]}')
                try:
                    server = self.AMP_Modules[image_source](instanceID=amp_instance['InstanceID'], serverdata=amp_instance, Handler=self)
                except AMP.AMPInitError as e:
                    # A misconfigured/unreachable game instance used to sys.exit(1) the whole
                    # process from inside AMPInstance.__init__ (or, for a game instance, hit an
                    # UnboundLocalError first -- see core/AMP.py's _bootstrap_permissions()).
                    # Neither should take the rest of the bot down over one bad server: log and
                    # skip it, leaving every other instance (and this same loop, for the rest of
                    # `result`) unaffected. It'll be retried on the next 30s instance check.
                    self.logger.error(
                        f'Failed to initialize AMP instance {amp_instance.get("FriendlyName", amp_instance["InstanceID"])} '
                        f'(InstanceID {amp_instance["InstanceID"]}): {e} -- skipping this instance.'
                    )
                    continue
                self.AMP_Instances[server.InstanceID] = server

        # AMPHandler AMP Instances will be empty on first startup; we need to NOT compare for any missing instances.
        if startup:
            return

        for instanceID in amp_instance_keys:
            if instanceID not in available_instances:
                amp_server = self.AMP_Instances[instanceID]
                self.logger.warning(f'Found the AMP Instance {amp_server.InstanceName} that no longer exists.')
                self.logger.warning(f'Removing {amp_server.InstanceName} from `Gatekeepers` available Instance list.')
                self.AMP_Instances.pop(instanceID)
                self.SessionIDlist.pop(instanceID, None)


def getAMPHandler(args: Namespace = False) -> AMPHandler:
    global Handler
    if Handler == None:
        Handler = AMPHandler(args=args)
    return Handler
