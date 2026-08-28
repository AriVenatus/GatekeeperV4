# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import logging
import pathlib
import importlib.util
import traceback

#prebuilt packages
import discord

#custom scripts
from core import AMP_Handler

#loop = asyncio.new_event_loop()
loaded = []

class Handler:
    """This is the Basic Module Loader for AMP to Discord Integration/Interactions"""
    def __init__(self, client:discord.Client):
        self._client = client

        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMP_Modules = self.AMPHandler.AMP_Modules
        self.Cog_Modules = {}

        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()} ')

    async def module_auto_loader(self):
        """This loads all the required Cogs/Scripts for each unique AMPInstance.Module type"""
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
        except Exception:
            dir_list = []
            self.logger.error(f'**ERROR** {self.name} Finding Server Cog Module ** - File Not Found {traceback.format_exc()}')

        for folder in dir_list:
            file_list = folder.glob('cog_*.py')

            for script in file_list:
                # Per-script, deliberately: this used to be one `try` around the entire nested loop,
                # so a single cog module that raised on import aborted discovery for every module
                # after it -- silently, and dependent on filesystem iteration order. Those modules
                # then fell back to Generic with nothing in the log tying it to the real cause.
                try:
                    module_name = script.name[4:-3].capitalize()
                    spec = importlib.util.spec_from_file_location(module_name, script)
                    class_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(class_module)

                    for DIS in getattr(class_module,'DisplayImageSources'):
                        self.Cog_Modules[DIS] = script

                    self.logger.dev(f'**SUCCESS** {self.name} Found Server Cog Module **{module_name}**')

                except Exception:
                    self.logger.error(f'**ERROR** {self.name} Finding Server Cog Module **{script.name}** - {traceback.format_exc()}')
                    continue

        #Just to make it easier; always load the Generic Module as a base.
        await self._client.load_extension('modules.Generic.generic')
        self.logger.dev(f'**SUCCESS** {self.name} Loading Server Cog Module **Generic**')
        loaded.append('Generic')

        #This loads the Cog Module if it finds a Instance that requires said Module.
        for instance in list(self.AMPInstances):
            DisplayImageSource = self.AMPInstances[instance].DisplayImageSource
            if DisplayImageSource not in self.Cog_Modules:
                self.logger.warning(
                    f'No Server Cog Module matches {self.AMPInstances[instance].FriendlyName}\'s DisplayImageSource '
                    f'{DisplayImageSource!r} -- only the Generic Cog applies to it. Known values: {sorted(self.Cog_Modules)}'
                )
                continue

            path = self.Cog_Modules[DisplayImageSource]
            cog = (".").join(path.as_posix().split("/")[-3:])[:-3]
            try:
                await self._client.load_extension(cog)
                self.logger.info(f'**SUCCESS** {self.name} Loading Server Cog Module **{path.stem}**')

            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                continue

            except Exception:
                self.logger.error(f'**ERROR** {self.name} Loading Server Cog Module **{path.stem}** - {traceback.format_exc()}')

        self.logger.info('**All Server Modules Loaded**')

    async def cog_auto_loader(self, reload= False):
        """This will load all Cogs inside of the cogs folder."""
        path = 'cogs' #This gets us to the folder for the module specific scripts to load via the cog.

        loaded_cogs = []
        #Grab all the cogs inside my `cogs` folder and duplicate the list.
        cog_file_list = pathlib.Path.joinpath(self._cwd,'cogs').iterdir()
        cur_cog_file_list = list(cog_file_list)

        #This while loop will force it to load EVERY cog it finds until the list is empty.
        while len(cur_cog_file_list) > 0:
            for script in cur_cog_file_list:
                #Ignore Pycache or similar files.
                #Lets Ignore our Custom Permisisons Cog. We will load it on-demand.
                if script.name.startswith('__') or script.name.lower() == 'permissions_cog.py' or not script.name.endswith('.py'):
                    self.logger.dev(f'Removed cog from loader list: {script.name}')
                    cur_cog_file_list.remove(script)
                    continue

                #bot_cog.py hosts the `/bot` group -- including this very reload command. Reloading
                #it as part of a bulk `bot cog reload` is skipped so the command tree that triggered
                #the reload can't disappear out from under itself; it's still auto-loaded normally
                #on startup (only the `reload=True` pass skips it). A process restart (`/bot utils
                #restart`) picks up code changes to this one file.
                if reload and script.name.lower() == 'bot_cog.py':
                    self.logger.dev('Skipped reloading bot_cog.py to avoid disrupting the live /bot command group.')
                    #Mark it satisfied anyway: it IS still loaded (we skipped reloading it, we didn't
                    #unload it), and the cogs that attach subcommands to `/bot` depend on it. Without
                    #this, their dependency never resolves, the dependency branch below `continue`s
                    #WITHOUT removing them from the list, and the enclosing `while` spins forever.
                    loaded_cogs.append(script.name.lower())
                    cur_cog_file_list.remove(script)
                    continue

                module_name = script.name[:-3].capitalize() #File name ofc.
                spec = importlib.util.spec_from_file_location(module_name, script)
                class_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(class_module)


                module_dependencies = getattr(class_module, 'Dependencies')
                self.logger.dev(f"Checking Dependencies on {script.name}")
                if module_dependencies != None:

                    missing_dependencies = False
                    for dependency in module_dependencies:
                        #If the cog we need isnt loaded; skip. We will come back around to it.
                        if dependency.lower() not in loaded_cogs:
                            missing_dependencies = True
                            break

                    #If our Cogs dependecies are missing; lets go onto our next cog.
                    if missing_dependencies:
                        self.logger.dev(f"Missing Dependencies: {dependency.lower()} for {script.name}")
                        continue


                cog = f'{path}.{script.name[:-3]}'

                try:
                    if reload:
                        await self._client.reload_extension(cog)
                        loaded_cogs.append(script.name.lower()) #Append to our loaded cogs for dependency check
                        cur_cog_file_list.remove(script) #Remove the entry from our cog list; so we don't attempt to load it again.

                    else:
                        await self._client.load_extension(cog)
                        loaded_cogs.append(script.name.lower()) #Append to our loaded cogs for dependency check
                        cur_cog_file_list.remove(script) #Remove the entry from our cog list; so we don't attempt to load it again.

                    self.logger.dev(f'**FINISHED LOADING** {self.name} -> **{cog}**')

                except Exception as e:
                    cur_cog_file_list.remove(script)
                    self.logger.dev(f'Removed cog from loader list: {script.name}')
                    self.logger.error(f'**ERROR** Loading Cog {script.name}** - {e} {traceback.format_exc()}')
                    continue

        self.logger.info('**All Cog Modules Loaded**')





