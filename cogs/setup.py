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

import nextcord
import os
from nextcord.ext import commands, tasks
from utils import ui

class SetupDialog:
    def __init__(self, bot):
        self.bot = bot
        self.embed = nextcord.Embed()
        self.language = self.bot.langmgr
        self.message = None
        self.user = self.bot.get_user(self.bot.owner)

    def check(self, interaction):
        return interaction.user.id == self.user.id and interaction.message.id == self.message.id

    def get(self, string):
        return self.language.get(string, 'setup.setup_menu')

    def fget(self, string, values=None):
        return self.language.fget(string, 'setup.setup_menu', values=values)

    def update(self, title, description, color=None, image_url=None, fields=None):
        self.embed.clear_fields()
        self.embed.colour = color or self.bot.colors.unifier
        self.embed.title = title
        self.embed.description = description

        if image_url:
            self.embed.set_image(url=image_url)

        if fields:
            for field in fields:
                self.embed.add_field(name=field[0], value=field[1], inline=False)

    async def start(self):
        can_skip = os.path.isdir('old') or os.path.isdir('update')

        self.update(
            self.get('welcome_title'),
            self.get('welcome_body')+'\n\n'+self.get('welcome_continue')+'\n\n'+self.get('welcome_upgraded')
            if can_skip else self.get('welcome_body')+'\n\n'+self.get('welcome_continue'),
            image_url='https://pixels.onl/images/unifier-banner.png'
        )

        components = ui.MessageComponents()

        if can_skip:
            row = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    label=self.language.get('next', 'commons.navigation'),
                    custom_id='next'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    label=self.get('skip'),
                    custom_id='skip'
                )
            )
        else:
            row = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    label=self.language.get('next','commons.navigation'),
                    custom_id='next'
                )
            )
        components.add_row(row)

        self.message = await self.user.send(embed=self.embed, view=components)
        interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)
        if interaction['custom_id'] == 'skip':
            return True
        return False

    async def boolean(self, title, description, image_url=None):
        self.update(title, description, image_url=image_url)

        components = ui.MessageComponents()
        
