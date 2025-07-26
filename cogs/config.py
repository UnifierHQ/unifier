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
from nextcord.ext import commands, application_checks
import traceback
import re
from utils import log, ui, langmgr, restrictions as r, restrictions_legacy as r_legacy, slash as slash_helper, base_filter
import math
import emoji as pymoji
import time
import asyncio
from typing import Union, Optional

restrictions = r.Restrictions()
restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_helper.SlashHelper(language)

# Room settings keys
settings_keys = [
    'relay_deletes', 'relay_edits', 'relay_forwards', 'dynamic_reply_embed', 'compact_reply', 'nsfw',
    'bridge_large_attachments'
]
settings_defaults = {
    'relay_deletes': True, 'relay_edits': True, 'relay_forwards': True, 'dynamic_reply_embed': False,
    'compact_reply': True, 'nsfw': False, 'bridge_large_attachments': False
}

def timetoint(t):
    try:
        return int(t)
    except:
        pass
    if not type(t) is str:
        t = str(t)
    total = 0
    if t.count('d')>1 or t.count('w')>1 or t.count('h')>1 or t.count('m')>1 or t.count('s')>1:
        raise ValueError('each identifier should never recur')
    t = t.replace('n','n ').replace('d','d ').replace('w','w ').replace('h','h ').replace('m','m ').replace('s','s ')
    times = t.split()
    for part in times:
        if part.endswith('d'):
            multi = int(part[:-1])
            total += (86400 * multi)
        elif part.endswith('w'):
            multi = int(part[:-1])
            total += (604800 * multi)
        elif part.endswith('h'):
            multi = int(part[:-1])
            total += (3600 * multi)
        elif part.endswith('m'):
            multi = int(part[:-1])
            total += (60 * multi)
        elif part.endswith('s'):
            multi = int(part[:-1])
            total += multi
        else:
            raise ValueError('invalid identifier')
    return total

class FilterDialog:
    def __init__(self, bot, ctx: Union[nextcord.Interaction, commands.Context], room=None, query=None):
        self.ctx = ctx
        self.__bot = bot
        self.room = room
        self.message = None
        self.embed = nextcord.Embed(color=self.__bot.colors.unifier)
        self.selector = language.get_selector(ctx)
        self.selection = None
        self.query = query
        self.modal = None
        self.filter = None
        self.config = None
        self.maxpage = 0
        self.match_both = False
        self.match_name = True
        self.match_desc = True
        self.global_filters = not room
        self.title = self.__bot.ui_emojis.rooms + ' ' + (
            self.selector.get('title_global') if self.global_filters else
            self.selector.fget('title',values={'room':self.room})
        )

    @property
    def author(self):
        if type(self.ctx) is nextcord.Interaction:
            return self.ctx.user
        else:
            return self.ctx.author

    async def sanitize(self):
        self.embed.clear_fields()
        self.embed.remove_author()
        self.embed.remove_footer()
        self.selection = None

    async def menu(self, search: Optional[str] = None, page: int = 0):
        await self.sanitize()

        if search:
            filters = dict(self.__bot.bridge.filters)
            keys = list(filters.keys())
            for bridge_filter in keys:
                # noinspection PyTypeChecker
                filter_obj: base_filter.BaseFilter = filters[bridge_filter]
                if self.match_both:
                    if not (
                            (
                                    (search.lower() in bridge_filter.lower() if self.match_name else True) or
                                    (search.lower() in filter_obj.name.lower() if self.match_name else True)
                            ) and (
                                    search.lower() in filter_obj.description.lower() if self.match_desc else True
                            )
                    ):
                        filters.pop(bridge_filter)
                else:
                    if not (
                            (
                                    (search.lower() in bridge_filter.lower() if self.match_name else True) or
                                    (search.lower() in filter_obj.name.lower() if self.match_name else True)
                            ) or (
                                    search.lower() in filter_obj.description.lower() if self.match_desc else True
                            )
                    ):
                        filters.pop(bridge_filter)
            self.embed.description = self.selector.rawfget(
                "search_results", "commons.search", values={"query": search, "results": len(filters)}
            )
        else:
            filters = dict(self.__bot.bridge.filters)
            self.embed.description = self.selector.get('choose_filter')

        roomdata = self.__bot.bridge.get_room(self.room)
        limit = 20
        maxpage = math.ceil(len(filters)/limit)-1
        self.maxpage = maxpage

        if page > maxpage:
            page = maxpage
        elif page < 0:
            page = 0

        offset = page * limit

        self.embed.title = self.title

        self.selection = nextcord.ui.StringSelect(
            max_values=1, min_values=1, custom_id='selection', placeholder=self.selector.get("selection")
        )

        for index in range(limit):
            if index + offset >= len(filters) or len(filters) == 0:
                break

            # noinspection PyTypeChecker
            filter_obj = filters[list(filters.keys())[index + offset]]

            if roomdata['meta']['filters'].get(filter_obj.id, {}).get('enabled', False):
                self.embed.add_field(
                    name=f'{self.__bot.ui_emojis.success} **{filter_obj.name} (`{filter_obj.id}`)**',
                    value=filter_obj.description or self.selector.get("no_desc"),
                    inline=False
                )
            else:
                self.embed.add_field(
                    name=f'{filter_obj.name} (`{filter_obj.id}`)',
                    value=filter_obj.description or self.selector.get("no_desc"),
                    inline=False
                )

            trimmed = filter_obj.description or self.selector.get("no_desc")
            if len(trimmed) > 100:
                trimmed = trimmed[:97] + '...'

            self.selection.add_option(
                label=filter_obj.name,
                description=trimmed,
                value=filter_obj.id
            )

        if len(self.embed.fields) == 0:
            self.selection.disabled = True
            self.selection.add_option(
                label='placeholder',
                value='placeholder'
            )
            self.embed.add_field(
                name=self.selector.get('noresults_title'),
                value=(
                    self.selector.get("noresults_body_search") if search else
                    self.selector.get("noresults_body_filters")
                ),
                inline=False
            )

        self.embed.set_footer(text=self.selector.rawfget("page", "commons.search", values={
            "page": page + 1, "maxpage": maxpage + 1
        }))

    async def display(self, bridge_filter: base_filter.BaseFilter, searched: bool = False):
        await self.sanitize()

        self.embed.title = self.title + f' / {bridge_filter.id}'
        if searched:
            self.embed.title = self.title + f' / {self.selector.get("search")} / {bridge_filter.id}'

        roomdata = self.__bot.bridge.get_room(self.room)

        self.embed.description = (
            f'{bridge_filter.description or self.selector.get("no_desc")}\n\n' +
            (
                self.selector.fget("enabled", values={"emoji": self.__bot.ui_emojis.success})
                if roomdata['meta']['filters'].get(bridge_filter.id, {}).get('enabled', False)
                else self.selector.fget("disabled", values={"emoji": self.__bot.ui_emojis.error})
            )
        )

        self.selection = nextcord.ui.StringSelect(
            max_values=1, min_values=1, custom_id='selection', placeholder=self.selector.get("selection_config")
        )

        configs = bridge_filter.configs
        for config in configs:
            self.embed.add_field(
                name=configs[config].name,
                value=configs[config].description or self.selector.get("no_desc"),
                inline=False
            )

            self.selection.add_option(
                label=configs[config].name,
                description=configs[config].description or self.selector.get("no_desc"),
                value=config
            )

        if not roomdata['meta']['filters'].get(bridge_filter.id, {}).get('enabled', False):
            self.selection.disabled = True

    async def display_config(self, bridge_filter: base_filter.BaseFilter, option: str, searched: bool = False):
        await self.sanitize()
        roomdata = self.__bot.bridge.get_room(self.room)

        config = bridge_filter.configs[option]
        value = roomdata['meta']['filters'].get(bridge_filter.id, {}).get(option, config.default)

        self.embed.title = self.title + f' / {bridge_filter.id} / {option}'
        if searched:
            self.embed.title = self.title + f' / {self.selector.get("search")} / {bridge_filter.id} / {option}'

        textinput = nextcord.ui.TextInput(
            label=self.selector.get('value'),
            style=nextcord.TextInputStyle.short,
            placeholder=self.selector.get("value_prompt"),
            default_value=str(value)
        )

        limittext = None
        if config.limits:
            if config.type == 'string':
                limittext = f'{self.selector.fget("limit_str",values={"lower":config.limits[0],"upper":config.limits[1]})}'
                textinput.min_length = config.limits[0]
                textinput.max_length = config.limits[1]
            elif config.type == 'number' or config.type == 'integer' or config.type == 'float':
                limittext = f'{self.selector.fget("limit_num",values={"lower":config.limits[0],"upper":config.limits[1]})}'

        valuetext = '`'+str(value)+'`'
        if len(valuetext) > 1024:
            valuetext = valuetext[:1020] + '...`'

        if config.type == 'boolean':
            valuetext = (
                f'{self.__bot.ui_emojis.success} {self.selector.get("enabled_config")}' if value else
                f'{self.__bot.ui_emojis.error} {self.selector.get("disabled_config")}'
            )

        self.embed.description = f'# {config.name} (`{option}`)\n{config.description}'
        self.embed.add_field(name=self.selector.get('current'), value=valuetext, inline=False)

        if limittext:
            self.embed.add_field(name=self.selector.get('limits'), value=limittext, inline=False)

        self.modal = nextcord.ui.Modal(
            title=self.selector.get('form_title'),
            auto_defer=False
        )

        self.modal.add_item(
            textinput
        )

    async def run(self):
        page = 0
        panel = 0
        if self.query:
            panel = 1

        interaction = None
        while True:
            buttons = []
            if panel == 0:
                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('prev', 'commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.__bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('next', 'commons.navigation'),
                            custom_id='next',
                            disabled=page >= self.maxpage,
                            emoji=self.__bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=self.selector.rawget('search', 'commons.search'),
                            custom_id='search',
                            emoji=self.__bot.ui_emojis.search
                        )
                    ]
                ]
                await self.menu(page=page)
            elif panel == 1:
                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('prev', 'commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.__bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('next', 'commons.navigation'),
                            custom_id='next',
                            disabled=page >= self.maxpage,
                            emoji=self.__bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=self.selector.rawget('search', 'commons.search'),
                            custom_id='search',
                            emoji=self.__bot.ui_emojis.search
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            custom_id='match',
                            label=(
                                self.selector.rawget('match_any', 'commons.search') if not self.match_both else
                                self.selector.rawget('match_both', 'commons.search')
                            ),
                            style=(
                                nextcord.ButtonStyle.green if not self.match_both else
                                nextcord.ButtonStyle.blurple
                            ),
                            emoji=(
                                '\U00002194' if not self.match_both else
                                '\U000023FA'
                            )
                        ),
                        nextcord.ui.Button(
                            custom_id='name',
                            label=self.selector.get("filter_name"),
                            style=nextcord.ButtonStyle.green if self.match_name else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label=self.selector.get("filter_desc"),
                            style=nextcord.ButtonStyle.green if self.match_desc else nextcord.ButtonStyle.gray
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=self.selector.rawget('back', 'commons.navigation'),
                            custom_id='back',
                            emoji=self.__bot.ui_emojis.back
                        )
                    ]
                ]
                await self.menu(search=self.query, page=page)
            elif panel == 2:
                await self.display(self.filter, searched=bool(self.query))

                if self.global_filters:
                    enabled = self.__bot.db['filters'].get(self.filter.id, {}).get('enabled', False)
                else:
                    roominfo = self.__bot.bridge.get_room(self.room)
                    enabled = roominfo['meta']['filters'].get(self.filter.id, {}).get('enabled', False)

                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.red if enabled else nextcord.ButtonStyle.green,
                            label=self.selector.get('disable') if enabled else self.selector.get('enable'),
                            custom_id='toggle'
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=self.selector.rawget('back', 'commons.navigation'),
                            custom_id='back',
                            emoji=self.__bot.ui_emojis.back
                        )
                    ]
                ]
            elif panel == 3:
                await self.display_config(self.filter, self.config, searched=bool(self.query))
                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.get('change'),
                            custom_id='change'
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=self.selector.rawget('back', 'commons.navigation'),
                            custom_id='back',
                            emoji=self.__bot.ui_emojis.back
                        )
                    ]
                ]

            components = ui.MessageComponents()

            if self.selection and len(self.selection.options) > 0:
                components.add_row(ui.ActionRow(self.selection))

            components.add_rows(
                *[ui.ActionRow(*buttons[index]) for index in range(len(buttons))]
            )

            if not self.message:
                self.message = await self.ctx.send(embed=self.embed, view=components)
                if type(self.ctx) is nextcord.Interaction:
                    self.message = await self.message.fetch()
            elif not interaction.response.is_done():
                # noinspection PyUnresolvedReferences
                await interaction.response.edit_message(embed=self.embed, view=components)

            def check(interaction):
                if not interaction.message:
                    return False

                return interaction.user.id == self.author.id and interaction.message.id == self.message.id

            try:
                interaction = await self.__bot.wait_for('interaction', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await self.message.edit(view=None)

            custom_id = interaction.data['custom_id']
            if interaction.type == nextcord.InteractionType.component:
                if custom_id == 'prev':
                    page -= 1
                elif custom_id == 'next':
                    page -= 1
                elif custom_id == 'back':
                    panel -= 1
                    if panel == 1 and not self.query or panel < 0:
                        panel = 0
                elif custom_id == 'selection':
                    page = 0

                    if panel == 0 or panel == 1:
                        self.filter = self.__bot.bridge.filters[interaction.data['values'][0]]
                        panel = 1
                    elif panel == 2:
                        self.config = interaction.data['values'][0]

                    panel += 1
                elif custom_id == 'search':
                    self.modal = nextcord.ui.Modal(title=self.selector.rawget('search_title','commons.search'),auto_defer=False)
                    self.modal.add_item(
                        nextcord.ui.TextInput(
                            label=self.selector.rawget('query', 'commons.search'),
                            style=nextcord.TextInputStyle.short,
                            placeholder=self.selector.get("search_prompt")
                        )
                    )
                    await interaction.response.send_modal(self.modal)
                elif custom_id == 'toggle':
                    if self.global_filters:
                        current = self.__bot.db['filters'].get(self.filter.id, {}).get('enabled', False)

                        if not self.filter.id in self.__bot.db['filters'].keys():
                            self.__bot.db['filters'].update({self.filter.id: {}})

                        self.__bot.db['filters'][self.filter.id].update({'enabled': not current})
                        self.__bot.db.save_data()
                    else:
                        roominfo = self.__bot.bridge.get_room(self.room)

                        current = roominfo['meta']['filters'].get(self.filter.id, {}).get('enabled', False)

                        if not self.filter.id in roominfo['meta']['filters'].keys():
                            roominfo['meta']['filters'].update({self.filter.id: {}})

                        roominfo['meta']['filters'][self.filter.id].update({'enabled': not current})
                        self.__bot.bridge.update_room(self.room, roominfo)
                elif custom_id == 'change':
                    if not self.filter.configs[self.config].type == 'boolean':
                        await interaction.response.send_modal(self.modal)
                        continue

                    if self.global_filters:
                        current = self.__bot.db['filters'].get(self.filter.id, {}).get(self.config, self.filter.configs[self.config].default)

                        if not self.filter.id in self.__bot.db['filters'].keys():
                            self.__bot.db['filters'].update({self.filter.id: {}})

                        self.__bot.db['filters'][self.filter.id].update({self.config: not current})
                        self.__bot.db.save_data()
                    else:
                        roominfo = self.__bot.bridge.get_room(self.room)

                        current = roominfo['meta']['filters'].get(self.filter.id, {}).get(self.config, self.filter.configs[self.config].default)

                        if not self.filter.id in roominfo['meta']['filters'].keys():
                            roominfo['meta']['filters'].update({self.filter.id: {}})

                        roominfo['meta']['filters'][self.filter.id].update({self.config: not current})
                        self.__bot.bridge.update_room(self.room, roominfo)
                elif custom_id == 'match':
                    self.match_both = not self.match_both
                elif custom_id == 'name':
                    self.match_name = not self.match_name
                elif custom_id == 'desc':
                    self.match_desc = not self.match_desc
            elif interaction.type == nextcord.InteractionType.modal_submit:
                if panel == 0 or panel == 1:
                    if panel == 0:
                        self.match_both = False
                        self.match_name = True
                        self.match_desc = True
                    panel = 1
                    page = 0
                    self.query = interaction.data['components'][0]['components'][0]['value']
                elif panel == 3:
                    new_value = interaction.data['components'][0]['components'][0]['value']
                    if (
                            self.filter.configs[self.config].type == 'integer' or
                            self.filter.configs[self.config].type == 'number'
                    ):
                        try:
                            new_value = int(new_value)
                        except ValueError:
                            continue
                    elif self.filter.configs[self.config].type == 'float':
                        try:
                            new_value = float(new_value)
                        except ValueError:
                            continue

                    if self.filter.configs[self.config].limits:
                        if self.filter.configs[self.config].type == 'string' and not (
                                self.filter.configs[self.config].limits[0]
                                <= len(new_value) <=
                                self.filter.configs[self.config].limits[1]
                        ) or (
                                self.filter.configs[self.config].type == 'number' or
                                self.filter.configs[self.config].type == 'integer' or
                                self.filter.configs[self.config].type == 'float'
                        ) and not (
                                self.filter.configs[self.config].limits[0]
                                <= new_value <=
                                self.filter.configs[self.config].limits[1]
                        ):
                            continue

                    if self.global_filters:
                        if not self.filter.id in self.__bot.db['filters'].keys():
                            self.__bot.db['filters'].update({self.filter.id: {}})

                        self.__bot.db['filters'][self.filter.id].update({self.config: new_value})
                        self.__bot.db.save_data()
                    else:
                        roominfo = self.__bot.bridge.get_room(self.room)

                        if not self.filter.id in roominfo['meta']['filters'].keys():
                            roominfo['meta']['filters'].update({self.filter.id: {}})

                        roominfo['meta']['filters'][self.filter.id].update({self.config: new_value})
                        self.__bot.bridge.update_room(self.room, roominfo)

# Could've used inheritance here, but I'd need to override every method anyway, so better off not
class SettingsDialog:
    def __init__(self, bot, ctx: Union[nextcord.Interaction, commands.Context], room=None, query=None):
        self.ctx = ctx
        self.__bot = bot
        self.room = room
        self.message = None
        self.embed = nextcord.Embed(color=self.__bot.colors.unifier)
        self.selector = language.get_selector(ctx)
        self.selection = None
        self.query = query
        self.modal = None
        self.setting = None
        self.maxpage = 0
        self.match_both = False
        self.match_name = True
        self.match_desc = True
        self.title = self.__bot.ui_emojis.rooms + ' ' + self.selector.fget('title',values={'room':self.room})

    @property
    def author(self):
        if type(self.ctx) is nextcord.Interaction:
            return self.ctx.user
        else:
            return self.ctx.author

    async def sanitize(self):
        self.embed.clear_fields()
        self.embed.remove_author()
        self.embed.remove_footer()
        self.selection = None

    async def menu(self, search: Optional[str] = None, page: int = 0):
        await self.sanitize()

        if search:
            keys = list(settings_keys)
            for bridge_setting in settings_keys:
                # noinspection PyTypeChecker
                if self.match_both:
                    if not (
                            (
                                    (search.lower() in bridge_setting.lower() if self.match_name else True) or
                                    (search.lower() in self.selector.get(f"{bridge_setting}_name").lower() if self.match_name else True)
                            ) and (
                                    search.lower() in self.selector.get(f"{bridge_setting}_desc").lower() if self.match_desc else True
                            )
                    ):
                        keys.remove(bridge_setting)
                else:
                    if not (
                            (
                                    (search.lower() in bridge_setting.lower() if self.match_name else True) or
                                    (search.lower() in self.selector.get(f"{bridge_setting}_name").lower() if self.match_name else True)
                            ) or (
                                    search.lower() in self.selector.get(f"{bridge_setting}_desc").lower() if self.match_desc else True
                            )
                    ):
                        keys.remove(bridge_setting)
            self.embed.description = self.selector.rawfget(
                "search_results", "commons.search", values={"query": search, "results": len(keys)}
            )
        else:
            keys = list(settings_keys)
            self.embed.description = self.selector.get('choose_filter')

        roomdata = self.__bot.bridge.get_room(self.room)
        limit = 20
        maxpage = math.ceil(len(keys)/limit)-1
        self.maxpage = maxpage

        if page > maxpage:
            page = maxpage
        elif page < 0:
            page = 0

        offset = page * limit

        self.embed.title = self.title

        self.selection = nextcord.ui.StringSelect(
            max_values=1, min_values=1, custom_id='selection', placeholder=self.selector.get("selection")
        )

        for index in range(limit):
            if index + offset >= len(keys) or len(keys) == 0:
                break

            # noinspection PyTypeChecker
            setting_key = keys[index + offset]
            setting_name = self.selector.get(f"{keys[index + offset]}_name")
            setting_desc = self.selector.get(f"{keys[index + offset]}_desc")
            setting_default = settings_defaults[setting_key]

            if roomdata['meta']['settings'].get(setting_key, setting_default):
                self.embed.add_field(
                    name=f'{self.__bot.ui_emojis.success} **{setting_name} (`{setting_key}`)**',
                    value=setting_desc or self.selector.get("no_desc"),
                    inline=False
                )
            else:
                self.embed.add_field(
                    name=f'{setting_name} (`{setting_key}`)',
                    value=setting_desc or self.selector.get("no_desc"),
                    inline=False
                )

            trimmed = setting_desc or self.selector.get("no_desc")
            if len(trimmed) > 100:
                trimmed = trimmed[:97] + '...'

            self.selection.add_option(
                label=setting_name,
                description=trimmed,
                value=setting_key
            )

        if len(self.embed.fields) == 0:
            self.selection.disabled = True
            self.selection.add_option(
                label='placeholder',
                value='placeholder'
            )
            self.embed.add_field(
                name=self.selector.get('noresults_title'),
                value=(
                    self.selector.get("noresults_body_search") if search else
                    self.selector.get("noresults_body_filters")
                ),
                inline=False
            )

        self.embed.set_footer(text=self.selector.rawfget("page", "commons.search", values={
            "page": page + 1, "maxpage": maxpage + 1
        }))

    async def display(self, bridge_setting: str, searched: bool = False):
        await self.sanitize()

        setting_desc = self.selector.get(f"{bridge_setting}_desc")
        setting_default = settings_defaults[bridge_setting]

        self.embed.title = self.title + f' / {bridge_setting}'
        if searched:
            self.embed.title = self.title + f' / {self.selector.get("search")} / {bridge_setting}'

        roomdata = self.__bot.bridge.get_room(self.room)

        self.embed.description = (
            f'{setting_desc or self.selector.get("no_desc")}\n\n' +
            (
                self.selector.fget("enabled", values={"emoji": self.__bot.ui_emojis.success})
                if roomdata['meta']['settings'].get(bridge_setting, setting_default)
                else self.selector.fget("disabled", values={"emoji": self.__bot.ui_emojis.error})
            )
        )

    async def display_config(self, bridge_filter: base_filter.BaseFilter, option: str, searched: bool = False):
        await self.sanitize()
        roomdata = self.__bot.bridge.get_room(self.room)

        config = bridge_filter.configs[option]
        value = roomdata['meta']['filters'].get(bridge_filter.id, {}).get(option, config.default)

        self.embed.title = self.title + f' / {bridge_filter.id} / {option}'
        if searched:
            self.embed.title = self.title + f' / {self.selector.get("search")} / {bridge_filter.id} / {option}'

        textinput = nextcord.ui.TextInput(
            label=self.selector.get('value'),
            style=nextcord.TextInputStyle.short,
            placeholder=self.selector.get("value_prompt"),
            default_value=str(value)
        )

        limittext = None
        if config.limits:
            if config.type == 'string':
                limittext = f'{self.selector.fget("limit_str",values={"lower":config.limits[0],"upper":config.limits[1]})}'
                textinput.min_length = config.limits[0]
                textinput.max_length = config.limits[1]
            elif config.type == 'number' or config.type == 'integer' or config.type == 'float':
                limittext = f'{self.selector.fget("limit_num",values={"lower":config.limits[0],"upper":config.limits[1]})}'

        valuetext = '`'+str(value)+'`'
        if len(valuetext) > 1024:
            valuetext = valuetext[:1020] + '...`'

        if config.type == 'boolean':
            valuetext = (
                f'{self.__bot.ui_emojis.success} {self.selector.get("enabled_config")}' if value else
                f'{self.__bot.ui_emojis.error} {self.selector.get("disabled_config")}'
            )

        self.embed.description = f'# {config.name} (`{option}`)\n{config.description}'
        self.embed.add_field(name=self.selector.get('current'), value=valuetext, inline=False)

        if limittext:
            self.embed.add_field(name=self.selector.get('limits'), value=limittext, inline=False)

        self.modal = nextcord.ui.Modal(
            title=self.selector.get('form_title'),
            auto_defer=False
        )

        self.modal.add_item(
            textinput
        )

    async def run(self):
        page = 0
        panel = 0
        if self.query:
            panel = 1

        interaction = None
        while True:
            buttons = []
            if panel == 0:
                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('prev', 'commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.__bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('next', 'commons.navigation'),
                            custom_id='next',
                            disabled=page >= self.maxpage,
                            emoji=self.__bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=self.selector.rawget('search', 'commons.search'),
                            custom_id='search',
                            emoji=self.__bot.ui_emojis.search
                        )
                    ]
                ]
                await self.menu(page=page)
            elif panel == 1:
                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('prev', 'commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.__bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=self.selector.rawget('next', 'commons.navigation'),
                            custom_id='next',
                            disabled=page >= self.maxpage,
                            emoji=self.__bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=self.selector.rawget('search', 'commons.search'),
                            custom_id='search',
                            emoji=self.__bot.ui_emojis.search
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            custom_id='match',
                            label=(
                                self.selector.rawget('match_any', 'commons.search') if not self.match_both else
                                self.selector.rawget('match_both', 'commons.search')
                            ),
                            style=(
                                nextcord.ButtonStyle.green if not self.match_both else
                                nextcord.ButtonStyle.blurple
                            ),
                            emoji=(
                                '\U00002194' if not self.match_both else
                                '\U000023FA'
                            )
                        ),
                        nextcord.ui.Button(
                            custom_id='name',
                            label=self.selector.get("filter_name"),
                            style=nextcord.ButtonStyle.green if self.match_name else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label=self.selector.get("filter_desc"),
                            style=nextcord.ButtonStyle.green if self.match_desc else nextcord.ButtonStyle.gray
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=self.selector.rawget('back', 'commons.navigation'),
                            custom_id='back',
                            emoji=self.__bot.ui_emojis.back
                        )
                    ]
                ]
                await self.menu(search=self.query, page=page)
            elif panel == 2:
                await self.display(self.setting, searched=bool(self.query))
                roominfo = self.__bot.bridge.get_room(self.room)
                setting_default = settings_defaults[self.setting]
                enabled = roominfo['meta']['settings'].get(self.setting, setting_default)

                buttons = [
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.red if enabled else nextcord.ButtonStyle.green,
                            label=self.selector.get('disable') if enabled else self.selector.get('enable'),
                            custom_id='toggle'
                        )
                    ],
                    [
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=self.selector.rawget('back', 'commons.navigation'),
                            custom_id='back',
                            emoji=self.__bot.ui_emojis.back
                        )
                    ]
                ]

            components = ui.MessageComponents()

            if self.selection and len(self.selection.options) > 0:
                components.add_row(ui.ActionRow(self.selection))

            components.add_rows(
                *[ui.ActionRow(*buttons[index]) for index in range(len(buttons))]
            )

            if not self.message:
                self.message = await self.ctx.send(embed=self.embed, view=components)
                if type(self.ctx) is nextcord.Interaction:
                    self.message = await self.message.fetch()
            elif not interaction.response.is_done():
                # noinspection PyUnresolvedReferences
                await interaction.response.edit_message(embed=self.embed, view=components)

            def check(interaction):
                if not interaction.message:
                    return False

                return interaction.user.id == self.author.id and interaction.message.id == self.message.id

            try:
                interaction = await self.__bot.wait_for('interaction', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await self.message.edit(view=None)

            custom_id = interaction.data['custom_id']
            if interaction.type == nextcord.InteractionType.component:
                if custom_id == 'prev':
                    page -= 1
                elif custom_id == 'next':
                    page -= 1
                elif custom_id == 'back':
                    panel -= 1
                    if panel == 1 and not self.query or panel < 0:
                        panel = 0
                elif custom_id == 'selection':
                    self.setting = interaction.data['values'][0]
                    page = 0
                    panel = 2
                elif custom_id == 'search':
                    self.modal = nextcord.ui.Modal(title=self.selector.rawget('search_title','commons.search'),auto_defer=False)
                    self.modal.add_item(
                        nextcord.ui.TextInput(
                            label=self.selector.rawget('query', 'commons.search'),
                            style=nextcord.TextInputStyle.short,
                            placeholder=self.selector.get("search_prompt")
                        )
                    )
                    await interaction.response.send_modal(self.modal)
                elif custom_id == 'toggle':
                    roominfo = self.__bot.bridge.get_room(self.room)
                    setting_default = settings_defaults[self.setting]

                    current = roominfo['meta']['settings'].get(self.setting, setting_default)

                    roominfo['meta']['settings'].update({self.setting: not current})
                    self.__bot.bridge.update_room(self.room, roominfo)
                elif custom_id == 'match':
                    self.match_both = not self.match_both
                elif custom_id == 'name':
                    self.match_name = not self.match_name
                elif custom_id == 'desc':
                    self.match_desc = not self.match_desc
            elif interaction.type == nextcord.InteractionType.modal_submit:
                if panel == 0:
                    self.match_both = False
                    self.match_name = True
                    self.match_desc = True
                panel = 1
                page = 0
                self.query = interaction.data['components'][0]['components'][0]['value']

class Config(commands.Cog, name=':construction_worker: Config'):
    """Config is an extension that lets Unifier admins configure the bot and server moderators set up Unified Chat in their server."""

    def __init__(self,bot):
        global language
        self.bot = bot
        if not hasattr(self.bot, 'bridged_emojis'):
            if not 'emojis' in list(self.bot.db.keys()):
                self.bot.db.update({'emojis':[]})
                self.bot.db.save_data()
            self.bot.bridged_emojis = self.bot.db['emojis']
        if not hasattr(self.bot, 'trusted_group'):
            self.bot.trusted_group = self.bot.db['trusted']
        try:
            restrictions.attach_bot(self.bot)
        except ValueError:
            # assume already attached
            pass
        try:
            restrictions_legacy.attach_bot(self.bot)
        except ValueError:
            # assume already attached
            pass
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)
        language = self.bot.langmgr

    def can_manage(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                room = self.bot.bridge.get_invite(room)['room']
            except:
                return False

        __roominfo = self.bot.bridge.get_room(room)
        if not __roominfo:
            return False

        is_server = str(user.guild.id) == __roominfo['meta']['private_meta']['server']
        is_moderator = user.id in self.bot.moderators
        is_admin = user.id in self.bot.admins
        is_owner = user.id == self.bot.owner or user.id in self.bot.other_owners

        if __roominfo['meta']['private']:
            return (
                    user.guild_permissions.manage_channels and is_server
            ) or ((is_moderator and self.bot.config['private_rooms_mod_access']) or is_admin or is_owner)
        else:
            return is_admin or is_owner

    def can_join(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                self.bot.bridge.get_invite(room)
                return True
            except:
                return False

        __roominfo = self.bot.bridge.get_room(room)
        if not __roominfo:
            return False

        is_server = str(user.guild.id) == __roominfo['meta']['private_meta']['server']
        is_allowed = user.guild.id in __roominfo['meta']['private_meta']['allowed']

        if __roominfo['meta']['private']:
            return is_server or is_allowed
        else:
            return True

    def is_user_admin(self,user_id):
        try:
            if user_id in self.bot.config['admin_ids']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def is_room_restricted(self, room, db):
        try:
            if db['rooms'][room]['meta']['restricted']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def is_room_locked(self, room, db):
        try:
            if db['rooms'][room]['meta']['locked']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    async def cog_before_invoke(self, ctx):
        ctx.user = ctx.author

    async def room_manage_private_autocomplete(self, room, user):
        # Usually I'd add this to a util or something to share it with other cogs,
        # but I'm not feeling like that right now...maybe next patch?
        possible = []
        for roomname in self.bot.bridge.rooms:
            roominfo = self.bot.bridge.get_room(roomname)
            if not roominfo['meta']['private']:
                continue
            if self.bot.bridge.can_manage_room(roomname, user) and roomname.startswith(room):
                possible.append(roomname)

        return possible

    @nextcord.slash_command(
        contexts=[nextcord.InteractionContextType.guild],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def config(self, ctx):
        pass

    @commands.group(name='config')
    async def config_legacy(self,ctx):
        pass

    @config_legacy.command(
        description=language.desc('config.addmod'),
        description_localizations=language.slash_desc('config.addmod')
    )
    @restrictions_legacy.admin()
    async def addmod(self,ctx,*,userid):
        selector = language.get_selector(ctx)
        discord_hint = True
        userid = userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)
        try:
            userid = int(userid)
        except:
            discord_hint = False

        username = None
        discriminator = None
        is_bot = False
        if discord_hint:
            user = self.bot.get_user(userid)
            username = user.name
            discriminator = user.discriminator if not user.discriminator == '0' else None
            is_bot = user.bot
        else:
            for platform in self.bot.platforms.keys():
                support = self.bot.platforms[platform]
                try:
                    user = support.get_user(userid)
                except:
                    continue
                username = support.user_name(user)
                is_bot = support.is_bot(user)
                break

        if not username:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        if userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_mod")}')
        if self.is_user_admin(userid) or is_bot:
            return await ctx.send(selector.get("self_target"))
        self.bot.db['moderators'].append(userid)
        self.bot.moderators.append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{username}#{discriminator}'
        if not discriminator:
            mod = f'@{username}'
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"mod":mod})}')

    @config_legacy.command(
        aliases=['remmod','delmod'],
        description=language.desc('config.removemod'),
        description_localizations=language.slash_desc('config.removemod')
    )
    @restrictions_legacy.admin()
    async def removemod(self,ctx,*,userid):
        selector = language.get_selector(ctx)
        discord_hint = True
        userid = userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)
        try:
            userid = int(userid)
        except:
            discord_hint = False

        username = None
        discriminator = None
        if discord_hint:
            user = self.bot.get_user(userid)
            username = user.name
            discriminator = user.discriminator if not user.discriminator == '0' else None
        else:
            for platform in self.bot.platforms.keys():
                support = self.bot.platforms[platform]
                try:
                    user = support.get_user(userid)
                    username = support.user_name(user)
                except:
                    continue
                break

        if not username:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid","config.addmod")}')
        if not userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_mod")}')
        if self.is_user_admin(userid):
            return await ctx.send(selector.rawget("self_target","config.addmod"))
        self.bot.db['moderators'].remove(userid)
        self.bot.moderators.remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{username}#{discriminator}'
        if not discriminator:
            mod = f'@{username}'
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"mod":mod})}')

    # Create invite command
    async def create_invite(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: str, expiry: Optional[str] = None,
            max_usage: Optional[int] = None
    ):
        if not expiry:
            expiry = '1d'
        if not max_usage:
            max_usage = 2
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if len(self.bot.db['rooms'][room]['meta']['private_meta']['invites']) >= 20:
            if type(ctx) is nextcord.Interaction:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("invites_limit")}', ephemeral=True
                )
            else:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invites_limit")}')

        infinite_enabled = ''
        if self.bot.config['permanent_invites']:
            infinite_enabled = ' ' + selector.get("permanent")

        if expiry == 'inf':
            if not self.bot.config['permanent_invites']:
                if type(ctx) is nextcord.Interaction:
                    return await ctx.send(
                        f'{self.bot.ui_emojis.error} {selector.get("permanent_disabled")}', ephemeral=True
                    )
                else:
                    return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("permanent_disabled")}')
            expiry = 0
        else:
            try:
                expiry = timetoint(expiry)
            except:
                if type(ctx) is nextcord.Interaction:
                    return await ctx.send(
                        f'{self.bot.ui_emojis.error} {selector.rawget("invalid_duration","commons.moderation")}',
                        ephemeral=True
                    )
                else:
                    return await ctx.send(
                        f'{self.bot.ui_emojis.error} {selector.rawget("invalid_duration","commons.moderation")}'
                    )
            if expiry > 604800:
                if type(ctx) is nextcord.Interaction:
                    return await ctx.send(
                        f'{self.bot.ui_emojis.error} {selector.get("duration_toolong")}{infinite_enabled}',
                        ephemeral=True
                    )
                else:
                    return await ctx.send(
                        f'{self.bot.ui_emojis.error} {selector.get("duration_toolong")}{infinite_enabled}'
                    )
            expiry += time.time()
        invite = self.bot.bridge.create_invite(room, max_usage, expiry)
        try:
            await ctx.user.send(
                f'{selector.get("code")} `{invite}`\n{selector.fget("join",values={"prefix":self.bot.command_prefix,"invite":invite})}'
            )
        except:
            if type(ctx) is nextcord.Interaction:
                return await ctx.send(
                    f'{self.bot.ui_emojis.warning} {selector.fget("dm_fail",values={"prefix":self.bot.command_prefix})}',
                    ephemeral=True
                )
            else:
                return await ctx.send(
                    f'{self.bot.ui_emojis.warning} {selector.fget("dm_fail",values={"prefix":self.bot.command_prefix})}'
                )

        steps = '\n'.join([f'- {step}' for step in [
            selector.fget(
                'step_1',
                values={'command': self.bot.get_application_command_from_signature('bridge bind').get_mention()}
            ),
            selector.get('step_2')
        ]])

        embed = nextcord.Embed(
            title=selector.rawget('nextsteps','commons.navigation'),
            description=steps,
            color=self.bot.colors.unifier
        )

        if type(ctx) is nextcord.Interaction:
            await ctx.send(
                f'{self.bot.ui_emojis.success} {selector.get("success")}\n{selector.get("disclaimer")}', embed=embed,
                ephemeral=True
            )
        else:
            await ctx.send(
                f'{self.bot.ui_emojis.success} {selector.get("success")}\n{selector.get("disclaimer")}', embed=embed
            )

    # Delete invite command
    async def delete_invite(self, ctx: Union[nextcord.Interaction, commands.Context], invite: str):
        invite = invite.lower()
        if not self.bot.bridge.can_manage_room(invite, ctx.user):
            raise restrictions.NoRoomManagement()
        selector = language.get_selector(ctx)
        try:
            self.bot.bridge.delete_invite(invite)
        except self.bot.bridge.InviteNotFoundError:
            if type(ctx) is nextcord.Interaction:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("invalid")}', ephemeral=True
                )
            else:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')

        if type(ctx) is nextcord.Interaction:
            await ctx.send(
                f'{self.bot.ui_emojis.success} {selector.get("success")}', ephemeral=True
            )
        else:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    # Invites command
    async def invites(self, ctx: Union[nextcord.Interaction, commands.Context], room: str):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            if type(ctx) is nextcord.Interaction:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.rawget("is_public","config.create-invite")}', ephemeral=True
                )
            else:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.rawget("is_public","config.create-invite")}'
                )

        invites = self.bot.db['rooms'][room]['meta']['private_meta']['invites']

        embed = nextcord.Embed(
            title=f'Invites for `{room}`',
        )

        success = 0
        for invite in invites:
            invite_data = self.bot.bridge.get_invite(invite)
            if not invite_data:
                continue
            embed.add_field(
                name=f'`{invite}`',
                value=(
                    selector.get("unlimited") if invite_data['remaining'] == 0 else
                    f'{selector.get("remaining")} {invite_data["remaining"]}'
                )+f'\n{selector.get("expiry")} '+(
                    selector.get("never") if invite_data["expire"] == 0 else f'<t:{round(invite_data["expire"])}:R>'
                )
            )
            success += 1

        embed.description = selector.fget("created",values={"created":success,"limit":20})
        try:
            await ctx.user.send(embed=embed)
        except:
            if type(ctx) is nextcord.Interaction:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("dm_fail")}', ephemeral=True)
            else:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("dm_fail")}')

        if type(ctx) is nextcord.Interaction:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}', ephemeral=True)
        else:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @config_legacy.command(
        description=language.desc('config.rename'),
        description_localizations=language.slash_desc('config.rename')
    )
    @restrictions_legacy.admin()
    @restrictions_legacy.not_banned()
    async def rename(self, ctx, room: str, newroom: str):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.author):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        newroom = newroom.lower()
        if not bool(re.match("^[A-Za-z0-9_-]*$", newroom)):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("alphanumeric","config.make")}')
        if newroom in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exists")}')
        if self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_private")}')
        self.bot.db['rooms'].update({newroom: self.bot.db['rooms'][room]})
        self.bot.db['rooms'].pop(room)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}\n`{room}` => `{newroom}`')

    # Display name command
    async def display_name(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: str, name: Optional[str] = None
    ):
        if not name:
            name = ''
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        current_name = str(self.bot.db['rooms'][room]['meta']['display_name'])

        if len(name) == 0:
            if not self.bot.db['rooms'][room]['meta']['display_name']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_name")}')
            self.bot.db['rooms'][room]['meta']['display_name'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        elif len(name) > 32:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("toolong")}')
        self.bot.db['rooms'][room]['meta']['display_name'] = name
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}\n`{current_name}` => `{name}`')

    # Room description command
    async def roomdesc(self, ctx: Union[nextcord.Interaction, commands.Context], room: str, desc: Optional[str] = None):
        if not desc:
            desc = ''
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(desc)==0:
            if not self.bot.db['rooms'][room]['meta']['description']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_desc")}')
            self.bot.db['rooms'][room]['meta']['description'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        self.bot.db['rooms'][room]['meta']['description'] = desc
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    # Room emoji command
    async def roomemoji(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: str, emoji: Optional[str] = None
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(emoji) == 0:
            if not self.bot.db['rooms'][room]['meta']['emoji']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_emoji")}')
            self.bot.db['rooms'][room]['meta']['emoji'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        if not pymoji.is_emoji(emoji):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_emoji")}')
        self.bot.db['rooms'][room]['meta']['emoji'] = emoji
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(selector.get("success"))

    @config_legacy.command(
        description=language.desc('config.restrict'),
        description_localizations=language.slash_desc('config.restrict')
    )
    @restrictions_legacy.admin()
    async def restrict(self,ctx,room=None):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_private")}')
        if self.bot.db['rooms'][room]['meta']['restricted']:
            self.bot.db['rooms'][room]['meta']['restricted'] = False
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['restricted'] = True
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')

    # Lock command
    async def lock(self, ctx: Union[nextcord.Interaction, commands.Context], room: Optional[str] = None):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private'] and not ctx.user.id in self.bot.admins:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if self.bot.db['rooms'][room]['meta']['locked']:
            self.bot.db['rooms'][room]['meta']['locked'] = False
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['locked'] = True
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @config_legacy.command(description='Maps channels to rooms in bulk.', aliases=['autobind'])
    @restrictions_legacy.admin()
    @restrictions_legacy.no_admin_perms()
    async def map(self, ctx):
        channels = []
        channels_enabled = []
        namelist = []

        selector = language.get_selector(ctx)

        # get using async because this property may take a while to get if there's lots of rooms
        public_rooms = await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.public_rooms)

        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.loading} {selector.get("map_title")}',
                               description=selector.get("check_body"),
                               color=self.bot.colors.warning)
        msg = await ctx.send(embed=embed)
        hooks = await ctx.guild.webhooks()
        for channel in ctx.guild.text_channels:
            duplicate = False
            for roomname in list(public_rooms):
                # Prevent duplicate binding
                try:
                    hook_id = self.bot.bridge.get_room(roomname)['discord'][f'{ctx.guild.id}'][0]
                except:
                    continue
                for hook in hooks:
                    if hook.id == hook_id and hook.channel_id==channel.id:
                        duplicate = True
                        break
            if duplicate:
                continue
            roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
            if len(roomname) < 3:
                roomname = str(channel.id)
            if roomname in namelist:
                continue
            namelist.append(roomname)
            try:
                if len(self.bot.db['rooms'][roomname]['discord'][f'{ctx.guild.id}']) >= 1:
                    continue
            except:
                pass
            perms = channel.permissions_for(ctx.guild.me)
            if perms.manage_webhooks and perms.send_messages and perms.read_messages and perms.read_message_history:
                channels.append(channel)
                if len(channels_enabled) < 10:
                    channels_enabled.append(channel)
            if len(channels) >= 25:
                break

        interaction = None
        restricted = False
        locked = False
        while True:
            text = ''
            for channel in channels_enabled:
                roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
                if len(roomname) < 3:
                    roomname = str(channel.id)
                if text=='':
                    text = f'#{channel.name} ==> **{roomname}**' + (
                        ' (__New__)' if not roomname in self.bot.db['rooms'].keys() else '')
                else:
                    text = f'{text}\n#{channel.name} ==> **{roomname}**' + (
                        ' (__New__)' if not roomname in self.bot.db['rooms'].keys() else '')
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.rooms} {selector.get("map_title")}',
                description=f'{selector.get("map_body")}\n\n{text}',
                color=self.bot.colors.unifier
            )

            view = ui.MessageComponents()
            selection = nextcord.ui.StringSelect(
                max_values=10 if len(channels) > 10 else len(channels),
                placeholder=selector.get("selection_ch"),
                custom_id='selection'
            )

            for channel in channels:
                selection.add_option(
                    label=f'#{channel.name}',
                    value=str(channel.id),
                    default=channel in channels_enabled
                )

            view.add_rows(
                ui.ActionRow(
                    selection
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.get("selectall_over10") if len(channels) > 10 else selector.get("selectall"),
                        custom_id='selectall'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.get("deselect"),
                        custom_id='deselect'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label=selector.get("bind"),
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=selector.get("bind_restricted"),
                        custom_id='bind_restricted'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=selector.get("bind_locked"),
                        custom_id='bind_locked'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.rawget("cancel","commons.navigation"),
                        custom_id='cancel'
                    )
                ) if ctx.author.id in self.bot.admins else ui.ActionRow(
                    # we don't support non-admins mapping yet, but in case we do
                    # then making rooms should not be allowed
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label=selector.get("bind"),
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.rawget("cancel","commons.navigation"),
                        custom_id='cancel'
                    )
                )
            )

            if interaction:
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await msg.edit(embed=embed, view=view)

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
                if interaction.data['custom_id']=='cancel':
                    raise RuntimeError()
            except:
                return await msg.edit(view=ui.MessageComponents())

            if interaction.data['custom_id'].startswith('bind'):
                embed.title = embed.title.replace(self.bot.ui_emojis.rooms, self.bot.ui_emojis.loading, 1)
                await msg.edit(embed=embed, view=ui.MessageComponents())
                await interaction.response.defer(with_message=True)
                if 'restricted' in interaction.data['custom_id']:
                    restricted = True
                elif 'locked' in interaction.data['custom_id']:
                    locked = True
                break
            elif interaction.data['custom_id']=='selection':
                channels_enabled = []
                for value in interaction.data['values']:
                    channel = self.bot.get_channel(int(value))
                    channels_enabled.append(channel)
            elif interaction.data['custom_id']=='selectall':
                channels_enabled = []
                for channel in channels:
                    channels_enabled.append(channel)
                    if len(channels_enabled) >= 10:
                        break
            elif interaction.data['custom_id'] == 'deselect':
                channels_enabled = []

        for channel in channels_enabled:
            roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
            if len(roomname) < 3:
                roomname = str(channel.id)
            if not roomname in self.bot.db['rooms'].keys():
                self.bot.bridge.create_room(roomname, private=False)
                if restricted:
                    self.bot.db['rooms'][roomname]['meta']['restricted'] = True
                elif locked:
                    self.bot.db['rooms'][roomname]['meta']['locked'] = True
            webhook = await channel.create_webhook(name='Unifier Bridge')
            await self.bot.bridge.join_room(ctx.author,roomname,ctx.channel,webhook_id=webhook.id)

        embed.title = f'{self.bot.ui_emojis.success} {selector.get("success")}'
        embed.colour = self.bot.colors.success
        await msg.edit(embed=embed)

        await interaction.edit_original_message(
            content=f'{self.bot.ui_emojis.success} {selector.get("say_hi")}')

    # Add rule command
    async def addrule(self, ctx: Union[nextcord.Interaction, commands.Context], room: str, rule: str):
        __room = room.lower()
        if not __room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(__room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(self.bot.db['rooms'][__room]['meta']['rules']) >= 25:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exceed")}')
        self.bot.db['rooms'][__room]['meta']['rules'].append(rule)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    # Delete rule command
    async def delrule(self, ctx: Union[nextcord.Interaction, commands.Context], room: str, rule: int):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        try:
            rule = int(rule)
            if rule <= 0:
                raise ValueError()
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        self.bot.db['rooms'][room]['meta']['rules'].pop(rule-1)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    # Toggle emoji command
    async def toggle_emoji(self, ctx: Union[nextcord.Interaction, commands.Context]):
        selector = language.get_selector(ctx)
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')
        self.bot.db['emojis'] = self.bot.bridged_emojis
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

    # Filters command
    async def filters(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: Optional[str] = None,
            query: Optional[str] = None
    ):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        roomdata = self.bot.bridge.get_room(room)
        if not roomdata:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        dialog = FilterDialog(self.bot, ctx, room=room, query=query)
        await dialog.run()

    # Settings command
    async def settings(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: Optional[str] = None,
            query: Optional[str] = None
    ):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        roomdata = self.bot.bridge.get_room(room)
        if not roomdata:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        dialog = SettingsDialog(self.bot, ctx, room=room, query=query)
        await dialog.run()

    # Permissions override command
    # TODO: work on this
    async def permissions_override(
            self, ctx: Union[nextcord.Interaction, commands.Context], room: Optional[str] = None,
            query: Optional[str] = None
    ):
        selector = language.get_selector(ctx)
        status = self.bot.db['permission_overrides'].get(f'{ctx.guild.id}')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.get("title")}',
            description=f'{selector.get("body")}\n{selector.get("body_2")}',
            color=self.bot.colors.warning
        )

        selection = nextcord.ui.StringSelect(
            max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("time")
        )
        selection.add_option(
            label=selector.get("hour"),
            value='1h'
        )
        selection.add_option(
            label=selector.get("day"),
            value='1d'
        )
        selection.add_option(
            label=selector.get("week"),
            value='1w'
        )

        components = ui.MessageComponents()

        if status:
            embed.title = f'{self.bot.ui_emojis.warning} {selector.get("disable_title")}'
            embed.description = selector.get("disable_body")

            button = nextcord.ui.Button()

    # Universal commands handlers and autocompletes

    # config create-invite
    @config.subcommand(
        name='create-invite',
        description=language.desc('config.create-invite'),
        description_localizations=language.slash_desc('config.create-invite')
    )
    @restrictions.not_banned()
    async def create_invite_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.create-invite.room'),
            expiry: Optional[str] = slash.option('config.create-invite.expiry', required=False),
            max_usage: Optional[int] = slash.option('config.create-invite.max-usage', required=False)
    ):
        await self.create_invite(ctx, room, expiry, max_usage)

    @config_legacy.command(name='create-invite')
    @restrictions_legacy.not_banned()
    async def create_invite_legacy(
            self, ctx: commands.Context, room: str, expiry: Optional[str] = None, max_usage: Optional[int] = None
    ):
        await self.create_invite(ctx, room, expiry=expiry, max_usage=max_usage)

    # config delete-invite
    @config.subcommand(
        name='delete-invite',
        description=language.desc('config.delete-invite'),
        description_localizations=language.slash_desc('config.delete-invite')
    )
    @restrictions.not_banned()
    async def delete_invite_slash(
            self, ctx: nextcord.Interaction,
            invite: str = slash.option('config.delete-invite.invite')
    ):
        await self.delete_invite(ctx, invite)

    @config_legacy.command(name='delete-invite')
    @restrictions_legacy.not_banned()
    async def delete_invite_legacy(self, ctx: commands.Context, invite: str):
        await self.delete_invite(ctx, invite)

    # config invites
    @config.subcommand(
        name='invites',
        description=language.desc('config.invites'),
        description_localizations=language.slash_desc('config.invites')
    )
    @restrictions.not_banned()
    async def invites_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.invites.room')
    ):
        await self.invites(ctx, room)

    @config_legacy.command(name='invites')
    async def invites_legacy(self, ctx: commands.Context, room: str):
        await self.invites(ctx, room)

    @invites_slash.on_autocomplete("room")
    async def invites_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_manage_private_autocomplete(room, ctx.user))

    # config display-name
    @config.subcommand(
        name='display-name',
        description=language.desc('config.display-name'),
        description_localizations=language.slash_desc('config.display-name')
    )
    @restrictions.not_banned()
    async def display_name_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.display-name.room'),
            name: Optional[str] = slash.option('config.display-name.display-name', required=False)
    ):
        await self.display_name(ctx, room, name=name)

    @config_legacy.command(name='display-name')
    async def display_name_legacy(self, ctx: commands.Context, room: str, name: Optional[str] = None):
        await self.display_name(ctx, room, name=name)

    # config roomdesc
    @config.subcommand(
        name='roomdesc',
        description=language.desc('config.roomdesc'),
        description_localizations=language.slash_desc('config.roomdesc')
    )
    @restrictions.not_banned()
    async def roomdesc_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.roomdesc.room'),
            desc: Optional[str] = slash.option('config.roomdesc.description', required=False)
    ):
        await self.roomdesc(ctx, room, desc=desc)

    @config_legacy.command(name='roomdesc')
    @restrictions_legacy.not_banned()
    async def roomdesc_legacy(self, ctx: commands.Context, room: str, desc: Optional[str] = None):
        await self.roomdesc(ctx, room, desc=desc)

    # config roomemoji
    @config.subcommand(
        name='roomemoji',
        description=language.desc('config.roomemoji'),
        description_localizations=language.slash_desc('config.roomemoji')
    )
    @restrictions.not_banned()
    async def roomemoji_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.roomemoji.room'),
            emoji: Optional[str] = slash.option('config.roomemoji.emoji', required=False)
    ):
        await self.roomemoji(ctx, room, emoji=emoji)

    @config_legacy.command(name='roomemoji')
    @restrictions_legacy.not_banned()
    async def roomemoji_legacy(self, ctx: commands.Context, room: str, emoji: Optional[str] = None):
        await self.roomemoji(ctx, room, emoji=emoji)

    # config lock
    @config.subcommand(
        name='lock',
        description=language.desc('config.lock'),
        description_localizations=language.slash_desc('config.lock')
    )
    @restrictions.moderator()
    async def lock_slash(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('config.lock.room', required=False)
    ):
        await self.lock(ctx, room=room)

    @config_legacy.command(name='lock')
    @restrictions_legacy.moderator()
    async def lock_legacy(self, ctx: commands.Context, room: Optional[str] = None):
        await self.lock(ctx, room=room)

    # config add-rule
    @config.subcommand(
        name='add-rule',
        description=language.desc('config.add-rule'),
        description_localizations=language.slash_desc('config.add-rule')
    )
    @restrictions.not_banned()
    async def addrule_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.add-rule.room'),
            rule: str = slash.option('config.add-rule.rule')
    ):
        await self.addrule(ctx, room, rule)

    @config_legacy.command(name='add-rule')
    @restrictions_legacy.not_banned()
    async def addrule_legacy(self, ctx: commands.Context, room: str, rule: str):
        await self.addrule(ctx, room, rule)

    # config delete-rule
    @config.subcommand(
        name='delete-rule',
        description=language.desc('config.delete-rule'),
        description_localizations=language.slash_desc('config.delete-rule')
    )
    @restrictions.not_banned()
    async def delrule_slash(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.delete-rule.room'),
            rule: int = slash.option('config.delete-rule.rule')
    ):
        await self.delrule(ctx, room, rule)

    @config_legacy.command(name='delete-rule')
    @restrictions_legacy.not_banned()
    async def delrule_legacy(self, ctx: commands.Context, room: str, rule: int):
        await self.delrule(ctx, room, rule)

    # config toggle-emoji
    @config.subcommand(
        name='toggle-emoji',
        description=language.desc('config.toggle-emoji'),
        description_localizations=language.slash_desc('config.toggle-emoji')
    )
    @application_checks.has_permissions(manage_guild=True)
    async def toggle_emoji_slash(self, ctx: nextcord.Interaction):
        await self.toggle_emoji(ctx)

    @config_legacy.command(name='toggle-emoji')
    @commands.has_permissions(manage_guild=True)
    async def toggle_emoji_legacy(self, ctx: commands.Context):
        await self.toggle_emoji(ctx)

    # config filters
    @config.subcommand(
        name='filters',
        description=language.desc('config.filters'),
        description_localizations=language.slash_desc('config.filters')
    )
    @restrictions.not_banned()
    async def filters_slash(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('config.filters.room', required=False),
            query: Optional[str] = slash.option('config.filters.query', required=False)
    ):
        await self.filters(ctx, room=room, query=query)

    @config_legacy.command(name='filters')
    @restrictions_legacy.not_banned()
    async def filters_legacy(self, ctx: commands.Context, room: Optional[str] = None, query: Optional[str] = None):
        await self.filters(ctx, room=room, query=query)

    @filters_slash.on_autocomplete("query")
    async def filters_autocomplete(self, ctx: nextcord.Interaction, query: str):
        possible = []
        for bridge_filter in self.bot.bridge.filters.keys():
            if query.lower() in bridge_filter.lower():
                possible.append(bridge_filter)
        return await ctx.response.send_autocomplete(possible[:25])

    # config settings
    @config.subcommand(
        name='settings',
        description=language.desc('config.settings'),
        description_localizations=language.slash_desc('config.settings')
    )
    @restrictions.not_banned()
    async def settings_slash(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('config.settings.room', required=False),
            query: Optional[str] = slash.option('config.settings.query', required=False)
    ):
        await self.settings(ctx, room=room, query=query)

    @config_legacy.command(name='settings')
    @restrictions_legacy.not_banned()
    async def settings_legacy(self, ctx: commands.Context, room: Optional[str] = None, query: Optional[str] = None):
        await self.settings(ctx, room=room, query=query)

    @settings_slash.on_autocomplete("query")
    async def settings_autocomplete(self, ctx: nextcord.Interaction, query: str):
        possible = []
        for bridge_setting in settings_keys:
            if query.lower() in bridge_setting.lower():
                possible.append(bridge_setting)
        return await ctx.response.send_autocomplete(possible[:25])

def setup(bot):
    bot.add_cog(Config(bot))
