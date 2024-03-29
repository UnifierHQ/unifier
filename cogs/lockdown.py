"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
import json
import traceback

with open('config.json', 'r') as file:
    data = json.load(file)
owner = data['owner']

def log(type='???',status='ok',content='None'):
    from time import gmtime, strftime
    time1 = strftime("%Y.%m.%d %H:%M:%S", gmtime())
    if status=='ok':
        status = ' OK  '
    elif status=='error':
        status = 'ERROR'
    elif status=='warn':
        status = 'WARN '
    elif status=='info':
        status = 'INFO '
    else:
        status = ' N/A '
    print(f'[{type} | {time1} | {status}] {content}')

class Lockdown(commands.Cog, name=':lock: Lockdown'):
    """An emergency extension that unloads literally everything.

    Developed by Green and ItsAsheer"""
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(self.bot, "locked"):
            self.bot.locked = False

    @commands.command(hidden=True,aliases=['globalkill'])
    async def lockdown(self,ctx):
        if not ctx.author.id==owner:
            return
        if self.bot.locked:
            return await ctx.send('Bot is already locked down.')
        embed = discord.Embed(title='Activate lockdown?',description='This will unload ALL EXTENSIONS and lock down the bot until next restart. Continue?',color=0xff0000)
        btns = discord.ui.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.red, label='Continue', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel', custom_id=f'reject', disabled=False)
        )
        components = discord.ui.MessageComponents(btns)
        btns2 = discord.ui.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.red, label='Continue', custom_id=f'accept', disabled=True),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel', custom_id=f'reject', disabled=True)
        )
        components_cancel = discord.ui.MessageComponents(btns2)
        msg = await ctx.send(embed=embed,components=components)

        def check(interaction):
            return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            return await msg.edit(components=components_cancel)
        if interaction.custom_id=='reject':
            return await interaction.response.edit_message(components=components_cancel)
        embed.title = ':warning: FINAL WARNING!!! :warning:'
        embed.description = '- :warning: All functions of the bot will be disabled.\n- :no_entry_sign: Managing extensions will be unavailable.\n- :arrows_counterclockwise: To restore the bot, a reboot is required.'
        await interaction.response.edit_message(embed=embed)
        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            return await msg.edit(components=components_cancel)
        if interaction.custom_id=='reject':
            return await interaction.response.edit_message(components=components_cancel)

        log('BOT', 'error', f'Bot lockdown issued by {ctx.author.id}!')

        try:
            log("RVT", "info", "Shutting down Revolt client...")
            await self.bot.revolt_session.close()
            del self.bot.revolt_client
            del self.bot.revolt_session
            self.bot.unload_extension('cogs.bridge_revolt')
            log("RVT", "ok", "Revolt client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                log("RVT", "error", "Shutdown failed.")
                traceback.print_exc()
        try:
            log("GLD", "info", "Shutting down Guilded client...")
            await self.bot.guilded_client.close()
            self.bot.guilded_client_task.cancel()
            del self.bot.guilded_client
            self.bot.unload_extension('cogs.bridge_guilded')
            log("GLD", "ok", "Guilded client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                log("GLD", "error", "Shutdown failed.")
                traceback.print_exc()
        log("SYS", "info", "Backing up message cache...")
        await self.bot.bridge.backup()
        log("SYS", "ok", "Backup complete")
        log("SYS", "info", "Disabling bridge...")
        del self.bot.bridge
        self.bot.unload_extension('cogs.bridge')
        log("SYS", "ok", "Bridge disabled")

        self.bot.locked = True
        for cog in list(self.bot.extensions):
            if not cog=='cogs.lockdown':
                self.bot.unload_extension(cog)
        log("SYS", "ok", "Lockdown complete")

        embed.title = 'Lockdown activated'
        embed.description = 'The bot is now in a crippled state. It cannot recover without a reboot.'
        return await interaction.response.edit_message(embed=embed,components=components_cancel)

def setup(bot):
    bot.add_cog(Lockdown(bot))