"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

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

import discord
from discord.ext import commands
import json
from utils import log

with open('config.json', 'r') as file:
    data = json.load(file)

owner = data['owner']

class Lockdown(commands.Cog, name=':lock: Lockdown'):
    """An emergency extension that unloads literally everything."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'admin', self.bot.loglevel)

    @commands.command(hidden=True, aliases=['globalkill'])
    async def lockdown(self, ctx):
        if ctx.author.id != owner:
            return

        embed = discord.Embed(title='Activate lockdown?', description='This will unload ALL EXTENSIONS and lock down the bot until next restart. Continue?', color=0xff0000)
        btns = discord.ui.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.red, label='Continue', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel', custom_id=f'reject', disabled=False)
        )
        components = discord.ui.MessageComponents(btns)
        msg = await ctx.send(embed=embed, components=components)

        def check(interaction):
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            if interaction.custom_id == 'reject':
                return await interaction.response.edit_message(components=None)
        except asyncio.TimeoutError:
            return await msg.edit(components=None)

        embed.title = ':warning: FINAL WARNING!!! :warning:'
        embed.description = '- :warning: All functions of the bot will be disabled.\n- :no_entry_sign: Managing extensions will be unavailable.\n- :arrows_counterclockwise: To restore the bot, a reboot is required.'
        await msg.edit(embed=embed, components=None)

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            if interaction.custom_id == 'reject':
                return await interaction.response.edit_message(components=None)
        except asyncio.TimeoutError:
            return await msg.edit(components=None)

        self.logger.critical(f'Bot lockdown issued by {ctx.author.id}!')

        try:
            async with self.bot.revolt_session:
                await self.bot.revolt_session.close()
            if hasattr(self.bot, "revolt_client"):
                self.bot.unload_extension('cogs.bridge_revolt')
                del self.bot.revolt_client
                del self.bot.revolt_session
                self.logger.info("Revolt client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Revolt client shutdown failed.")

        try:
            async with self.bot.guilded_client:
                await self.bot.guilded_client.close()
            if hasattr(self.bot, "guilded_client"):
                self.bot.guilded_client_task.cancel()
                del self.bot.guilded_client
                self.bot.unload_extension('cogs.bridge_guilded')
                self.logger.info("Guilded client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Guilded client shutdown failed.")

        try:
            self.logger.info("Backing up message cache...")
            await self.bot.bridge.backup()
            self.logger.info("Backup complete")
            self.logger.info("Disabling bridge...")
            del self.bot.bridge
            self.bot.unload_extension('cogs.bridge')
            self.logger.info("Bridge disabled")
        except Exception as e:
            self.logger.exception("Bridge disabling failed.")

        # Unload all extensions except Lockdown cog
        for cog in list(self.bot.extensions):
            if cog != 'cogs.lockdown':
                self.bot.unload_extension(cog)

        self.logger.info("Lockdown complete")
        embed.title = 'Lockdown activated'
        embed.description = 'The bot is now in a crippled state. It cannot recover without a reboot.'
        await msg.edit(embed=embed, components=None)

def setup(bot):
    bot.add_cog(Lockdown(bot))
