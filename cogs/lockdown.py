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

import nextcord
from nextcord.ext import commands
from utils import log, ui, langmgr, restrictions as r

restrictions = r.Restrictions()
language = langmgr.placeholder()

class Lockdown(commands.Cog, name=':lock: Lockdown'):
    """An emergency extension that unloads literally everything.

    Developed by Green and ItsAsheer"""

    def __init__(self,bot):
        global language
        self.bot = bot
        language = self.bot.langmgr
        restrictions.attach_bot(self.bot)
        if not hasattr(self.bot, "locked"):
            self.bot.locked = False
        self.logger = log.buildlogger(self.bot.package,'admin',self.bot.loglevel)

    @commands.command(hidden=True,aliases=['globalkill'],description=language.desc('lockdown.lockdown'))
    @restrictions.owner()
    async def lockdown(self,ctx):
        selector = language.get_selector(ctx)
        if self.bot.locked:
            return await ctx.send(selector.get('already_locked'))
        embed = nextcord.Embed(
            title=selector.get('warning_title'),
            description=selector.get('warning_body'),
            color=self.bot.colors.error
        )
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label=selector.get('continue'), custom_id=f'accept', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray, label=language.get('cancel','commons.navigation'), custom_id=f'reject', disabled=False
            )
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        btns2 = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label=selector.get('continue'), custom_id=f'accept', disabled=True
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray, label=language.get('cancel','commons.navigation'), custom_id=f'reject', disabled=True
            )
        )
        components_cancel = ui.MessageComponents()
        components_cancel.add_row(btns2)
        msg = await ctx.send(embed=embed,view=components)

        def check(interaction):
            return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            return await msg.edit(view=components_cancel)
        if interaction.data['custom_id']=='reject':
            return await interaction.response.edit_message(view=components_cancel)
        embed.title = f':warning: {selector.get("fwarning_title")} :warning:'
        embed.description = f'- :warning: {selector.get("fwarning_functions")}\n- :no_entry_sign: {selector.get("fwarning_management")}\n- :arrows_counterclockwise: {selector.get("fwarning_reboot")}'
        embed.colour = self.bot.colors.critical
        await interaction.response.edit_message(embed=embed)
        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            return await msg.edit(view=components_cancel)
        if interaction.data['custom_id']=='reject':
            return await interaction.response.edit_message(view=components_cancel)

        self.logger.critical(f'Bot lockdown issued by {ctx.author.id}!')

        try:
            self.logger.info("Shutting down Revolt client...")
            await self.bot.revolt_session.close()
            del self.bot.revolt_client
            del self.bot.revolt_session
            self.bot.unload_extension('cogs.bridge_revolt')
            self.logger.info("Revolt client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Shutdown failed.")
        try:
            self.logger.info("Shutting down Guilded client...")
            await self.bot.guilded_client.close()
            self.bot.guilded_client_task.cancel()
            del self.bot.guilded_client
            self.bot.unload_extension('cogs.bridge_guilded')
            self.logger.info("Guilded client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Shutdown failed.")
        self.logger.info("Backing up message cache...")
        await self.bot.bridge.backup()
        self.logger.info("Backup complete")
        self.logger.info("Disabling bridge...")
        del self.bot.bridge
        self.bot.unload_extension('cogs.bridge')
        self.logger.info("Bridge disabled")

        self.bot.locked = True
        for cog in list(self.bot.extensions):
            if not cog=='cogs.lockdown':
                self.bot.unload_extension(cog)
        self.logger.info("Lockdown complete")

        embed.title = selector.get("success_title")
        embed.description = selector.get("success_body")
        return await interaction.response.edit_message(embed=embed,view=components_cancel)

def setup(bot):
    bot.add_cog(Lockdown(bot))
