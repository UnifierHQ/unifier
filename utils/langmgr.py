from nextcord.ext import commands
import os
import ujson as json
from typing import Union
from utils import log

class LanguageManager:
    def __init__(self, bot):
        self.bot = bot
        self.language = {}
        self.logger = log.buildlogger(self.bot.package, 'langmgr', self.bot.loglevel)
        self.__loaded = True

    def load(self, language=None):
        if not language:
            try:
                with open('languages/current.json', 'r') as file:
                    self.language = json.load(file)
            except:
                os.system('cp languages/english.json languages/current.json')
                with open('languages/current.json', 'r') as file:
                    self.language = json.load(file)
        else:
            with open('languages/'+language+'.json', 'r') as file:
                self.language = json.load(file)
        self.__loaded = True

    def desc(self, parent):
        return self.get('description',parent)

    def get(self, string, parent: Union[commands.Context, str], default="ERROR: Tell an admin to check console"):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if isinstance(parent, commands.Context):
            extlist = list(self.bot.extensions)
            extname = None
            cmdname = parent.command.qualified_name
            for x in range(len(self.bot.cogs)):
                if self.bot.cogs[x]==parent.cog:
                    extname = extlist[x]
                    break
        else:
            extname, cmdname = parent.split('.')
        if not extname:
            self.logger.error('Invalid extension in context, something is very wrong here')
            return default
        try:
            return self.language['strings'][extname][cmdname][string]
        except:
            self.logger.exception('An error occurred!')
            return default

    def get_formatted(self,
                      string,
                      parent: Union[commands.Context, str],
                      default=None,
                      values: dict = None):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if not values:
            values = {}
        if default:
            string = self.get(string, parent, default=default)
        else:
            string = self.get(string, parent)
        return string.format(**values)

    def fget(self,
             string,
             parent: Union[commands.Context, str],
             default=None,
             values: dict = None):
        """Alias for get_formatted"""
        if default:
            return self.get_formatted(string, parent, default=default, values=values)
        else:
            return self.get_formatted(string, parent, default, values=values)

    def get_selector(self, parent: Union[commands.Context, str]):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if isinstance(parent, commands.Context):
            extlist = list(self.bot.extensions)
            extname = None
            cmdname = parent.command.qualified_name
            for x in range(len(self.bot.cogs)):
                if self.bot.cogs[x]==parent.cog:
                    extname = extlist[x]
                    break
        else:
            extname, cmdname = parent.split('.')
        return Selector(self, extname, cmdname)

class Selector:
    def __init__(self, parent: LanguageManager, extname, cmdname):
        self.parent = parent
        self.extname = extname
        self.cmdname = cmdname

    def get(self, string):
        return self.parent.get(string, f"{self.extname}.{self.cmdname}")

    def get_formatted(self, string, values):
        return self.parent.get_formatted(string, f"{self.extname}.{self.cmdname}", values=values)

    def fget(self, string, values):
        """Alias for get_formatted"""
        return self.parent.get_formatted(string, f"{self.extname}.{self.cmdname}", values=values)

def placeholder():
    # placeholder class so IDE doesn't complain
    return LanguageManager(None)