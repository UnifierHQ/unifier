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
import asyncio
from nextcord.ext import commands
from utils import ui, log
import json
import sys
import time
import tomli
import tomli_w

try:
    import ujson as json
except:
    pass

class SetupDialog:
    def __init__(self, bot):
        self.bot = bot
        self.embed = nextcord.Embed()
        self.language = self.bot.langmgr
        self.message = None
        self.user = self.bot.get_user(self.bot.owner)

    def check(self, interaction):
        return interaction.user.id == self.user.id and interaction.message.id == self.message.id

    def rawget(self, string, parent):
        return self.language.get(string, parent)

    def get(self, string):
        return self.language.get(string, 'setup.setup_menu')

    def fget(self, string, values=None):
        return self.language.fget(string, 'setup.setup_menu', values=values)

    def update(self, title, description, color=None, image_url=None, fields=None):
        self.embed.clear_fields()
        self.embed.colour = color or self.bot.colors.unifier
        self.embed.title = title
        self.embed.description = description
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
        await interaction.response.defer(ephemeral=False, with_message=False)

        if interaction.data['custom_id'] == 'skip':
            return True
        return False

    async def finish(self, skipped=False):
        self.update(
            self.get('finish_title'),
            self.get('finish_body') + '\n' + self.get('finish_reboot')
        )

        components = ui.MessageComponents()
        row = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple,
                label=self.rawget('restart', 'commons.navigation')
            )
        )
        components.add_row(row)

        if skipped:
            self.update(
                self.get('finish_title'),
                self.get('finish_body')
            )
            components = None

        await self.message.edit(embed=self.embed, view=components)

        if skipped:
            return

        interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)
        await interaction.response.edit_message(view=None)

        x = open('.restart', 'w+')
        x.write(f'{time.time()}')
        x.close()

        await self.bot.session.close()
        await self.bot.close()
        sys.exit(0)

    async def boolean(self, title, description, image_url=None):
        self.update(title, description, image_url=image_url)

        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green,
                    label=self.rawget('yes', 'commons.navigation'),
                    custom_id='yes'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=self.rawget('no', 'commons.navigation'),
                    custom_id='no'
                )
            )
        )

        await self.message.edit(embed=self.embed, view=components)

        interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)
        await interaction.response.defer(ephemeral=False,with_message=False)
        return interaction.data['custom_id'] == 'yes'

    async def range(self, title, description, image_url=None, max_value=100, min_value=0, default=0):
        self.update(title, description, image_url=image_url)

        value = default

        while True:
            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        label='-10',
                        custom_id='sub10',
                        disabled=(value - 10) < min_value
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        label='-1',
                        custom_id='sub1',
                        disabled=(value - 1) < min_value
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=str(value),
                        custom_id='value',
                        disabled=True
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='+1',
                        custom_id='add1',
                        disabled=(value + 1) > max_value
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='+10',
                        custom_id='add10',
                        disabled=(value + 10) > max_value
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=self.rawget('confirm', 'commons.navigation'),
                        custom_id='confirm'
                    )
                )
            )
            await self.message.edit(embed=self.embed, view=components)

            interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)
            await interaction.response.defer(ephemeral=False, with_message=False)

            if interaction.data['custom_id'] == 'confirm':
                break

            if interaction.data['custom_id'] == 'add1':
                value += 1
            elif interaction.data['custom_id'] == 'add10':
                value += 10
            elif interaction.data['custom_id'] == 'sub1':
                value -= 1
            elif interaction.data['custom_id'] == 'sub10':
                value -= 10

            if value < min_value:
                value = min_value
            elif value > max_value:
                value = max_value

        return value

    async def choice(self, title, description, image_url=None, choices=None):
        if not choices:
            return None

        self.update(title, description, image_url=image_url)

        value = None

        for choice in choices:
            if choice.default:
                value = choice.value
                break

        while True:
            if value:
                for index in range(choices):
                    choices[index].default = choices[index].custom_id == value

            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.StringSelect(
                        placeholder=self.rawget('select', 'commons.navigation'),
                        options=choices,
                        custom_id='selection'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=self.rawget('confirm', 'commons.navigation'),
                        custom_id='confirm',
                        disabled=value is None
                    )
                )
            )
            await self.message.edit(embed=self.embed, view=components)

            interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)
            await interaction.response.defer(ephemeral=False, with_message=False)

            if interaction.data['custom_id'] == 'confirm':
                break
            else:
                value = interaction.data['values'][0]

        return value

    async def server_feature(self, title, description, image_url=None, server=None, feature='roles'):
        if not server:
            return None

        self.update(title, description, image_url=image_url)

        value = None

        def get_choices():
            old_choices = []
            new_choices = []

            if feature == 'roles':
                old_choices = server.roles

                for choice in old_choices:
                    if choice.name == '@everyone' or choice.managed:
                        old_choices.remove(choice)
            elif feature == 'channels':
                old_choices = server.channels
            elif feature == 'members':
                old_choices = server.members

            if len(old_choices) > 25:
                old_choices = old_choices[:25]

            for index in range(len(old_choices)):
                choice = old_choices[index]
                name = (choice.global_name or choice.name) if feature == 'members' else choice.name
                new_choices.append(nextcord.SelectOption(label=name, value=f'{choice.id}'))

            return new_choices

        choices = get_choices()
        if len(choices) == 0:
            return -1

        modal = nextcord.ui.Modal(title=self.get('custom'), custom_id='modal', auto_defer=False)
        modal.add_item(
            nextcord.ui.TextInput(
                label=self.get('custom'),
                style=nextcord.TextInputStyle.short,
                placeholder=self.get('integer'),
                required=True
            )
        )

        while True:
            if value:
                for index in range(len(choices)):
                    choices[index].default = choices[index].value == value

            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.StringSelect(
                        placeholder=self.rawget('select', 'commons.navigation'),
                        options=choices,
                        custom_id='selection'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=self.rawget('confirm', 'commons.navigation'),
                        custom_id='confirm',
                        disabled=value is None
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=self.get('refresh'),
                        custom_id='refresh'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=self.get('custom'),
                        custom_id='custom'
                    )
                )
            )
            await self.message.edit(embed=self.embed, view=components)

            interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)

            if not interaction.data['custom_id'] == 'custom':
                await interaction.response.defer(ephemeral=False, with_message=False)

            if interaction.data['custom_id'] == 'confirm':
                break
            elif interaction.data['custom_id'] == 'refresh':
                value = None
                choices = get_choices()
            elif interaction.data['custom_id'] == 'custom':
                await interaction.response.send_modal(modal)
            elif interaction.data['custom_id'] == 'modal':
                try:
                    value = int(interaction.data['components'][0]['components'][0]['value'])

                    if value < 1:
                        # this cannot be a valid ID
                        continue

                    break
                except:
                    pass
            else:
                value = interaction.data['values'][0]

        return value

    async def custom(self, title, description, image_url=None, modal=None, defaults=None, can_skip=False):
        if not modal:
            return None
        if modal.custom_id == 'summon_modal':
            return None

        self.update(title, description, image_url=image_url)

        values = []

        while True:
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=self.rawget('enter', 'commons.navigation'),
                        custom_id='summon_modal'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=self.get('skip'),
                        custom_id='skip',
                        disabled=not can_skip
                    )
                )
            )
            await self.message.edit(embed=self.embed, view=components)

            interaction = await self.bot.wait_for('interaction', check=self.check, timeout=300)

            if interaction.data['custom_id'] == 'summon_modal':
                await interaction.response.send_modal(modal)
            elif interaction.data['custom_id'] == 'skip':
                await interaction.response.defer(ephemeral=False, with_message=False)
                values = defaults
                break
            else:
                for index in range(len(interaction.data['components'])):
                    value = interaction.data['components'][index]['components'][0]['value']

                    if not value:
                        value = defaults[index]

                    values.append(value)

                await interaction.response.defer(ephemeral=False, with_message=False)
                break

        return values

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'setup', self.bot.loglevel)

        with open('.install.json') as file:
            install_data = json.load(file)

        if not install_data['setup']:
            self.bot.setup_task = asyncio.create_task(self.setup())

    async def setup(self):
        self.logger.info('Running setup')
        ignore_error = False
        try:
            can_skip = os.path.isdir('old') or os.path.isdir('update')
            if not can_skip:
                self.bot.setup_lock = True

            setup_dialog = SetupDialog(self.bot)
            skip = await setup_dialog.start()

            if skip:
                ignore_error = True
                return await setup_dialog.finish(skipped=True)

            if not self.bot.setup_lock:
                self.bot.setup_lock = True

            server = self.bot.get_guild(self.bot.config['home_guild'])

            if not server:
                self.logger.critical('Home server is misconfigured, setup cannot proceed!')
                sys.exit(0)

            modal = nextcord.ui.Modal(title=setup_dialog.get('prefix_title'),auto_defer=False)
            modal.add_item(
                nextcord.ui.TextInput(
                    label=setup_dialog.get('prefix_title'),
                    style=nextcord.TextInputStyle.short,
                    placeholder=setup_dialog.get('string'),
                    required=True,
                    default_value='u!'
                )
            )

            prefix = await setup_dialog.custom(
                setup_dialog.get('prefix_title'),
                setup_dialog.get('prefix_body')+'\n'+setup_dialog.get('prefix_default'),
                modal=modal,
                defaults='u!',
                can_skip=True
            )

            prefix = prefix[0]

            backup_freq = await setup_dialog.range(
                setup_dialog.get('backup_title'),
                setup_dialog.get('backup_body')+'\n'+setup_dialog.get('backup_nobackup'),
                max_value=86400,
                default=0
            )

            periodic_freq = await setup_dialog.range(
                setup_dialog.get('ping_title'),
                setup_dialog.get('ping_body') + '\n' + setup_dialog.get('ping_noping'),
                max_value=86400,
                default=0
            )

            modal = nextcord.ui.Modal(title=setup_dialog.get('main_title'), auto_defer=False)
            modal.add_item(
                nextcord.ui.TextInput(
                    label=setup_dialog.get('main_title'),
                    style=nextcord.TextInputStyle.short,
                    placeholder=setup_dialog.get('string'),
                    required=True,
                    default_value='main'
                )
            )

            main_room = await setup_dialog.custom(
                setup_dialog.get('main_title'),
                setup_dialog.get('main_body') + '\n' + setup_dialog.get('main_name') + '\n' + setup_dialog.get('main_default'),
                modal=modal,
                defaults='main',
                can_skip=True
            )

            main_room = main_room[0]

            enable_ctx = await setup_dialog.boolean(
                setup_dialog.get('ctx_title'),
                setup_dialog.get('ctx_body') + '\n' + setup_dialog.get('ctx_required'),
            )

            mod_role = -1
            logging = False
            reporting = False
            logging_edit = False
            logging_delete = False
            logging_channel = -1
            reports_channel = -1

            if enable_ctx:
                mod_role = await setup_dialog.server_feature(
                    setup_dialog.get('mod_title'),
                    setup_dialog.get('mod_body'),
                    server=server,
                    feature='roles'
                )

                logging = await setup_dialog.boolean(
                    setup_dialog.get('logging_title'),
                    setup_dialog.get('logging_body') + '\n' + setup_dialog.get('logging_actions'),
                )

                if logging:
                    logging_channel = await setup_dialog.server_feature(
                        setup_dialog.get('channel_title'),
                        setup_dialog.get('channel_body'),
                        server=server,
                        feature='channels'
                    )

                    logging_edit = await setup_dialog.boolean(
                        setup_dialog.get('edit_title'),
                        setup_dialog.get('edit_body')
                    )

                    logging_delete = await setup_dialog.boolean(
                        setup_dialog.get('delete_title'),
                        setup_dialog.get('delete_body')
                    )

                    reporting = await setup_dialog.boolean(
                        setup_dialog.get('reporting_title'),
                        setup_dialog.get('reporting_body')
                    )

                    if reporting:
                        reports_channel = await setup_dialog.server_feature(
                            setup_dialog.get('rchannel_title'),
                            setup_dialog.get('rchannel_body'),
                            server=server,
                            feature='channels'
                        )

            safefile = await setup_dialog.boolean(
                setup_dialog.get('safefile_title'),
                setup_dialog.get('safefile_body') + '\n' + setup_dialog.get('safefile_block')
            )

            posts = await setup_dialog.boolean(
                setup_dialog.get('posts_title'),
                setup_dialog.get('posts_body') + '\n' + setup_dialog.get('posts_info')
            )

            proom = 'posts'
            pcomment = 'posts-comments'

            if posts:
                modal = nextcord.ui.Modal(title=setup_dialog.get('proom_name'), auto_defer=False)
                modal.add_item(
                    nextcord.ui.TextInput(
                        label=setup_dialog.get('proom_name'),
                        style=nextcord.TextInputStyle.short,
                        placeholder=setup_dialog.get('string'),
                        required=True,
                        default_value='posts'
                    )
                )

                proom = await setup_dialog.custom(
                    setup_dialog.get('proom_title'),
                    setup_dialog.get('proom_body') + '\n' + setup_dialog.get('proom_name') + '\n' + setup_dialog.get('proom_default'),
                    modal=modal,
                    defaults='posts',
                    can_skip=True
                )

                proom = proom[0]

                modal = nextcord.ui.Modal(title=setup_dialog.get('pcomment_name'), auto_defer=False)
                modal.add_item(
                    nextcord.ui.TextInput(
                        label=setup_dialog.get('pcomment_name'),
                        style=nextcord.TextInputStyle.short,
                        placeholder=setup_dialog.get('string'),
                        required=True,
                        default_value='posts-comments'
                    )
                )

                pcomment = await setup_dialog.custom(
                    setup_dialog.get('pcomment_title'),
                    setup_dialog.get('pcomment_body') + '\n' + setup_dialog.get('pcomment_name') + '\n' + setup_dialog.get('pcomment_default'),
                    modal=modal,
                    defaults='posts-comments',
                    can_skip=True
                )

                pcomment = pcomment[0]

            alerts = await setup_dialog.boolean(
                setup_dialog.get('alerts_title'),
                setup_dialog.get('alerts_body') + '\n' + setup_dialog.get('alerts_info')
            )

            aroom = 'alerts'

            if alerts:
                modal = nextcord.ui.Modal(title=setup_dialog.get('proom_name'), auto_defer=False)
                modal.add_item(
                    nextcord.ui.TextInput(
                        label=setup_dialog.get('proom_name'),
                        style=nextcord.TextInputStyle.short,
                        placeholder=setup_dialog.get('string'),
                        required=True,
                        default_value='posts'
                    )
                )

                aroom = await setup_dialog.custom(
                    setup_dialog.get('aroom_title'),
                    setup_dialog.get('aroom_body') + '\n' + setup_dialog.get('aroom_name') + '\n' + setup_dialog.get('aroom_default'),
                    modal=modal,
                    defaults='alerts',
                    can_skip=True
                )

                aroom = aroom[0]

            with open('config.toml', 'rb') as file:
                config = tomli.load(file)

            config['bot']['prefix'] = prefix
            config['backups']['periodic_backup'] = backup_freq
            config['bot']['ping'] = periodic_freq
            config['bridge']['main_room'] = main_room
            config['bridge']['enable_ctx_commands'] = enable_ctx
            config['moderation']['moderator_role'] = mod_role
            config['moderation']['enable_logging'] = logging
            config['moderation']['enable_reporting'] = reporting
            config['moderation']['logging_edit'] = logging_edit
            config['moderation']['logging_delete'] = logging_delete
            config['moderation']['logs_channel'] = logging_channel
            config['moderation']['reports_channel'] = reports_channel
            config['bridge']['safe_filetypes'] = safefile
            config['bridge']['allow_posts'] = posts
            config['bridge']['posts_room'] = proom
            config['bridge']['posts_ref_room'] = pcomment
            config['bridge']['enable_safety_alerts'] = alerts
            config['bridge']['alerts_room'] = aroom

            with open('config.toml', 'wb') as file:
                tomli_w.dump(config, file)

            with open('.install.json') as file:
                install_data = json.load(file)

            install_data['setup'] = True

            with open('.install.json', 'w') as file:
                json.dump(install_data, file)

            ignore_error = True
            return await setup_dialog.finish()
        except:
            if not ignore_error:
                self.logger.critical('An error occured!')
                user = self.bot.get_user(self.bot.owner)
                await user.send('An error occured during setup. The bot will now shut down.')
                sys.exit(1)

def setup(bot):
    bot.add_cog(Setup(bot))
