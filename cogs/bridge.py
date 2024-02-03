import discord
import aiofiles
import hashlib
import ast
from discord.ext import commands
import traceback
import time
from datetime import datetime
import random
import string

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)
moderators = []

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def genid():
    value = ''
    for i in range(6):
        letter = random.choice(string.ascii_lowercase+string.digits)
        value = '{0}{1}'.format(value,letter)
    return value

class Bridge(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(self.bot, 'bridged'):
            self.bot.bridged = {}
        if not hasattr(self.bot, 'owners'):
            self.bot.owners = {}
        if not hasattr(self.bot, 'origin'):
            self.bot.origin = {}
        if not hasattr(self.bot, 'prs'):
            self.bot.prs = {}
        if not hasattr(self.bot, 'notified'):
            self.bot.notified = []

    @commands.command(aliases=['find'])
    async def identify(self,ctx):
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members) and not ctx.author.id==356456393491873795:
            return
        try:
            msg = ctx.message.reference.cached_message
            if msg==None:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except:
            return await ctx.send('Invalid message!')
        hookfound = False
        for key in self.bot.db['rooms']:
            room_guilds = self.bot.db['rooms'][key]
            if f'{msg.webhook_id}' in f'{room_guilds}':
                hookfound = True
                break
        if not hookfound:
            return await ctx.send('I didn\'t forward this!')
        identifier = msg.author.name.split('(')
        identifier = identifier[len(identifier)-1].replace(')','')
        username = msg.author.name[:-9]
        found = False
        origin_guild = None
        origin_user = None
        for guild in self.bot.guilds:
            hashed = encrypt_string(f'{guild.id}')
            guildhash = identifier[3:]
            if hashed.startswith(guildhash):
                origin_guild = guild
                userhash = identifier[:-3]
                try:
                    matches = list(filter(lambda x: encrypt_string(f'{x.id}').startswith(userhash), guild.members))
                    if len(matches)==1:
                        origin_user = matches[0]
                    else:
                        if len(matches==0):
                            raise ValueError()
                        text = f'Found multiple matches for {origin_guild.name} ({origin_guild.id})'
                        for match in matches:
                            text = text + '\n{match} ({match.id})'
                        return await ctx.send(text)
                    found = True
                except:
                    continue
        
        if found:
            if ctx.author.id in moderators:
                try:
                    for key in self.bot.bridged:
                        origin_msg = self.bot.bridged[key]
                        values = list(origin_msg.values())
                        if ctx.message.reference.message_id in values:
                            origin_msg_id = key
                            break
                    await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})\nOriginal ID {origin_msg_id}')
                except:
                    raise
                    await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})\nCould not find origin message ID')
            else:
                await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})')
        else:
            await ctx.send('Could not identify user!')

    @commands.command()
    async def getbridged(self,ctx,*,msg_id):
        if not ctx.author.id in moderators:
            return
        try:
            content = self.bot.bridged[msg_id]
            await ctx.send(f'{content}')
        except:
            await ctx.send('No matches found!')

    @commands.command()
    async def nickname(self,ctx,*,nickname=''):
        if len(nickname) > 25:
            return await ctx.send('Please keep your nickname within 25 characters.')
        if len(nickname)==0:
            self.bot.db['nicknames'].pop(f'{ctx.author.id}',None)
        else:
            self.bot.db['nicknames'].update({f'{ctx.author.id}':nickname})
        self.bot.db.save_data()
        await ctx.send('Nickname updated.')

    @commands.command()
    async def emojis(self,ctx,*,index=1):
        text = ''
        index = index - 1
        if index < 0:
            return await ctx.send('what')
        offset = index*20
        emojis = []
        for emoji in self.bot.emojis:
            if emoji.guild_id in self.bot.db['emojis']:
                emojis.append(emoji)
        for i in range(20):
            try:
                emoji = emojis[i+offset]
            except:
                break
            emoji_text = f'<:{emoji.name}:{emoji.id}>'
            if emoji.animated:
                emoji_text = f'<a:{emoji.name}:{emoji.id}>'
            if len(text)==0:
                text = f'- {emoji_text} {emoji.name}'
            else:
                text = f'{text}\n- {emoji_text} {emoji.name}'
        if len(text)==0:
            return await ctx.send('Out of range!')
        pages = len(emojis)//20
        if len(emojis) % 20 > 0:
            pages += 1
        embed = discord.Embed(title='UniChat Emojis list',description='To use an emoji, simply send `[emoji: emoji_name]`.\nIf there\'s emojis with duplicate names, use `[emoji2: emoji_name]` to send the 2nd emoji with that name.\n'+text)
        embed.set_footer(text=f'Page {index+1}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def emoji(self,ctx,*,emoji=''):
        # wip
        return

    @commands.command()
    async def delete(self,ctx):
        '''Deletes all bridged messages. Does not delete the original.'''
        try:
            msg_id = ctx.message.reference.message_id
        except:
            return await ctx.send('No message!')
        
        ownedby = []
        if f'{ctx.author.id}' in list(self.bot.owners.keys()):
            ownedby = self.bot.owners[f'{ctx.author.id}']
        if not msg_id in ownedby and not ctx.author.id in moderators:
            return await ctx.send('You didn\'t send this message!')

        # Is this the parent?
        if not f'{msg_id}' in list(self.bot.bridged.keys()):
            # Not the parent.
            found = False
            for key in self.bot.bridged:
                if msg_id in list(self.bot.bridged[key].values()):
                    # Found the parent!
                    found = True
                    msg_id = int(key)
                    break
            if not found:
                # Nothing.
                return await ctx.send('Could not find message in cache!')

        hooks = await ctx.channel.webhooks()
        found = False
        origin_room = 0
        
        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                hook_ids = data.setdefault(f'{ctx.guild.id}', [])
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        deleted = 0

        try:
            origins = self.bot.origin[f'{msg_id}']
            guild = self.bot.get_guild(origins[0])
            ch = guild.get_channel(origins[1])
            try:
                msg = await ch.fetch_message(msg_id)
                await msg.delete()
                if msg.webhook_id==None:
                    # Parent is a user/bot message.
                    # Since we have something to delete bridged copies on parent delete,
                    # don't bother deleting the copies.
                    # (note: webhook parents don't have bridged copies automatically deleted)
                    return await ctx.send('Deleted parent, bridged messages should be automatically deleted.')
            except:
                # Parent may be a webhook message, so try to delete as webhook.
                hook_ids = data.setdefault(key, [])
                try:
                    hooks = await guild.webhooks()
                except:
                    raise ValueError('no hooks')
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        await webhook.delete_message(msg_id)
                        break
        except:
            # Failed to delete, move on
            pass

        for key in data:
            hook_ids = data.setdefault(key, [])
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.delete_message(self.bot.bridged[f'{msg_id}'][key])
                        deleted += 1
                    except:
                        # likely deleted msg
                        # skip cache check as it's already been done
                        pass
                    break

        await ctx.send(f'Deleted {deleted} forwarded messages')

    @commands.context_command(name='Delete message')
    async def delete_ctx(self,ctx,msg: discord.Message):
        # wip
        msg_id = msg.id

    @commands.command(hidden=True)
    async def testreg(self,ctx,*,args=''):
        if not ctx.author.id==356456393491873795:
            return
        if 'dereg' in args:
            await self.bot.register_application_commands(commands=[])
            return await ctx.send('gone, reduced to atoms (hopefully)')
        toreg = []
        for command in self.bot.commands:
            if isinstance(command, commands.core.ContextMenuCommand):
                toreg.append(command)
        print(f'Registering: {toreg}')
        await self.bot.register_application_commands(commands=toreg)
        return await ctx.send(f'Registered {len(toreg)} commands to bot')

    @commands.Cog.listener()
    async def on_message(self,message):
        if not message.webhook_id==None:
            # webhook msg
            return

        if message.guild==None:
            return

        if message.content.startswith(self.bot.command_prefix):
            cmd = message.content.replace(self.bot.command_prefix,'',1).split()[0]
            if not self.bot.get_command(cmd)==None:
                return

        gbans = self.bot.db['banned']

        if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
            ct = time.time()
            cdt = datetime.utcnow()
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil==0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    self.bot.db.update()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil==0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.update()
                else:
                    return

        if message.author.id==self.bot.user.id:
            return

        try:
            hooks = await message.channel.webhooks()
        except:
            return
        found = False
        origin_room = 0
        
        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                hook_ids = data.setdefault(f'{message.guild.id}', [])
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        og_embeds = []
        if message.author.bot or len(message.embeds) > 0:
            for emb in message.embeds:
                og_embeds.append(emb)

        if not found:
            return

        if 'discord.gg/' in message.content or 'discord.com/invite/' in message.content:
            try:
                await message.delete()
            except:
                pass
            return await message.channel.send(f'<@{message.author.id}> Invites aren\'t allowed!')

        if not message.guild.explicit_content_filter==discord.ContentFilter.all_members:
            return await message.channel.send('**Hold up a sec!**\nThis server isn\'t letting Discord make sure nothing NSFW is being sent in SFW channels, meaning adult content could be sent over UniChat. We don\'t want that!'
                                  +'\n\nPlease ask your server admins to enable explicit content scanning for **all members**.',reference=message)
        elif message.channel.nsfw:
            return await message.channel.send('**Hold up a sec!**\nThis channel is marked as NSFW, meaning Discord won\'t go mad when you try sending adult content over UniChat. We don\'t want that!'
                                  +'\n\nPlease ask your server admins to unmark this channel as NSFW.',reference=message)

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = ' ('+user_hash + guild_hash+')'

        hookmsg_ids = {}
        content = message.content
        
        emojified = False

        def replace_nth_occurance(string,srch,rplc,n):
            Sstring = string.split(srch)
            if len(Sstring) > (n):
                return f'{srch.join(Sstring[:(n)])}{rplc}{srch.join(Sstring[n:])}' 
            else:
                return string
            
        content = message.content.split('[emoji')
        parse_index = -1
        for element in content:
            parse_index += 1
            if not message.content.startswith('[emoji') and parse_index==0:
                continue
            if message.author.bot or not '[emoji' in message.content:
                break
            if not ']' in element:
                continue
            parts = element.split(']')[0].split(': ')
            try:
                name = parts[1]
                if name.endswith('\\'):
                    raise ValueError()
            except:
                continue

            noindex = False
            try:
                index = int(parts[0])
            except:
                noindex = True
                index = 1

            skip = []
            failed = False
            emoji_text = ''
            
            for x in range(index):
                emoji = discord.utils.find(lambda e: e.name==name and not e.id in skip and e.guild_id in self.bot.db['emojis'], self.bot.emojis)
                if emoji==None:
                    failed = True
                    break
                skip.append(emoji.id)
                emoji_text = f'<:{emoji.name}:{emoji.id}>'
                if emoji.animated:
                    emoji_text = f'<a:{emoji.name}:{emoji.id}>'

            if failed:
                continue
            
            if noindex:
                message.content = message.content.replace(f'[emoji: {name}]',emoji_text,1)
            else:
                message.content = message.content.replace(f'[emoji{index}: {name}]',emoji_text,1)
            emojified = True

        is_pr = False
        is_pr_ref = False
        ref_id = ''
        if origin_room==1:
            is_pr = True
            pr_id = genid()
            pr_ids = {}
        if origin_room==2:
            passed = True
            if message.content.startswith('['):
                components = message.content.split(']',1)
                if len(components)==1:
                    passed = False
                else:
                    ref_id = components[0].replace('[','')
                    if ref_id=='latest' or ref_id=='newest' or ref_id=='recent':
                        ref_id = list(self.bot.prs.keys())[len(list(self.bot.prs.keys()))-1]
                    if not ref_id in list(self.bot.prs.keys()):
                        return await ctx.send('This isn\'t a valid PR ID!')
                    else:
                        content = components[1]
                        while content.startswith(' ') or content.startswith('\n'):
                            if content.startswith(' '):
                                content = content.replace(' ','',1)
                            else:
                                content = content.replace('\n','',1)
                        if len(content)==0:
                            passed = False
            else:
                passed = False
            if passed:
                is_pr = True
                is_pr_ref = True
                message.content = content

        pr_deletefail = False

        if emojified or is_pr:
            try:
                await message.delete()
            except:
                if is_pr_ref:
                    return await message.channel.send('I need to be able to delete messages in order to process PR references.',reference=message)
                elif is_pr and not emojified:
                    pr_deletefail = True
                    await message.channel.send(f'Assigned PR ID: `{pr_id}`\nUse this to reference this PR message.',reference=message)
                else:
                    return await message.channel.send('I need to be able to delete messages in order to process global emojis.',reference=message)

        identifier_cache = identifier
        banned = False

        if not (message.type==discord.MessageType.default or
                message.type==discord.MessageType.reply or
                message.type==discord.MessageType.application_command):
            return
        
        # Forwarding
        for key in data:
            blocked = False
            sameguild = False
            if len(identifier)==0:
                # restore identifier
                identifier = identifier_cache
            if int(key)==message.guild.id:
                sameguild = True
                identifier = ''
                if not emojified and not is_pr or pr_deletefail:
                    if is_pr and not is_pr_ref:
                        pr_ids.update({f'{message.guild.id}':message.id})

                    # Not using webhooks - make parent the message.
                    self.bot.origin.update({f'{message.id}':[message.guild.id,message.channel.id]})
                    continue
            if key in list(gbans.keys()):
                continue
            banlist = []
            if f'{message.guild.id}' in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][f'{message.guild.id}']
            if (message.author.id in banlist or message.guild.id in banlist) and not message.author.id in moderators:
                continue
            hook_ids = data.setdefault(key, [])
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            dont_attach = False
                
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        url = message.author.avatar.url
                    except:
                        url = None
                    files = []
                    index = 0
                    for attachment in message.attachments:
                        if dont_attach:
                            break
                        if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                            not 'image' in attachment.content_type):
                            continue
                        file = await attachment.to_file(use_cached=True,spoiler=attachment.is_spoiler())
                        files.append(file)
                        index += 1
                    if not message.reference==None or is_pr:
                        if not message.reference==None:
                            msg = message.reference.cached_message
                            if msg==None:
                                msg = await message.channel.fetch_message(message.reference.message_id)

                            if not msg.webhook_id==None:
                                author = f'@{msg.author.name}'
                                identifier_resp = author.split('(')
                                identifier_resp = identifier_resp[len(identifier_resp)-1]
                                author = author[:-(2+len(identifier_resp))]
                            else:
                                if f'{msg.author.id}' in gbans or f'{msg.guild.id}' in gbans:
                                    banned = True
                                elif (msg.author.id in banlist or msg.guild.id in banlist) and not msg.author.id in moderators:
                                    blocked = True
                                author = f'{msg.author.name}#{msg.author.discriminator}'
                                if msg.author.discriminator=='0':
                                    author = f'@{msg.author.name}'
                            content = msg.content
                            if len(msg.content)==0:
                                if len(msg.attachments)==0:
                                    if len(msg.embeds) > 0:
                                        content = '[embed]'
                                    else:
                                        content = '[no content]'
                                else:
                                    content = ''
                                    for attachment in msg.attachments:
                                        if content=='':
                                            content = f'[{attachment.filename}]'
                                        else:
                                            content = f'{content}\n[{attachment.filename}]'
                            if banned or blocked:
                                author = '[hidden]'
                                if banned:
                                    content = '**GLOBAL BANNED - MESSAGE HIDDEN**\nThe author of this message replied to a global banned user or server. Global bans are placed on users and servers that break UniChat rules continuously or/and severely.'
                                elif blocked:
                                    content = '**SERVER BANNED - MESSAGE HIDDEN**\nThe author of this message replied to a server banned user or server. Server bans are placed on users and servers by this server\'s moderators.\nAsk them to unblock the origin user or server.'
                            embed = discord.Embed(title=f'Replying to {author}',description=content,color=0xeba134)
                            if banned or blocked:
                                embed.color = 0xff0000
                            if not msg.author.avatar==None and not banned and not blocked:
                                embed.set_author(name=author,icon_url=msg.author.avatar.url)
                            else:
                                embed.set_author(name=author)
                        embeds = og_embeds.copy()
                        components = None
                        if False: #len(checked_embeds)==0: - embeds disabled for now
                            embeds = [embed]
                        else:
                            if not message.reference==None:
                                if not message.author.bot:
                                    embeds = []
                                else:
                                    embeds = message.embeds
                                ButtonStyle = discord.ButtonStyle
                                if banned or blocked:
                                    btns = discord.ui.ActionRow(
                                        discord.ui.Button(style=ButtonStyle.red, label=f'Replying to [hidden]',disabled=True)
                                        )
                                else:
                                    try:
                                        globalmoji = False
                                        if msg.webhook_id==None:
                                            reference_msg_id = self.bot.bridged[f'{msg.id}'][f'{webhook.guild_id}']
                                        else:
                                            try:
                                                reference_msg_id = self.bot.bridged[f'{msg.id}'][f'{webhook.guild_id}']
                                                globalmoji = True
                                            except:
                                                for key in self.bot.bridged:
                                                    entry = self.bot.bridged[key]
                                                    if msg.id in entry.values():
                                                        try:
                                                            reference_msg_id = self.bot.bridged[f'{key}'][f'{webhook.guild_id}']
                                                        except:
                                                            msg = await webhook.channel.fetch_message(int(key))
                                                            if not msg==None:
                                                                reference_msg_id = int(key)
                                                        break
                                        if globalmoji:
                                            author = f'@{msg.author.name}'
                                        if len(msg.content) > 80:
                                            trimmed = msg.content[:-(len(msg.content)-77)]+'...'
                                        else:
                                            trimmed = msg.content
                                        trimmed = trimmed.replace('\n',' ')
                                        btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=ButtonStyle.link, label=f'Replying to {author}',disabled=False,
                                                              url=f'https://discord.com/channels/{webhook.guild_id}/{webhook.channel_id}/{reference_msg_id}')
                                            )
                                        if len(trimmed) > 0:
                                            btns2 = discord.ui.ActionRow(
                                                discord.ui.Button(style=ButtonStyle.blurple, label=trimmed, disabled=True)
                                                )
                                        else:
                                            btns2 = discord.ui.ActionRow(
                                                discord.ui.Button(style=ButtonStyle.blurple, label=f'x{len(msg.embeds)+len(msg.attachments)}', emoji='\U0001F3DE',disabled=True)
                                                )
                                    except:
                                        if is_pr_ref and sameguild:
                                            btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=ButtonStyle.link, label=f'Replying to {author}',disabled=False,
                                                              url=f'https://discord.com/channels/{webhook.guild_id}/{webhook.channel_id}/{message.reference.message_id}')
                                            )
                                        else:
                                            if msg.author.id==self.bot.user.id:
                                                btns = discord.ui.ActionRow(
                                                    discord.ui.Button(style=ButtonStyle.gray, label=f'Replying to [system message]',disabled=True)
                                                    )
                                            else:
                                                btns = discord.ui.ActionRow(
                                                    discord.ui.Button(style=ButtonStyle.gray, label=f'Replying to [unknown]',disabled=True)
                                                    )
                            try:
                                if blocked or banned:
                                    raise ValueError()
                                if is_pr:
                                    if is_pr_ref:
                                        try:
                                            hook = data.setdefault(f'{webhook.guild.id}', [])[0]
                                            hooks_2 = await webhook.guild.webhooks()
                                            for hook_obj in hooks_2:
                                                if hook_obj.id==hook:
                                                    hook = hook_obj
                                                    break
                                            reference_msg_id = self.bot.prs[ref_id][f'{webhook.guild_id}']
                                            ref_btns = discord.ui.ActionRow(
                                                discord.ui.Button(style=discord.ButtonStyle.link, label=f'Reference to PR #{ref_id}',
                                                                  url=f'https://discord.com/channels/{webhook.guild_id}/{hook.channel_id}/{reference_msg_id}',
                                                                  emoji='\U0001F517',
                                                                  disabled=False)
                                                )
                                        except:
                                            ref_btns = discord.ui.ActionRow(
                                                discord.ui.Button(style=discord.ButtonStyle.gray, label=f'Reference to PR #{ref_id}',emoji='\U0001F517',disabled=True)
                                                )
                                    else:
                                        ref_btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=discord.ButtonStyle.blurple, label=f'PR ID: {pr_id}',emoji='\U0001F4AC',disabled=True)
                                            )
                                    try:
                                        components = discord.ui.MessageComponents(ref_btns,btns,btns2)
                                    except:
                                        try:
                                            components = discord.ui.MessageComponents(ref_btns,btns)
                                        except:
                                            components = discord.ui.MessageComponents(ref_btns)
                                else:
                                    components = discord.ui.MessageComponents(btns,btns2)
                            except:
                                components = discord.ui.MessageComponents(btns)
                        author_resp = nicknames.setdefault(f'{message.author.id}', message.author.global_name)
                        if sameguild:
                            author_resp = message.author.nick
                            if author_resp==None:
                                author_resp = message.author.global_name
                        try:
                            msg = await webhook.send(avatar_url=url,username=author_resp+identifier,
                                               content=message.content,embeds=embeds,
                                               files=files,allowed_mentions=mentions,wait=True,components=components)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}':[message.guild.id,message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}':msg.id})
                            if is_pr and not is_pr_ref:
                                pr_ids.update({f'{webhook.guild_id}':msg.id})
                        except discord.HTTPException as e:
                            if e.code==413:
                                files = []
                                msg = await webhook.send(avatar_url=url,username=author+identifier,
                                               content=message.content,embeds=embeds,
                                               allowed_mentions=mentions,wait=True)
                                await message.channel.send('An attachment or two was too large - attachments will not be sent.\nPlease send a URL instead.',reference=message)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}':[message.guild.id,message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}':msg.id})
                            if is_pr and not is_pr_ref:
                                pr_ids.update({f'{webhook.guild_id}':msg.id})
                    else:
                        if message.author.bot:
                            embeds = message.embeds
                        else:
                            embeds = []                           
                        author = self.bot.db['nicknames'].setdefault(f'{message.author.id}', message.author.global_name)
                        if sameguild:
                            author = message.author.nick
                            if author==None:
                                author = message.author.global_name
                        try:
                            msg = await webhook.send(avatar_url=url,username=author+identifier,
                                           content=message.content,embeds=embeds,
                                           files=files,allowed_mentions=mentions,wait=True)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}':[message.guild.id,message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}':msg.id})
                        except discord.HTTPException as e:
                            if e.code==413:
                                files = []
                                msg = await webhook.send(avatar_url=url,username=author+identifier,
                                               content=message.content,embeds=embeds,
                                               allowed_mentions=mentions,wait=True)
                                await message.channel.send('An attachment or two was too large - attachments will not be sent.\nPlease send a URL instead.',reference=message)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}':[message.guild.id,message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}':msg.id})
        if is_pr and not is_pr_ref:
            self.bot.prs.update({pr_id:pr_ids})
        if emojified:
            self.bot.bridged.update({f'{sameguild_id}':hookmsg_ids})
        else:
            self.bot.bridged.update({f'{message.id}':hookmsg_ids})
        try:
            del files
        except:
            pass        

    @commands.Cog.listener()
    async def on_message_edit(self,before,after):
        if before.content==after.content:
            return
        
        message = after

        if message.guild==None:
            return

        gbans = self.bot.db['banned']

        if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
            ct = time.time()
            cdt = datetime.utcnow()
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil==0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    self.bot.db.update()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil==0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.update()
                else:
                    return
        
        if not message.webhook_id==None:
            # webhook msg, dont bother
            return
        
        if message.author.id==self.bot.user.id:
            return

        hooks = await message.channel.webhooks()
        found = False
        origin_room = 0
        
        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                hook_ids = data.setdefault(f'{message.guild.id}', [])
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = user_hash + guild_hash

        for key in data:
            if int(key)==message.guild.id:
                continue
            if key in gbans:
                continue
            banlist = []
            if f'{message.guild.id}' in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][f'{message.guild.id}']
            if message.author.id in banlist and not message.author.id in moderators:
                continue
            hook_ids = data.setdefault(key, [])
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.edit_message(self.bot.bridged[f'{message.id}'][key],
                                        content=message.content,allowed_mentions=mentions)
                    except:
                        # likely deleted msg
                        try:
                            self.bot.bridged[f'{message.id}']
                        except:
                            # message wiped from cache
                            return
                        pass

    @commands.Cog.listener()
    async def on_message_delete(self,message):
        gbans = self.bot.db['banned']

        if f'{message.author.id}' in gbans or f'{message.guild.id}' in gbans:
            return
        
        if not message.webhook_id==None:
            # webhook msg, dont bother
            return

        if message.author.id==self.bot.user.id:
            return

        hooks = await message.channel.webhooks()
        found = False
        origin_room = 0
        
        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                hook_ids = data.setdefault(f'{message.guild.id}', [])
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = user_hash + guild_hash

        guild = self.bot.get_guild(1097238317881380984)
        ch = guild.get_channel(1189146414735953941)
        
        roomname = list(self.bot.db['rooms'].keys())[origin_room]

        content = message.content
        
        if len(message.content)==0:
            content = '[no content]'
        embed = discord.Embed(title=f'Message deleted from `{roomname}`',description=content)
        embed.add_field(name='Embeds',value=f'{len(message.embeds)} embeds, {len(message.attachments)} files',inline=False)
        embed.add_field(name='IDs',value=f'MSG: {message.id}\nSVR: {message.guild.id}\nUSR: {message.author.id}',inline=False)
        if message.author.discriminator=='0':
            author = f'@{message.author.name}'
        else:
            author = f'{message.author.name}#{message.author.discriminator}'
        try:
            embed.set_author(name=author,icon_url=message.author.avatar.url)
        except:
            embed.set_author(name=author)
        await ch.send(embed=embed)

        for key in data:
            if int(key)==message.guild.id:
                continue
            if key in gbans:
                continue
            banlist = []
            if f'{message.guild.id}' in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][f'{message.guild.id}']
            if message.author.id in banlist and not message.author.id in moderators:
                continue
            hook_ids = data.setdefault(key, [])
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.delete_message(self.bot.bridged[f'{message.id}'][key])
                    except:
                        # likely deleted msg
                        try:
                            self.bot.bridged[f'{message.id}']
                        except:
                            # message wiped from cache
                            return
                        pass

def setup(bot):
    bot.add_cog(Bridge(bot))
