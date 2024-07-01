from nextcord.ext import commands
import ujson as json
from typing import Union
from utils import log
import os

class LanguageManager:
    def __init__(self, bot):
        self.bot = bot
        self.language_base = {}
        self.language_custom = {}
        self.language_set = 'english'
        if bot:
            self.logger = log.buildlogger(self.bot.package, 'langmgr', self.bot.loglevel)
        self.__loaded = True

    def load(self):
        with open('languages/english.json', 'r') as file:
            self.language_base = json.load(file)
        if self.bot:
            for language in os.listdir('languages'):
                if language=='english.json':
                    continue
                if not language.endswith('.json'):
                    continue
                with open(f'languages/{language}.json', 'r') as file:
                    new_lang = json.load(file)
                self.language_custom.update({language[:-5]: new_lang})
            self.language_set = self.bot.config['language']
        self.__loaded = True

    def desc(self, parent):
        return self.get('description',parent)

    def get(self, string, parent: Union[commands.Context, str], default="[unknown string]", language=None):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if not language:
            language = self.language_set
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
            if self.bot:
                self.logger.error('Invalid extension in context, something is very wrong here')
            return default
        try:
            try:
                if language=='english':
                    # throw error so it uses english
                    raise Exception()
                return self.language_custom[language]['strings'][extname][cmdname][string]
            except:
                return self.language_base['strings'][extname][cmdname][string]
        except:
            if self.bot:
                self.logger.exception('An error occurred!')
            return default

    def get_formatted(self,
                      string,
                      parent: Union[commands.Context, str],
                      default=None,
                      values: dict = None,
                      language=None):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if not values:
            values = {}
        if default:
            string = self.get(string, parent, default=default, language=language)
        else:
            string = self.get(string, parent)
        return string.format(**values)

    def fget(self,
             string,
             parent: Union[commands.Context, str],
             default=None,
             values: dict = None,
             language=None):
        """Alias for get_formatted"""
        if default:
            return self.get_formatted(string, parent, default=default, values=values, language=language)
        else:
            return self.get_formatted(string, parent, default, values=values, language=language)

    def get_selector(self, parent: Union[commands.Context, str], userid: int = None):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if isinstance(parent, commands.Context):
            extlist = list(self.bot.extensions)
            extname = None
            cmdname = parent.command.qualified_name
            for x in range(len(self.bot.cogs)):
                if list(self.bot.cogs)[x]==parent.cog.qualified_name:
                    extname = extlist[x].replace('cogs.','',1)
                    break
            if not userid:
                userid = parent.author.id
        else:
            if not userid:
                raise ValueError('userid must be provided if parent is string')
            extname, cmdname = parent.split('.')
        return Selector(self, extname, cmdname, userid)

class Selector:
    def __init__(self, parent: LanguageManager, extname, cmdname, userid=None):
        self.parent = parent
        self.extname = extname
        self.cmdname = cmdname
        self.language_set = (
            self.parent.bot.db['languages'][f'{userid}'] if f'{userid}' in self.parent.bot.db['languages'].keys()
            else parent.language_set
        )
        self.userid = userid

    def rawget(self, string, parent: Union[commands.Context, str]):
        return self.parent.get(string, parent, language=self.language_set)

    def rawget_formatted(self, string, parent: Union[commands.Context, str], values: dict = None):
        return self.parent.get_formatted(string, parent, language=self.language_set, values=values)

    def rawfget(self, string, parent: Union[commands.Context, str], values: dict = None):
        return self.parent.get_formatted(string, parent, language=self.language_set, values=values)

    def get(self, string):
        return self.parent.get(string, f"{self.extname}.{self.cmdname}", language=self.language_set)

    def get_formatted(self, string, values):
        return self.parent.get_formatted(
            string, f"{self.extname}.{self.cmdname}", values=values, language=self.language_set
        )

    def fget(self, string, values):
        """Alias for get_formatted"""
        return self.parent.get_formatted(
            string, f"{self.extname}.{self.cmdname}", values=values, language=self.language_set
        )

def partial():
    # Creates a LanguageManager object without a bot
    return LanguageManager(None)
