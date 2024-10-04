"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from nextcord.ext import commands
import json
from typing import Union
from utils import log
import os

# import ujson if installed
try:
    import ujson as json  # pylint: disable=import-error
except:
    pass

class LanguageManager:
    def __init__(self, bot):
        self.__bot = bot
        self.__language_base = {}
        self.__language_custom = {}
        self.__language_set = 'english'
        if bot:
            self.logger = log.buildlogger(self.__bot.package, 'langmgr', self.__bot.loglevel)
        self.__loaded = True

    @property
    def default_language(self):
        return self.__language_set

    @property
    def languages(self):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        return ['english']+list(self.__language_custom.keys())

    def load(self):
        try:
            with open('languages/english.json', 'r') as file:
                self.__language_base = json.load(file)
        except:
            # probably didn't carry over from v2 => v3 upgrade
            with open('update/languages/english.json', 'r') as file:
                self.__language_base = json.load(file)

            if not os.path.isdir('languages'):
                # create languages folder
                os.mkdir('languages')

            with open('languages/english.json', 'w+') as file:
                # noinspection PyTypeChecker
                json.dump(self.__language_base, file, indent=4)
        if self.__bot:
            for language in os.listdir('languages'):
                if language=='english.json':
                    continue
                if not language.endswith('.json'):
                    continue
                with open(f'languages/{language}', 'r') as file:
                    new_lang = json.load(file)
                self.__language_custom.update({language[:-5]: new_lang})
            self.__language_set = self.__bot.config['language']
        self.__loaded = True

    def get_user_language(self, user):
        return self.__bot.db['languages'].get(f'{user}','english')

    def get_language_meta(self, language):
        if language == 'english':
            return {
                'language': self.__language_base['language'],
                'language_english': self.__language_base['language_english'],
                'emoji': self.__language_base['emoji'],
                'author': self.__language_base['author']
            }
        else:
            return {
                'language': self.__language_custom[language]['language'],
                'language_english': self.__language_custom[language]['language_english'],
                'emoji': self.__language_custom[language]['emoji'],
                'author': self.__language_custom[language]['author']
            }

    def desc(self, parent):
        return self.get('description',parent)

    def desc_from_all(self, command, language=None):
        try:
            base = self.__language_custom[language]['strings']
        except:
            base = self.__language_base['strings']
        for key in base.keys():
            if key == "commons":
                continue
            if command in base[key].keys():
                return self.get("description", f"{key}.{command}", language=language)
        return None

    def get(self, string, parent: Union[commands.Context, str], default="[unknown string]", language=None):
        if not self.__loaded:
            raise RuntimeError('language not loaded, run LanguageManager.load()')
        if not language:
            language = self.__language_set
        if isinstance(parent, commands.Context):
            extlist = list(self.__bot.extensions)
            extname = None
            cmdname = parent.command.qualified_name
            for x in range(len(self.__bot.cogs)):
                if self.__bot.cogs[x]==parent.cog:
                    extname = extlist[x]
                    break
        else:
            extname, cmdname = parent.split('.')
        if not extname:
            if self.__bot:
                self.logger.error('Invalid extension in context, something is very wrong here')
            return default
        try:
            try:
                if language=='english':
                    # throw error so it uses english
                    raise Exception()
                return self.__language_custom[language]['strings'][extname][cmdname][string]
            except:
                return self.__language_base['strings'][extname][cmdname][string]
        except:
            return default

    def get_formatted(self,
                      string,
                      parent: Union[commands.Context, str],
                      default="[unknown string]",
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
             default="[unknown string]",
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
            extlist = list(self.__bot.extensions)
            extname = None
            cmdname = parent.command.qualified_name
            for x in range(len(self.__bot.cogs)):
                if list(self.__bot.cogs)[x]==parent.cog.qualified_name:
                    extname = extlist[x].replace('cogs.','',1)
                    break
            if not userid:
                userid = parent.author.id
        else:
            if not userid:
                raise ValueError('userid must be provided if parent is string')
            extname, cmdname = parent.split('.')
        return Selector(self, self.__bot, extname, cmdname, userid)

class Selector:
    def __init__(self, parent: LanguageManager, bot, extname, cmdname, userid=None):
        self.__parent = parent
        self.__extname = extname
        self.__cmdname = cmdname
        self.__bot = bot
        self.__language_set = (
            self.__bot.db['languages'][f'{userid}'] if f'{userid}' in self.__bot.db['languages'].keys()
            else parent.default_language
        )
        self.userid = userid

    @property
    def extname(self):
        return self.__extname
    
    @property
    def cmdname(self):
        return self.__cmdname

    def rawget(self, string, parent: Union[commands.Context, str], default="[unknown string]"):
        return self.__parent.get(string, parent, language=self.__language_set, default=default)

    def rawget_formatted(self, string, parent: Union[commands.Context, str], values: dict = None, default="[unknown string]"):
        return self.__parent.get_formatted(string, parent, language=self.__language_set, values=values, default=default)

    def rawfget(self, string, parent: Union[commands.Context, str], values: dict = None, default="[unknown string]"):
        return self.__parent.get_formatted(string, parent, language=self.__language_set, values=values, default=default)

    def get(self, string, default="[unknown string]"):
        return self.__parent.get(string, f"{self.__extname}.{self.__cmdname}", language=self.__language_set, default=default)

    def get_formatted(self, string, values, default="[unknown string]"):
        return self.__parent.get_formatted(
            string, f"{self.__extname}.{self.__cmdname}", values=values, language=self.__language_set, default=default
        )

    def desc_from_all(self, string):
        return self.__parent.desc_from_all(string, self.__language_set)

    def fget(self, string, values):
        """Alias for get_formatted"""
        return self.__parent.get_formatted(
            string, f"{self.__extname}.{self.__cmdname}", values=values, language=self.__language_set
        )

def partial():
    # Creates a LanguageManager object without a bot
    return LanguageManager(None)
