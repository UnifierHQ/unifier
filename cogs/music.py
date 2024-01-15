import re

from discord.ext import commands
import discord
import lavalink
import aiofiles
import ast
import sys
import os
import time
import random
import copy
import textwrap
import inspect
import io
import aiohttp
from contextlib import redirect_stdout
import base64
import psutil
import cpuinfo
import platform
import traceback

writeerr = sys.stderr.write

nodesdown = []

# Node types
# 0: Primary
#    Bot will try to connect to this node when creating the player.
#
# 1: Performance
#    Secondary high-performance node.
#
# 2: Standard
#    Secondary standard-performance node.

lavalink_nodes = [
    {'enable':True,
     'name':'Moegiiro',
     'id':'eu-moegiiro',
     'host':'45.65.114.160',
     'port':6019,
     'region':'europe',
     'password':'!qto#QTs83LZET',
     'type':0,
     'secure':False
     },
    {'enable':True,
     'name':'Hinata',
     'id':'uk-hinata',
     'host':'pnode2.danbot.host',
     'port':7258,
     'region':'uk',
     'password':'sEp7PM4QaSkY@$',
     'type':1,
     'secure':False
     },
##    {'enable':False,
##     'name':'[Testing] Sillydev - Berry',
##     'id':'eu-berry',
##     'host':'95.214.180.27',
##     'port':6040,
##     'password':'discord.gg/sillydev',
##     'region':'europe',
##     'type':2,
##     'secure':False
##     }
    
    ]

class DevNull:
    DevNullified = True
    
    def write(self, msg):
        if msg.startswith('[Node:') and 'Invalid response received' in msg:
            nodename = msg.replace('[Node:','',1).split('] ')[0]
            content = msg.replace('[Node:','',1).split('] ')[1]
            if nodename in nodesdown:
                pass
            else:
                nodesdown.append(nodename)
                for node in lavalink_nodes:
                    if node['name']==nodename:
                        if node['type']==0:
                            log(type='LAV',status='error',content=f'Could not connect to primary node {nodename}. Will keep trying.')
                            log(type='LAV',status='error',content=f'{nodename}: {content}')
                        else:
                            log(type='LAV',status='warn',content=f'Could not connect to secondary node {nodename}. Will keep trying.')
                            log(type='LAV',status='warn',content=f'{nodename}: {content}')
                        break
        elif msg.startswith('[Node:'):
            nodename = msg.replace('[Node:','',1).split('] ')[0]
            content = msg.replace('[Node:','',1).split('] ')[1]
            log(type='LAV',status='info',content=f'{nodename}: {content}')
        elif msg.startswith('Unable to move players') or msg.startswith('Request "GET version" failed'):
            pass
        else:
            writeerr(msg)


try:
    sys.stderr.DevNullified
except:
    sys.stderr = DevNull()

url_rx = re.compile(r'https?://(?:www\.)?.+')
activity = {}
rainbows = {}
tracks = {}
disable_lavalink = False
debug = False
localhost = False

noeval = '''```-------------No eval?-------------
⠀⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀```'''

def cleanup_code(content):
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    return content.strip('` \n')

osinfo = platform.platform()
if 'macOS' in osinfo:
    localhost = False
    debug = True

async def update(key,content):
    activity.update( {'%s' % key : content} )

def cleanup(guild,name):
    try:
        del activity['%s' % guild]
    except:
        pass
    try:
        del activity['%s_playing' % guild]
    except:
        pass
    try:
        os.remove('%s.mp3' % name)
    except:
        pass

async def getacc(user):
    import aiofiles
    import ast
    try:
        async with aiofiles.open('%s_account.txt' % user,'r',encoding='utf-8') as acc:
            data = await acc.read()
            await acc.close()
    except:
        data = ''
    account1 = data
    try:
        async with aiofiles.open('%s_suspension.txt' % account1,'r',encoding='utf-8') as acc:
            data = await acc.read()
            await acc.close()
    except:
        data = 'no'
    try:
        suspension = data
    except:
        suspension = 'no'
    if suspension=='yes':
        account1=''
    return account1

async def applytheme(userid,embed=None):
    theme = 0
    themename = 'Pixels Blue'
    themecolor = 0xb5eeff
    if embed==None:
        return {'id': theme,'name': themename,'color': themecolor}
    if f'{embed.color}'=='#ff0000' or f'{embed.color}'=='#ffff00' or f'{embed.color}'=='#d9d9d9':
        # likely a system msg, can't apply
        return embed
    embed.color = themecolor
    return embed

def log(type='???',status='ok',content='None'):
    from time import ctime, gmtime, strftime
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
        raise ValueError('Invalid status type provided')
    print(f'[{type} | {time1} | {status}] {content}')

class EventHandler:
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
    
    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        guild_id = int(event.player.guild_id)
        if guild_id in self.bot.nodeswitch:
            return
        guild = self.bot.get_guild(guild_id)
        try:
            tracks.pop(f'{event.player.guild_id}')
        except:
            pass
        try:
            await guild.voice_client.disconnect(force=True)
        except AttributeError:
            # No voice client, likely disconnected so avoiding errors here
            pass

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        track = copy.deepcopy(event.track)
        tracks.update({f'{event.player.guild_id}':track})

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        guild_id = int(event.player.guild_id)
        if guild_id in self.bot.nodeswitch:
            return
        try:
            tracks.pop(f'{event.player.guild_id}')
        except:
            pass
        await update('%s_skip' % guild_id,0)

    @lavalink.listener(lavalink.TrackStuckEvent)
    async def track_stuck(self, event: lavalink.TrackStuckEvent):
        log(type='LAV',status='warn',content=f'Track {event.track.uri} on {event.player.node.name} got stuck!')

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_error(self, event: lavalink.TrackExceptionEvent):
        log(type='LAV',status='error',content=f'Track {event.track.uri} on {event.player.node.name} threw an error!')
        trimmed = event.message
        trimmed2 = event.cause
        if len(event.message)>200 or len(event.cause)>200:
            filename = f'error_{round(time.time(),3)}.txt'
            x = open(f'lavalink_logs/{filename}','w+',encoding='utf-8')
            x.write(f'Caused by: {event.cause}\n\n{event.message}')
            x.close()
            if len(event.message)>200:
                trimmed = event.message[:-(len(event.message)-200)]+f'...(check lavalink_logs/{filename})'
            else:
                trimmed2 = event.cause[:-(len(event.cause)-200)]+f'...(check lavalink_logs/{filename})'
        log(type='LAV',status='error',content=f'{trimmed}')
        log(type='LAV',status='error',content=f'{trimmed2}')

    @lavalink.listener(lavalink.NodeReadyEvent)
    async def node_ready(self, event: lavalink.NodeReadyEvent):
        log(type='LAV',status='ok',content=f'Node {event.node._node.name} ({event.node._host}:{event.node._port}) is ready - session ID {event.session_id}')
        if not event.node._node.name in self.bot.nodesready:
            self.bot.nodesready.append(event.node._node.name)
        try:
            nodesdown.remove(event.node._node.name)
        except:
            pass

    @lavalink.listener(lavalink.NodeDisconnectedEvent)
    async def node_disconnect(self, event: lavalink.NodeDisconnectedEvent):
        host = '[unknown]'
        port = '[unknown]'
        for node in lavalink_nodes:
            if node['name']==event.node.name:
                host = node['host']
                port = node['port']
        try:
            self.bot.nodesready.remove(event.node._node.name)
        except:
            pass
        log(type='LAV',status='warn',content=f'Node {event.node.name} ({host}:{port}) disconnected ({event.code}): {event.reason}')

class LavalinkVoiceClient(discord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            for node in lavalink_nodes:
                if node['enable']:
                    self.client.lavalink.add_node(node['host'], node['port'], node['password'], node['region'], node['name'], node['secure'])
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_SERVER_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_STATE_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        '''touse = None
        dead = False
        standby = []
        for node in self.lavalink.node_manager.nodes:
            try:
                primary = False
                for regnode in lavalink_nodes:
                    if node.name==regnode['name']:
                        if regnode['type']==0:
                            primary = True
                        break
                latency = await node.get_rest_latency()
                if latency==-1:
                    raise ValueError()
                if not primary and not regnode['name']=='Moegiiro':
                    standby.append(node)
                    continue
                touse = node
                break
            except:
                dead = True
                log(type='LAV',status='error',content=f'Node {node.name} failed. Trying next node.')
        if dead:
            if touse==None:
                if len(standby)==0:
                    return
                touse = standby[0]
            log(type='LAV',status='ok',content=f'Node {touse.name} is active, using it instead.')
            print('connect')'''
        #if touse==None:
        try:
            player = self.lavalink.player_manager.get(self.channel.guild.id)
        except:
            self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        '''else:
            self.lavalink.player_manager.remove(guild_id=self.channel.guild.id)
            player = self.lavalink.player_manager.create(guild_id=self.channel.guild.id,node=touse)'''
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the 
        # disconnect
        try:
            player.channel_id = None
        except:
            pass

        # destroy player so dead nodes don't ruin stuff
        self.lavalink.player_manager.remove(self.channel.guild.id)
        
        self.cleanup()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.localhost = localhost

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            for node in lavalink_nodes:
                if node['enable']:
                    bot.lavalink.add_node(node['host'], node['port'], node['password'], node['region'], node['name'], node['secure'])
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        if not hasattr(self.bot, 'nodeswitch'):
            self.bot.nodeswitch = []

        if not hasattr(self.bot, 'nodesready'):
            self.bot.nodesready = []

        self.lavalink: lavalink.Client = bot.lavalink
        self.lavalink.add_event_hooks(EventHandler(self.bot))

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """

        # lock commands if another bot of mine is already in there
        try:
            nev = ctx.guild.get_member(853979577156501564)
            nat = ctx.guild.get_member(411535418878590976)
            if nev==None or nat==None:
                pass
            else:
                if nev in ctx.author.voice.channel.members or nat in ctx.author.voice.channel.members:
                    if not ctx.guild.me in ctx.author.voice.channel.members:
                        if ctx.guild.me.id==nev.id:
                            userid = nat.id
                        else:
                            userid = nev.id
                        raise commands.CommandInvokeError(f'**<@{userid}> is already in there!**\nPlease use that bot to control music instead. If you want to use my music functions, then join a different voice channel.')
        except commands.CommandInvokeError:
            raise
        except:
            pass
        if ctx.guild.id==948937918347608085:
            admin = ctx.guild.get_role(956466393514143814)
            staff = ctx.guild.get_role(950276268593659925)
            if ctx.author.id==356456393491873795 or staff in ctx.author.roles or admin in ctx.author.roles:
                pass
            else:
                return False
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            banned = [f'{self.bot.command_prefix}music_nodes',
                      f'{self.bot.command_prefix}music_hardreload',
                      f'{self.bot.command_prefix}music_version']
            for cmd in banned:
                if ctx.message.content.startswith(cmd):
                    # cmd isnt for music interactions, call it a day
                    return guild_check
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.
        try:
            nev = ctx.guild.get_member(853979577156501564)
            nat = ctx.guild.get_member(411535418878590976)
            if nev==None or nat==None:
                pass
            else:
                if nev in ctx.author.voice.channel.members or nat in ctx.author.voice.channel.members:
                    if not ctx.guild.me in ctx.author.voice.channel.members:
                        if ctx.guild.me.id==nev.id:
                            userid = nev.id
                        else:
                            userid = nat.id
                        await ctx.send(f'**<@{userid}> is already in there!**\nPlease use that bot to control music instead. If you want to use my music functions, then join a different voice channel.')
                        return False
        except:
            pass
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            censored = f'{error.original}'.replace('143.42.49.184','[redacted]')
            if len(censored)==0:
                await ctx.send('[Empty exception]')
            else:
                await ctx.send(censored)
            if not f'{error.original}'.endswith('Please use that bot to control music instead. If you want to use my music functions, then join a different voice channel.'):
                raise
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        
        region = ctx.author.voice.channel.rtc_region
        try:
            should_connect = ctx.command.name in ('music_play','music_rickroll','music_fart','music_spooky','music_bruh','music_sus','music_laugh','music_wikipedia','music_nut','music_icecream','music_cringebomb','music_lofi')
        except:
            should_connect = False

        if should_connect:
            try:
                player = self.bot.lavalink.player_manager.get(ctx.guild.id)
                if player.is_playing or player.paused:
                    pass
            except:
                dead = False
                touse = None
                standby = []
                for node in self.lavalink.node_manager.nodes:
                    try:
                        primary = False
                        for regnode in lavalink_nodes:
                            if node.name==regnode['name']:
                                if regnode['type']==0:
                                    primary = True
                                break
                        latency = await node.get_rest_latency()
                        if latency==-1 or not regnode['name'] in self.bot.nodesready:
                            raise ValueError()
                        if not primary:
                            standby.append(node)
                            continue
                        touse = node
                        break
                    except:
                        log(type='LAV',status='error',content=f'Node {node.name} failed. Trying next node.')
                        dead = True
                if dead:
                    if touse==None:
                        log(type='LAV',status='error',content=f'All primary nodes down, using secondary nodes...')
                        if len(standby)==0:
                            log(type='LAV',status='error',content=f'All nodes down, cannot play music.')
                            await ctx.guild.voice_client.disconnect()
                            return await ctx.send('No nodes are available. Please try again later.')
                        log(type='LAV',status='ok',content=f'Using secondary node {standby[0].name} as no primary nodes are available.')
                        touse = standby[0]
                    else:
                        log(type='LAV',status='ok',content=f'Node {touse.name} is active, using it instead.')
                player = self.bot.lavalink.player_manager.create(ctx.guild.id,node=touse)
                if player.is_playing or player.paused:
                    pass
                else:
                    if type(region) is None:
                        region = ctx.guild.region
                    nodemgr = self.bot.lavalink.node_manager
                    nodes = nodemgr.nodes
                    touse_node = nodemgr.find_ideal_node(str(region))
                    query = ctx.message.content.replace(f'{self.bot.command_prefix}music_play ','',1)
                    query = query.strip('<>')
                    try:
                        lat = await touse_node.get_rest_latency()
                        if lat==-1 or not touse_node.name in self.bot.nodesready:
                            raise ValueError()
                        await player.change_node(touse_node)
                    except:
                        pass
        else:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('**OOPS**: You are not in a voice channel. :x:')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('**OOPS**: Not connected. :x:')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            print(permissions.connect, permissions.speak)
            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError('**OOPS**: I need the `CONNECT` and `SPEAK` permissions to play music. Please contact a server administrator. :x:')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('**OOPS**: You are not in my voice channel. :x:')

    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
        player = self.bot.lavalink.player_manager.get(member.guild.id)
        if player==None:
            return
        if member.id==self.bot.user.id:
            if after.channel==None and not before.channel==None:
                player.queue.clear()
                await player.stop()
                try:
                    await member.guild.voice_client.disconnect(force=True)
                except:
                    # already dc'd
                    return
                nodemgr = self.bot.lavalink.node_manager
                playing = 0
                for node in nodemgr.available_nodes:
                    playing += node.stats.playing_players
                if playing<=0:
                    for node in nodemgr.nodes:
                        nodemgr.remove_node(node)
                    del self.bot.lavalink
                    self.bot.unload_extension('cogs.music')
                    self.bot.load_extension('cogs.music')
                    log(type='BOT',status='info',content='Reloaded music cog due to inactivity to keep nodes connected')
            return
        await member.guild.query_members(limit=1, user_ids=[self.bot.user.id], cache=True)
        usr = member.guild.get_member(self.bot.user.id)
        if type(player) is None:
            return
        if after.channel==None and not before.channel==None:
            if usr in before.channel.members:
                allbot = True
                for member in before.channel.members:
                    if not member.bot:
                        allbot = False
                        break
                if not allbot:
                    return
                player.queue.clear()
                await player.stop()
                await member.guild.voice_client.disconnect(force=True)
                nodemgr = self.bot.lavalink.node_manager
                playing = 0
                for node in nodemgr.available_nodes:
                    playing += node.stats.playing_players
                if playing<=0:
                    for node in nodemgr.nodes:
                        nodemgr.remove_node(node)
                    del self.bot.lavalink
                    self.bot.unload_extension('cogs.music')
                    self.bot.load_extension('cogs.music')
                    log(type='BOT',status='info',content='Reloaded music cog due to inactivity to keep nodes connected')
        elif member.id==self.bot.user.id and not before.channel==None and after.voice.channel==None:
            await player.stop()
            player.queue.clear()
            await member.guild.voice_client.disconnect(force=True)
        else:
            try:
                if player.current['stream']:
                    return
                if not before.self_deaf and after.self_deaf:
                    if usr in after.channel.members:
                        human = 0
                        for member in before.channel.members:
                            if not member.bot:
                                human += 1
                        if human==1:
                            await player.set_pause(pause=True)
                elif before.self_deaf and not after.self_deaf:
                    if usr in after.channel.members:
                        human = 0
                        for member in before.channel.members:
                            if not member.bot:
                                human += 1
                        if human==1:
                            await player.set_pause(pause=False)
            except:
                pass

    @commands.command(hidden=True)
    async def music_eval(self,ctx,*,body):
        if ctx.author.id==356456393491873795:
            import io
            import traceback
            player = self.bot.lavalink.player_manager.get(ctx.guild.id) or None
            env = {
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                'source': inspect.getsource,
                'session':self.bot.session,
                'bot':self.bot,
                'player': player
            }

            env.update(globals())

            body = cleanup_code(body)
            stdout = io.StringIO()
            err = out = None

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                if 'bot.token' in body or 'password' in body:
                    return await ctx.send('Blocked phrase, can\'t eval!')
                exec(to_compile, env)
            except Exception as e:
                pass

            try:
                func = env['func']
            except Exception as e:
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` your code sucks <@356456393491873795>\n`2.` no megamind?')
                await ctx.author.send(f'```py\n{e.__class__.__name__}: {e}\n```')
                return
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` your code sucks <@356456393491873795>\n`2.` no megamind?')
                await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                if value=='':
                    pass
                else:
                    await ctx.send('```%s```' % value)
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @music_eval.error
    async def music_eval_error(self,ctx,error):
        if ctx.author.id==356456393491873795:
            if isinstance(error, commands.MissingRequiredArgument):
                try:
                    await ctx.send('no shit youre a certified dumbass <@356456393491873795> **YOU FORGOT THE DAMN CODE LMFAOOOOO**',file=discord.File(fp='nocode.png'))
                except:
                    try:
                        await ctx.send('no shit youre a certified dumbass <@356456393491873795> **YOU FORGOT THE DAMN CODE LMFAOOOOO**\nalso you (or the server mods) forgor :skull: to give me attach files perms so pls do that i guess')
                    except:
                        await ctx.author.send('ok green how dumb can you be, you forgot your code AND **YOU TRIED TO EVAL IN A CHANNEL WHERE I CANT SEND SHIT BRUHHHHHH**')
            else:
                try:
                    await ctx.send('<@356456393491873795> id call you an idiot but something terribly went wrong here and idk what it is')
                except:
                    await ctx.author.send('i cant send shit in that channel lol you fucking idiot')
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @commands.command()
    async def music_version(self,ctx):
        return await ctx.send('This bot has Nevira Music installed. Running on version 3.1.0 (Lavalink REST)\nWarning: REST API support is still experimental. Don\'t expect this to work flawlessly.')

    @commands.command(aliases=['music_now','music_nowplaying','music_np'])
    async def music_queue(self, ctx):
        import math
        ButtonStyle = discord.ButtonStyle
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        try:
            rainbow = rainbows['%s' % ctx.guild.id]
        except:
            rainbow = False
        seconds = player.position / 1000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        h = int(h)
        m = int(m)
        s = math.floor(s)
        def bars(num,rainbow=False):
            num = num / 5
            num = int(num)
            string = ''
            for x in range(num):
                if rainbow:
                    if x==0 or x==18:
                        string = '%s[0;31m' % string
                    elif x==3:
                        string = '%s[0;33m' % string
                    elif x==6:
                        string = '%s[0;32m' % string
                    elif x==9:
                        string = '%s[0;36m' % string
                    elif x==12:
                        string = '%s[0;34m' % string
                    elif x==15:
                        string = '%s[0;35m' % string
                string = '%s|' % string
            num = 20 - num
            for x in range(num):
                string = '%s ' % string
            string = '%s[0m' % string
            return string
        total = player.current.duration / 1000
        percent = seconds / total * 100
        if s < 10:
            s = f'0{s}'
        if h==0:
            trackpos = f'{m}:{s}'
        else:
            trackpos = f'{h}:{m}:{s}'
        m2, s2 = divmod(total, 60)
        h2, m2 = divmod(m2, 60)
        h2 = int(h2)
        m2 = int(m2)
        s2 = math.floor(s2)
        if s2 < 10:
            s2 = f'0{s2}'
        if h2==0:
            totalpos = f'{m2}:{s2}'
        else:
            totalpos = f'{h2}:{m2}:{s2}'
            if m2 < 10:
                totalpos = f'{h2}:0{m2}:{s2}'
        try:
            track_title = ''
            for char in player.current['title']:
                if len(player.current['title'])<=255:
                    track_title = player.current['title']
                    break
                temptext = track_title + char
                if len(temptext)==252:
                    if char==' ':
                        track_title = track_title + '...'
                        break
                    track_title = temptext + '...'
                    break
                track_title = temptext
            if player.current['stream']:
                trackpos = '• LIVE'
                totalpos = ''
                percent = 100
            if player.paused:
                embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xd9d9d9)
            else:
                embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xb5eeff)
        except:
            embed = discord.Embed(title='Music control',description='```0:00 [                    ] 0:00```',color=0xd9d9d9)
        text = ''
        key = 1
        for track in player.queue:
            if key==1:
                remaining = total - seconds
            else:
                remaining += player.queue[key-1]['duration']/1000
            m2, s2 = divmod(remaining, 60)
            h2, m2 = divmod(m2, 60)
            h2 = int(h2)
            m2 = int(m2)
            s2 = math.floor(s2)
            if s2 < 10:
                s2 = f'0{s2}'
            if h2==0:
                totalpos = f'{m2}:{s2}'
            else:
                totalpos = f'{h2}:{m2}:{s2}'
                if m2 < 10:
                    totalpos = f'{h2}:0{m2}:{s2}'
            if text=='':
                if len(player.queue)==1:
                    text = track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~')
                else:
                    text = '`{0}.` {1} (in `{2}`)'.format(key,track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),totalpos)
            else:
                text = '{0}\n\n`{1}.` {2} (in `{3}`)'.format(text,key,track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),totalpos)
            key = key + 1
            if key==11:
                text = f'{text}\n\n({len(player.queue)-10} more track(s) in queue)'
                break
        if text=='':
            embed.add_field(name='Up next',value='Nothing',inline=False)
        else:
            embed.add_field(name='Up next',value=text,inline=False)
        canmodify = True
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    canmodify = False
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    canmodify = False
        if canmodify:
            lst = []
            if player.paused:
                if player.current['stream']:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay',disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind',disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause'))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward',disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay'))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind'))
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause'))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward'))
                if len(player.queue)==0:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip', disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip'))
            else:
                if player.current['stream']:
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay',disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind',disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause',disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward',disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay'))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind'))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause'))
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward'))
                if len(player.queue)==0:
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip', disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip'))
            if player.loop==1:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F502", custom_id='loop'))
            elif player.loop==2:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F501", custom_id='loop'))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F501", custom_id='loop'))
            if player.volume==0:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown', disabled=True))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown'))
            lst.append(discord.ui.Button(style=ButtonStyle.red, emoji="\U000023F9", custom_id='stop'))
            if player.volume==200:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup', disabled=True))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup'))
            if player.shuffle:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F500", custom_id='shuffle'))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F500", custom_id='shuffle'))
            effect8d = player.get_filter(lavalink.filters.Rotation)
            effecteq = player.get_filter(lavalink.filters.Equalizer)
            effectspatial = player.get_filter(lavalink.filters.Echo)
            if effectspatial==None:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F3A7", custom_id='usespatial'))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F3A7", custom_id='usespatial'))
            if effect8d==None:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000027BF", custom_id='use8d'))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000027BF", custom_id='use8d'))
            if effecteq==None:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F4F6", custom_id='useeq', disabled=True))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F4F6", custom_id='useeq'))
            if rainbow:
                lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U00002753", custom_id='rainbow'))
            else:
                lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U00002753", custom_id='rainbow'))
            btns = discord.ui.ActionRow(lst[0],lst[1],lst[2],lst[3],lst[4])
            btns2 = discord.ui.ActionRow(lst[5],lst[6],lst[7],lst[8],lst[9])
            btns3 = discord.ui.ActionRow(lst[10],lst[11],lst[12],lst[13])
            action_row = discord.ui.MessageComponents(btns,btns2,btns3)
            msg = await ctx.send(embed=await applytheme(ctx.author.id,embed),components=action_row)
            import asyncio
            while True:
                def check(interaction):
                    return interaction.user.id==ctx.author.id and interaction.message.id==msg.id
                try:
                    interaction = await self.bot.wait_for("component_interaction", check=check, timeout=30.0)
                    if not player.is_playing or not ctx.author.voice or not ctx.author.voice.channel:
                        raise ValueError()
                    else:
                        if int(player.channel_id) != ctx.author.voice.channel.id:
                            raise ValueError()
                except:
                    lst = []
                    if player.paused:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind', disabled=True))
                        if player.paused:
                            lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause', disabled=True))
                        else:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind', disabled=True))
                        if player.paused:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000025B6", custom_id='pause', disabled=True))
                        else:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip', disabled=True))
                    if player.loop==1:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F502", custom_id='loop', disabled=True))
                    elif player.loop==2:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F501", custom_id='loop', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F501", custom_id='loop', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.red, emoji="\U000023F9", custom_id='stop', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup', disabled=True))
                    if player.shuffle:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F500", custom_id='shuffle',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F500", custom_id='shuffle',disabled=True))
                    effect8d = player.get_filter(lavalink.filters.Rotation)
                    effecteq = player.get_filter(lavalink.filters.Equalizer)
                    effectspatial = player.get_filter(lavalink.filters.Echo)
                    if effectspatial==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F3A7", custom_id='usespatial',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F3A7", custom_id='usespatial',disabled=True))
                    if effect8d==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000027BF", custom_id='use8d',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000027BF", custom_id='use8d',disabled=True))
                    if effecteq==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F4F6", custom_id='useeq', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F4F6", custom_id='useeq',disabled=True))
                    if rainbow:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U00002753", custom_id='rainbow',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U00002753", custom_id='rainbow',disabled=True))
                    btns = discord.ui.ActionRow(lst[0],lst[1],lst[2],lst[3],lst[4])
                    btns2 = discord.ui.ActionRow(lst[5],lst[6],lst[7],lst[8],lst[9])
                    btns3 = discord.ui.ActionRow(lst[10],lst[11],lst[12],lst[13])
                    action_row = discord.ui.MessageComponents(btns,btns2,btns3)
                    try:
                        return await interaction.response.edit_message(embed=await applytheme(ctx.author.id,embed),components=action_row)
                    except:
                        return await msg.edit(embed=await applytheme(ctx.author.id,embed),components=action_row)
                if not interaction.component.custom_id=='stop':
                    track_title = ''
                    for char in player.current['title']:
                        if len(player.current['title'])<=255:
                            track_title = player.current['title']
                            break
                        temptext = track_title + char
                        if len(temptext)==252:
                            if char==' ':
                                track_title = track_title + '...'
                                break
                            track_title = temptext + '...'
                            break
                        track_title = temptext
                    seconds = player.position / 1000
                    percent = seconds / total * 100
                    if player.current['stream']:
                        trackpos = '• LIVE'
                        totalpos = ''
                        percent = 100
                    if player.paused:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xd9d9d9)
                    else:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xb5eeff)
                if interaction.component.custom_id=='replay':
                    await player.seek(0)
                    embed.set_footer(text='Replaying track')
                elif interaction.component.custom_id=='rewind':
                    currentpos = player.position / 1000
                    if currentpos < 10:
                        await player.seek(0)
                    else:
                        await player.seek(round((currentpos - 10)*1000))
                    embed.set_footer(text='Rewinding 10 seconds')
                elif interaction.component.custom_id=='pause':
                    track_title = ''
                    for char in player.current['title']:
                        if len(player.current['title'])<=255:
                            track_title = player.current['title']
                            break
                        temptext = track_title + char
                        if len(temptext)==252:
                            if char==' ':
                                track_title = track_title + '...'
                                break
                            track_title = temptext + '...'
                            break
                        track_title = temptext
                    if not player.paused:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xd9d9d9)
                    else:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```',color=0xb5eeff)
                    if player.paused:
                        await player.set_pause(pause=False)
                        embed.set_footer(text='Resumed')
                    else:
                        await player.set_pause(pause=True)
                        embed.set_footer(text='Paused')
                elif interaction.component.custom_id=='fastforward':
                    currentpos = player.position / 1000
                    totalpos = player.current.duration / 1000
                    if currentpos + 10 > totalpos:
                        if not len(player.queue)==0:
                            await player.skip()
                    else:
                        await player.seek(round((currentpos + 10)*1000))
                    embed.set_footer(text='Fast forwarding 10 seconds')
                elif interaction.component.custom_id=='skip':
                    track_title = ''
                    for char in player.queue[0]['title']:
                        if len(player.queue[0]['title'])<=255:
                            track_title = player.queue[0]['title']
                            break
                        temptext = track_title + char
                        if len(temptext)==252:
                            if char==' ':
                                track_title = track_title + '...'
                                break
                            track_title = temptext + '...'
                            break
                        track_title = temptext
                    total = player.queue[0].duration / 1000
                    m2, s2 = divmod(total, 60)
                    h2, m2 = divmod(m2, 60)
                    h2 = int(h2)
                    m2 = int(m2)
                    s2 = math.floor(s2)
                    if s2 < 10:
                        s2 = f'0{s2}'
                    if h2==0:
                        totalpos = f'{m2}:{s2}'
                    else:
                        totalpos = f'{h2}:{m2}:{s2}'
                    if player.paused:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n0:00 [                    ] {totalpos}```',color=0xd9d9d9)
                    else:
                        embed = discord.Embed(title=track_title.replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),description=f'```ansi\n0:00 [                    ] {totalpos}```',color=0xb5eeff)
                    await player.skip()
                    embed.set_footer(text='Skipped')
                elif interaction.component.custom_id=='loop':
                    if player.loop==0:
                        player.set_loop(1)
                        embed.set_footer(text='Looping current track')
                    elif player.loop==1:
                        player.set_loop(2)
                        embed.set_footer(text='Looping queue')
                    else:
                        player.set_repeat(False)
                        embed.set_footer(text='Looping off')
                elif interaction.component.custom_id=='voldown':
                    if player.volume < 10:
                        await player.set_volume(0)
                        embed.set_footer(text='Muted')
                    else:
                        await player.set_volume(player.volume-10)
                        embed.set_footer(text='Volume 10% decreased')
                elif interaction.component.custom_id=='stop':
                    try:
                        player.queue.clear()
                    except:
                        pass
                    # Stop the current track so Lavalink consumes less resources.
                    await player.stop()
                    # Disconnect from the voice channel.
                    await ctx.guild.voice_client.disconnect(force=True)
                    lst = []
                    if player.paused:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind', disabled=True))
                        if player.paused:
                            lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause', disabled=True))
                        else:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind', disabled=True))
                        if player.paused:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000025B6", custom_id='pause', disabled=True))
                        else:
                            lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward', disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip', disabled=True))
                    if player.loop==1:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F502", custom_id='loop', disabled=True))
                    elif player.loop==2:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F501", custom_id='loop', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F501", custom_id='loop', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.red, emoji="\U000023F9", custom_id='stop', disabled=True))
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup', disabled=True))
                    if player.shuffle:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F500", custom_id='shuffle', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F500", custom_id='shuffle', disabled=True))
                    effect8d = None
                    effecteq = None
                    effectspatial = None
                    if effectspatial==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F3A7", custom_id='usespatial',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F3A7", custom_id='usespatial',disabled=True))
                    if effect8d==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000027BF", custom_id='use8d',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000027BF", custom_id='use8d',disabled=True))
                    if effecteq==None:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F4F6", custom_id='useeq', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F4F6", custom_id='useeq',disabled=True))
                    if rainbow:
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U00002753", custom_id='rainbow',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U00002753", custom_id='rainbow',disabled=True))
                    btns = discord.ui.ActionRow(lst[0],lst[1],lst[2],lst[3],lst[4])
                    btns2 = discord.ui.ActionRow(lst[5],lst[6],lst[7],lst[8],lst[9])
                    btns3 = discord.ui.ActionRow(lst[10],lst[11],lst[12],lst[13])
                    action_row = discord.ui.MessageComponents(btns,btns2,btns3)
                    return await interaction.response.edit_message(embed=await applytheme(ctx.author.id,embed),components=action_row)
                elif interaction.component.custom_id=='volup':
                    if player.volume > 190:
                        await player.set_volume(200)
                        embed.set_footer(text='Max volume set (200%)')
                    else:
                        await player.set_volume(player.volume+10)
                        embed.set_footer(text='Volume 10% increased')
                elif interaction.component.custom_id=='shuffle':
                    if player.shuffle==False:
                        player.shuffle = True
                        embed.set_footer(text='Shuffle on')
                    elif player.shuffle==True:
                        player.shuffle = False
                        embed.set_footer(text='Shuffle off')
                elif interaction.component.custom_id=='usespatial':
                    effectspatial = player.get_filter(lavalink.filters.Echo)
                    if effectspatial==None:
                        echo = lavalink.filters.Echo()
                        echo.update(delay=0.05,decay=0.3)
                        await player.set_filter(echo)
                        embed.set_footer(text='Spatial Audio on')
                    else:
                        await player.remove_filter(lavalink.filters.Echo)
                        embed.set_footer(text='Spatial Audio off')
                elif interaction.component.custom_id=='use8d':
                    effect8d = player.get_filter(lavalink.filters.Rotation)
                    if effect8d==None:
                        rotation = lavalink.filters.Rotation()
                        rotation.update(rotationHz=0.1)
                        await player.set_filter(rotation)
                        embed.set_footer(text='8D Audio on')
                    else:
                        await player.remove_filter(lavalink.filters.Rotation)
                        embed.set_footer(text='8D Audio off')
                elif interaction.component.custom_id=='useeq':
                    await player.remove_filter(lavalink.filters.Equalizer)
                    embed.set_footer(text='EQ off')
                elif interaction.component.custom_id=='rainbow':
                    if rainbow:
                        rainbow = False
                        embed.description = f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```'
                        rainbows.update({'%s' % ctx.guild.id: False})
                        embed.set_footer(text='\U00002601')
                    else:
                        rainbow = True
                        embed.description = f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```'
                        rainbows.update({'%s' % ctx.guild.id: True})
                        embed.set_footer(text='\U0001F308')
                if interaction.component.custom_id=='skip':
                    seconds = 0
                else:
                    seconds = player.position / 1000
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                h = int(h)
                m = int(m)
                s = math.floor(s)
                total = player.current.duration / 1000
                percent = seconds / total * 100
                if s < 10:
                    s = f'0{s}'
                if h==0:
                    trackpos = f'{m}:{s}'
                else:
                    trackpos = f'{h}:{m}:{s}'
                if player.current['stream']:
                    trackpos = '• LIVE'
                    totalpos = ''
                percent = 100
                m2, s2 = divmod(total, 60)
                h2, m2 = divmod(m2, 60)
                h2 = int(h2)
                m2 = int(m2)
                s2 = math.floor(s2)
                if s2 < 10:
                    s2 = f'0{s2}'
                if h2==0:
                    totalpos = f'{m2}:{s2}'
                else:
                    totalpos = f'{h2}:{m2}:{s2}'
                text = ''
                key = 1
                for track in player.queue:
                    if key==1:
                        remaining = total - seconds
                    else:
                        remaining += player.queue[key-1]['duration']/1000
                    m2, s2 = divmod(remaining, 60)
                    h2, m2 = divmod(m2, 60)
                    h2 = int(h2)
                    m2 = int(m2)
                    s2 = math.floor(s2)
                    if s2 < 10:
                        s2 = f'0{s2}'
                    if h2==0:
                        totalpos = f'{m2}:{s2}'
                    else:
                        totalpos = f'{h2}:{m2}:{s2}'
                        if m2 < 10:
                            totalpos = f'{h2}:0{m2}:{s2}'
                    if text=='':
                        if len(player.queue)==1:
                            text = track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~')
                        else:
                            text = '`{0}.` {1} (in `{2}`)'.format(key,track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),totalpos)
                    else:
                        text = '{0}\n\n`{1}.` {2} (in `{3}`)'.format(text,key,track['title'].replace('_','\_').replace('*','\*').replace(':','\:').replace('`','\`').replace('~','\~'),totalpos)
                    key = key + 1
                    if key==11:
                        text = f'{text}\n\n({len(player.queue)-10} more track(s) in queue)'
                        break
                if text=='':
                    embed.add_field(name='Up next',value='Nothing',inline=False)
                else:
                    embed.add_field(name='Up next',value=text,inline=False)
                lst = []
                if player.paused:
                    if player.current['stream']:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay',disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind',disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause'))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EE", custom_id='replay'))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023EA", custom_id='rewind'))
                        lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000025B6", custom_id='pause'))
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023E9", custom_id='fastforward'))
                    if len(player.queue)==0:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000023ED", custom_id='skip'))
                else:
                    if player.current['stream']:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay',disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind',disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause',disabled=True))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward',disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EE", custom_id='replay'))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023EA", custom_id='rewind'))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023F8", custom_id='pause'))
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023E9", custom_id='fastforward'))
                    if len(player.queue)==0:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip', disabled=True))
                    else:
                        lst.append(discord.ui.Button(style=ButtonStyle.blurple, emoji="\U000023ED", custom_id='skip'))
                if player.loop==1:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F502", custom_id='loop'))
                elif player.loop==2:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F501", custom_id='loop'))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F501", custom_id='loop'))
                if player.volume==0:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown', disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F509", custom_id='voldown'))
                lst.append(discord.ui.Button(style=ButtonStyle.red, emoji="\U000023F9", custom_id='stop'))
                if player.volume==200:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup', disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F50A", custom_id='volup'))
                if player.shuffle:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F500", custom_id='shuffle'))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F500", custom_id='shuffle'))
                effect8d = player.get_filter(lavalink.filters.Rotation)
                effecteq = player.get_filter(lavalink.filters.Equalizer)
                effectspatial = player.get_filter(lavalink.filters.Echo)
                if effectspatial==None:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F3A7", custom_id='usespatial'))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F3A7", custom_id='usespatial'))
                if effect8d==None:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U000027BF", custom_id='use8d'))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U000027BF", custom_id='use8d'))
                if effecteq==None:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U0001F4F6", custom_id='useeq', disabled=True))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U0001F4F6", custom_id='useeq'))
                if rainbow:
                    lst.append(discord.ui.Button(style=ButtonStyle.green, emoji="\U00002753", custom_id='rainbow'))
                else:
                    lst.append(discord.ui.Button(style=ButtonStyle.grey, emoji="\U00002753", custom_id='rainbow'))
                btns = discord.ui.ActionRow(lst[0],lst[1],lst[2],lst[3],lst[4])
                btns2 = discord.ui.ActionRow(lst[5],lst[6],lst[7],lst[8],lst[9])
                btns3 = discord.ui.ActionRow(lst[10],lst[11],lst[12],lst[13])
                action_row = discord.ui.MessageComponents(btns,btns2,btns3)
                seconds = player.position / 1000
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                h = int(h)
                m = int(m)
                s = math.floor(s)
                total = player.current.duration / 1000
                percent = seconds / total * 100
                if s < 10:
                    s = f'0{s}'
                if h==0:
                    trackpos = f'{m}:{s}'
                else:
                    trackpos = f'{h}:{m}:{s}'
                if player.current['stream']:
                    trackpos = '• LIVE'
                    totalpos = ''
                if player.current['stream']:
                    trackpos = '• LIVE'
                    totalpos = ''
                    percent = 100
                embed.description = f'```ansi\n{trackpos} [{bars(percent,rainbow)}] {totalpos}```'
                await interaction.response.edit_message(embed=await applytheme(ctx.author.id,embed),components=action_row)
        else:
            await ctx.send(embed=await applytheme(ctx.author.id,embed))

    @commands.command(aliases=['music_repeat'])
    async def music_loop(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.is_connected:
            return await ctx.send('**OOPS**: I\'m not in a voice channel. :x:')
        if player.loop==0:
            player.set_loop(1)
            return await ctx.send('**SUCCESS**: Looping current track. :white_check_mark:')
        elif player.loop==1:
            player.set_loop(2)
            return await ctx.send('**SUCCESS**: Looping queue. :white_check_mark:')
        else:
            player.set_loop(0)
            return await ctx.send('**SUCCESS**: Looping is now off. :white_check_mark:')
    
    @commands.command()
    async def music_eq(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if ctx.message.content.startswith('nv!'):
            value = ctx.message.content.replace('nv!music_eq ','')
        elif ctx.message.content.startswith('nt!'):
            value = ctx.message.content.replace('nt!music_eq ','')
        else:
            value = ctx.message.content.replace('.music_eq ','')
        hz = ['25  ','40  ','63  ','100 ','160 ','250 ','400 ','630 ','1k  ','1.6k','2.5k','4k  ','6.3k','10k ','16k ']
        equ = player.get_filter(lavalink.filters.Equalizer)
        if equ==None:
            equ = lavalink.filters.Equalizer()
        if value=='' or value=='nv!music_eq' or value=='nt!music_eq':
            eqlist = equ.values
            def bars(num):
                num = num / 5
                num = int(num)
                string = ''
                for x in range(num):
                    string = '%s|' % string
                num = 20 - num
                for x in range(num):
                    string = '%s ' % string
                return string
            txt = ''
            index = 0
            for eq in eqlist:
                toadd = eq + 1
                ogeq = eq
                eq = toadd * 50
                bar = bars(eq)
                if ogeq == 0:
                    strindex = f'  {index}'
                elif ogeq < 0:
                    strindex = f'- {index}'
                elif ogeq > 0:
                    strindex = f'+ {index}'
                if txt=='':
                    txt = '```diff\n  BD Freq GN Bar               GN\n{0}  {1} {2} {3}'.format(strindex,hz[index],bar,ogeq)
                else:
                    if len('%s' % index)==1:
                        txt = '{0}\n{1}  {2} {3} {4}'.format(txt,strindex,hz[index],bar,ogeq)
                    else:
                        txt = '{0}\n{1} {2} {3} {4}'.format(txt,strindex,hz[index],bar,ogeq)
                index = index + 1
            embed = discord.Embed(title='Equaliser',description=f'Music too bass boosted? Try lowering the user volume of Nevira first before changing these settings (90/95% recommended).\n{txt}```',color=0xb5eeff)
            return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if value=='reset':
            await player.remove_filter(lavalink.filters.Equalizer)
            return await ctx.send('**SUCCESS**: EQ reset. :white_check_mark:')
        for word in value.split():
            try:
                band = int(word)
            except:
                return await ctx.send('**OOPS**: Missing or invalid parameter: `<band>`. :x:')
            try:
                gain = value.replace('%s ' % band,'')
                gain = float(gain)
            except:
                return await ctx.send('**OOPS**: Invalid parameter: `<gain>`. :x:')
            break
        equ.update(bands=[(band, gain)])
        await player.set_filter(equ)
        return await ctx.send('**SUCCESS**: Set gain for band {0} to {1}. :white_check_mark:'.format(band,gain))

    @commands.command()
    async def music_volume(self, ctx, *, volume):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        try:
            volume = int(volume)
        except:
            return await ctx.send('**OOPS**: Invalid parameter: `<value>`. :x:')
        if volume > 200:
            return await ctx.send('**OOPS**: 200% is the maximum volume, as anything above may cause ear damage. :x:')
        await player.set_volume(volume)
        return await ctx.send('**SUCCESS**: Set volume to {0}%. :white_check_mark:'.format(volume))
    
    @commands.command()
    async def music_play(self, ctx, *, query=''):
        """ Searches and plays a song from a given query. """
        soundcloud = False
        url = False
        source = 0
        ensureplay = False

        # christmas update (reverted)
        # query = 'https://www.youtube.com/watch?v=7FMOj8VmWT4'

        if query=='' or query=='-ensure-play':
            try:
                toplay = ctx.message.attachments[0]
            except:
                return await ctx.send('You must either attach a file or give me a `<query>` to look up.')
            if not 'audio' in toplay.content_type and not 'video' in toplay.content_type:
                return await ctx.send('This doesn\'t seem like a valid audio file.')
            if query=='-ensure-play':
                ensureplay = True
            query = '-url %s' % toplay.url

        if query.startswith('-ensure-play'):
            ensureplay = True
            query = query.replace('-ensure-play ','',1)
            if query=='-ensure-play' or query=='' or query==' ':
                return await ctx.send('**OOPS**: Missing parameter: `<query>`. :x:')

        if query.startswith('-sc'):
            source = 1
            query = query.replace('-sc ','',1)
            if query=='-sc' or query=='' or query==' ':
                return await ctx.send('**OOPS**: Missing parameter: `<query>`. :x:')

        if query.startswith('-url'):
            source = 2
            query = query.replace('-url ','',1)
            if query=='-url' or query=='' or query==' ':
                return await ctx.send('**OOPS**: Missing parameter: `<query>`. :x:')
        
        try:
            await ctx.message.add_reaction('<a:loading0:697470120246902806>')
        except:
            pass
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            if source==1:
                soundcloud = True
                query = f'scsearch:{query}'
            elif source==2:
                url = True
                query = f'urlsearch:{query}'
            else:
                query = f'ytsearch:{query}'

        if source==2:
            url = True

        # Get the results for the query from Lavalink.
        try:
            results = await player.node.get_tracks(query)
        except:
            #traceback.print_exc()
            await ctx.guild.voice_client.disconnect(force=True)
            return await ctx.send('Something went wrong while searching. Please try again, it should usually work the second time. Otherwise, contact Green.')
            

        if not results or not results['tracks']:
            try:
                await ctx.message.remove_reaction('<a:loading0:697470120246902806>',discord.Object(id=self.bot.user.id))
                await ctx.message.add_reaction(':x:')
            except:
                pass
            if not player.is_playing and not player.paused:
                await ctx.guild.voice_client.disconnect(force=True)
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        embed = discord.Embed(color=0xb5eeff)

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        try:
            await ctx.message.remove_reaction('<a:loading0:697470120246902806>',discord.Object(id=self.bot.user.id))
        except:
            pass
        if results['loadType'] == 'PLAYLIST_LOADED':
            try:
                await ctx.message.add_reaction(':white_check_mark:')
            except:
                pass
            tracks = results['tracks']

            num = 0
            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = 'Playlist Enqueued'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks are now queued.'
        elif results['loadType'] == 'LOAD_FAILED':
            try:
                await ctx.message.add_reaction(':x:')
            except:
                pass
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            try:
                await ctx.message.add_reaction(':white_check_mark:')
            except:
                pass
            track = results['tracks'][0]
            if not url:
                if not 'soundcloud.com' in track["info"]["uri"]:
                    if url:
                        embed.title = 'Track Enqueued from file/URL'
                    else:
                        embed.title = 'Track Enqueued from YouTube'
                else:
                    if soundcloud:
                        embed.title = 'Track Enqueued from SoundCloud'
                    else:
                        if url:
                            embed.title = 'Track Enqueued from file/URL'
                        else:
                            embed.title = 'Track Enqueued from YouTube'
            else:
                embed.title = 'Track Enqueued from file/URL'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]}) is now queued.'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            player.add(requester=ctx.author.id, track=track)

        if not player.is_playing:
            embed.title = embed.title.replace('Track Enqueued','Now playing',1)

        # christmas update (reverted)
        # embed.title = 'merry christler'

        if player.paused:
            await ctx.send('**Reminder**: Your music player is paused. Run `nv!music_resume` to resume playback.',embed=await applytheme(ctx.author.id,embed))
        else:
            await ctx.send(embed=await applytheme(ctx.author.id,embed))
        
        if not player.is_playing:
            try:
                await player.play()
            except Exception as e:
                await ctx.guild.voice_client.disconnect(force=True)
                if isinstance(e, lavalink.errors.RequestError):
                    return await ctx.send('Something went wrong with the node. Please try again.')
                else:
                    raise
            if ensureplay:
                await player.change_node(player.node)

    @commands.command()
    async def music_setnode(self, ctx, *, node):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        nodemgr = self.bot.lavalink.node_manager
        if node=='auto':
            region = ctx.author.voice.channel.rtc_region
            if type(region) is None:
                region = ctx.guild.region
            touse_nd = nodemgr.find_ideal_node(str(region))
        else:
            bypass = False
            if node.startswith('bypass-'):
                bypass = True
                node = node.replace('bypass-','',1)
            node = int(node)
            #if node==1 and not bypass:
                #return await ctx.send('**Warning: Moegiiro is not fully functional!**\nSongs may not play from some sources. Consider using Natsumi and Koharu instead.\nYou can connect to Moegiiro anyway by typing `bypass-1`.')
            index = 0
            touse_nd = 0
            for regnode in lavalink_nodes:
                if node==index:
                    if not regnode['enable']:
                        return await ctx.send('This node is disabled. Please use a different node.')
                    for nd in nodemgr.nodes:
                        if nd.name==regnode['name']:
                            touse_nd = nd
                            break
                    break
                index += 1
            if touse_nd==0:
                return await ctx.send('This doesn\'t seem to be a node ID. Make sure that the node actually exists.')
            try:
                lat = await touse_nd.get_rest_latency()
                if lat==-1:
                    raise ValueError()
            except:
                return await ctx.send('This node seems to be down. Try a different node closest to your region.')
            if not touse_nd.name in self.bot.nodesready:
                return await ctx.send('This node is not ready yet. Try again soon.')
        try:
            current = tracks[f'{ctx.guild.id}']
        except:
            current = copy.deepcopy(player.current)
        pause = player.paused
        queue = player.queue.copy()
        loop = copy.deepcopy(player.loop)
        shuffle = copy.deepcopy(player.shuffle)
        volume = copy.deepcopy(player.volume)
        pos = copy.deepcopy(player.position)
        if not ctx.guild.id in self.bot.nodeswitch:
            self.bot.nodeswitch.append(ctx.guild.id)
        msg = await ctx.send(content='Changing node...')
        await player.stop()
        await player.change_node(touse_nd)
        await msg.edit(content='Node changed, copying over player data...')
        if player.current==None and not current==None:
            if current.stream:
                await player.play(current)
            else:
                await player.play(current,pause=pause,start_time=pos)
        if len(queue) > 0 and len(player.queue)==0:
            for item in queue:
                await player.add(item)
        player.set_loop(loop)
        player.set_shuffle(shuffle)
        await player.set_volume(volume)
        self.bot.nodeswitch.remove(ctx.guild.id)
        await msg.edit(content=f'Node changed successfully!\nNode: {lavalink_nodes[node]["name"]} (`{lavalink_nodes[node]["id"]}`)')

    @commands.command()
    async def music_rickroll(self, ctx):
        """Rickrolls everyone in the voice channel."""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Let\'s not be an asshole and rickroll people already listening to music, ok?')

        num = random.randint(1,10)
        if num==1:
            query = 'https://www.youtube.com/watch?v=yKQ_sQKBASM'
        else:
            query = 'never gonna give you up'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        if num==1:
            await ctx.send('Now rickrolling...?')
        else:
            await ctx.send('Now rickrolling <a:rickroll:798130995248496710>')

    @commands.command()
    async def music_fart(self, ctx):
        """uh oh someone FARDED!!!1"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Let\'s not interrupt the listening session right now, ok?')
        
        queries = ['https://pixels.onl/audio/fart1.mp3','https://pixels.onl/audio/fart2.mp3','https://pixels.onl/audio/fart3.mp3','https://pixels.onl/audio/fart4.mp3']
        import random
        query = random.choice(queries)

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':dash:')

    @commands.command()
    async def music_icecream(self, ctx):
        """BING CHILLING"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('ice cream store isn\'t open when music is playing')
        
        query = 'https://pixels.onl/audio/bingchilling.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':icecream:')

    @commands.command()
    async def music_lofi(self, ctx):
        """relaxation.mp3"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Music is already playing!')
        
        query = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':icecream:')

    @commands.command()
    async def music_cringebomb(self, ctx):
        """bomb has been planted"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('something is already playing, can\'t drop a bomb here')
        
        queries = ['https://pixels.onl/audio/cringe.mp3','https://pixels.onl/audio/cringe_lego.mp3']
        import random
        query = random.randint(1,10)
        if query==1:
            query = queries[1]
        else:
            query = queries[0]

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send('mine has been planted')

    @commands.command()
    async def music_bruh(self, ctx):
        """bRUH"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Let\'s not interrupt the listening session right now, ok?')
        
        query = 'https://pixels.onl/audio/bruh.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':moyai:')

    @commands.command()
    async def music_spooky(self, ctx):
        """bRUH"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('no spooky month until music ends')
        
        query = 'https://pixels.onl/audio/spooky.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':jack_o_lantern:')

    @commands.command()
    async def music_sus(self, ctx):
        """OMG AMONG US!!!1"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('**Nobody was ejected. (Skipped)**\nTry again when nothing\'s playing.')
        
        query = 'https://pixels.onl/audio/sus.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':knife:')

    @commands.command()
    async def music_laugh(self, ctx):
        """LMAOOOOOOO"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('LOOK AT THE TOP OF THIS QUEUE')
        
        query = 'https://pixels.onl/audio/laugh.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':joy:')

    @commands.command()
    async def music_wikipedia(self, ctx):
        """totally normal wikipedia"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Not the right time for Wikipedia, stuff\'s playing right now!')
        
        query = 'https://pixels.onl/audio/cbt.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send(':book:')

    @commands.command()
    async def music_nut(self, ctx):
        """NUT"""
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.is_playing:
            return await ctx.send('Can\'t nut in a music party.')
        
        query = 'https://pixels.onl/audio/nut.mp3'

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('**OOPS**: I couldn\'t find anything. :x:')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        lines = ''
        if results['loadType'] == 'LOAD_FAILED':
            return await ctx.send('**OOPS**: An error occurred while loading. :x:')
        else:
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
        
        if not player.is_playing:
            await player.play()

        await ctx.send('nut')

    @commands.command()
    async def music_pause(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if player.paused:
            return await ctx.send('**OOPS**: Music already paused. :x:')
        elif not player.is_playing:
            return await ctx.send('**OOPS**: Nothing is playing. :x:')
        else:
            if player.current['stream']:
                return await ctx.send('**OOPS**: Can\'t pause a stream! :x:')
            await player.set_pause(pause=True)
            return await ctx.send('**SUCCESS**: Paused music. :white_check_mark:')

    @commands.command()
    async def music_resume(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.paused:
            return await ctx.send('**OOPS**: Music is already playing. :x:')
        elif not player.is_playing:
            return await ctx.send('**OOPS**: Nothing is playing. :x:')
        else:
            await player.set_pause(pause=False)
            return await ctx.send('**SUCCESS**: Resumed music. :white_check_mark:')

    @commands.command()
    async def music_skip(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing and not player.queue==[]:
            if len(ctx.author.voice.channel.members)<=3:
                await player.skip()
                try:
                    del activity['%s_skip' % ctx.guild.id]
                except:
                    pass
                return await ctx.send('**SUCCESS**: Skipped track. :white_check_mark:')
            else:
                try:
                    role = discord.utils.get(ctx.guild.roles, name='DJ')
                    if role in ctx.author.roles:
                        await player.skip()
                        try:
                            del activity['%s_skip' % ctx.guild.id]
                        except:
                            pass
                        return await ctx.send('**SUCCESS**: Skipped track. :white_check_mark:')
                except:
                    pass
                if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    await player.skip()
                    try:
                        del activity['%s_skip' % ctx.guild.id]
                    except:
                        pass
                    return await ctx.send('**SUCCESS**: Skipped track. :white_check_mark:')
                try:
                    skip = activity['%s_skip' % ctx.guild.id]
                except:
                    skip = []
                try:
                    if ctx.author in skip:
                        return await ctx.send('**OOPS**: You already voted to skip! :x:')
                except:
                    skip = []
                count = len(skip)
                bots = -1
                for member in ctx.author.voice.channel.members:
                    if member.bot:
                        bots = bots + 1
                required = (len(ctx.author.voice.channel.members) - bots) / 2
                required = round(required)
                count = count + 1
                if count >= required:
                    await player.skip()
                    try:
                        del activity['%s_skip' % ctx.guild.id]
                    except:
                        pass
                    return await ctx.send('**SUCCESS**: Skipped track. :white_check_mark:')
                else:
                    skip.append(ctx.author)
                    await ctx.send('<@{0}> has voted to skip! `{1}/{2}`'.format(ctx.author.id,count,required))
                    return await update('%s_skip' % ctx.guild.id,skip)
        else:
            return await ctx.send('**OOPS**: Nothing is playing or the queue is empty. :x:')

    @commands.command()
    async def music_replay(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if player.is_playing:
            if player.current['stream']:
                return await ctx.send('**OOPS**: Can\'t replay a stream! :x:')
            
            return await ctx.send('**SUCCESS**: Replaying current track. :white_check_mark:')
        else:
            return await ctx.send('**OOPS**: Nothing is playing. :x:')

    @commands.command(aliases=['music_seek'])
    async def music_goto(self,ctx,*,timeframe):
        import math
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        tf = timeframe
        timeframe = timeframe.replace(':',' ',2)
        if player.is_playing:
            if player.current['stream']:
                return await ctx.send('**OOPS**: Can\'t seek in a stream! :x:')
            tf2 = timeframe.split()
            if len(tf2)==3:
                hours = tf2[0]
                minutes = tf2[1]
                seconds = tf2[2]
            elif len(tf2)==2:
                minutes = tf2[0]
                seconds = tf2[1]
            else:
                seconds = tf2[0]
            try:
                try:
                    hours = int(hours)
                except:
                    pass
                minutes = int(minutes)
                seconds = int(seconds)
            except:
                return await ctx.send('**OOPS**: Invalid parameter: `<timeframe>`. :x:')
            try:
                minutes = hours * 60 + minutes
            except:
                pass
            try:
                seconds = (minutes * 60 + seconds) * 1000
            except:
                pass
            await player.seek(seconds)
            m, s = divmod(seconds / 1000, 60)
            h, m = divmod(m, 60)
            h = int(h)
            m = int(m)
            s = math.floor(s)
            def bars(num):
                num = num / 5
                num = int(num)
                string = ''
                for x in range(num):
                    string = '%s|' % string
                num = 20 - num
                for x in range(num):
                    string = '%s ' % string
                return string
            total = player.current.duration / 1000
            percent = seconds / 1000 / total * 100
            if s < 10:
                s = f'0{s}'
            if h==0:
                trackpos = f'{m}:{s}'
            else:
                trackpos = f'{h}:{m}:{s}'
            m2, s2 = divmod(total, 60)
            h2, m2 = divmod(m2, 60)
            h2 = int(h2)
            m2 = int(m2)
            s2 = math.floor(s2)
            if s2 < 10:
                s2 = f'0{s2}'
            if h2==0:
                totalpos = f'{m2}:{s2}'
            else:
                totalpos = f'{h2}:{m2}:{s2}'
            return await ctx.send(f'**SUCCESS**: Going to `{tf}`. :white_check_mark:\n`[{bars(percent)}] {trackpos}/{totalpos}`')
        else:
            return await ctx.send('**OOPS**: Nothing is playing. :x:')

    @commands.command()
    async def music_shuffle(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.is_connected:
            return await ctx.send('**OOPS**: I\'m not in a voice channel. :x:')
        if player.shuffle==False:
            player.shuffle = True
            return await ctx.send('**SUCCESS**: Queue shuffling is now on. :white_check_mark:')
        elif player.shuffle==True:
            player.shuffle = False
            return await ctx.send('**SUCCESS**: Queue shuffling is now off. :white_check_mark:')

    @commands.command()
    async def music_reorder(self,ctx,pos: int,newpos: int):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.is_connected:
            return await ctx.send('**OOPS**: I\'m not in a voice channel. :x:')
        if newpos > len(player.queue)+1 or newpos < 1 or pos > len(player.queue) + 1 or pos < 1:
            return await ctx.send('**OOPS**: Invalid arguments given! :x:')
        if pos==newpos:
            return await ctx.send('**OOPS**: What\'s the point of reordering then? :x:')
        try:
            player.queue.insert(newpos-1, player.queue.pop(pos-1))
            return await ctx.send(f'**SUCCESS**: Moved `{player.queue[newpos-1]["title"]}` to position `{newpos}` in queue. :white_check_mark:')
        except:
            return await ctx.send('**OOPS**: Invalid arguments given! :x:')
    
    @commands.command()
    async def music_remove(self, ctx, *, pos):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if len(player.queue) > 0:
            if pos=='all':
                player.queue.clear()
                return await ctx.send('**SUCCESS**: Cleared queue. :white_check_mark:')
            pos = int(pos)
            try:
                track = player.queue.pop(pos-1)
            except:
                return await ctx.send('**OOPS**: Could not remove track. :x:')
            return await ctx.send('**SUCCESS**: Removed `%s` from the queue. :white_check_mark:' % track['title'])
        else:
            return await ctx.send('**OOPS**: Queue is empty. :x:')
        
    @commands.command(aliases=['music_dc','music_disconnect','music_fuckoff','music_stop'])
    async def music_leave(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('**OOPS**: Not connected. :x:')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send('**OOPS**: You\'re not in my voice channel! :x:')

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        try:
            player.queue.clear()
        except:
            pass
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.guild.voice_client.disconnect(force=True)
        await ctx.send('**SUCCESS**: Left the voice channel. :white_check_mark:')

        nodemgr = self.bot.lavalink.node_manager
        playing = 0
        for node in nodemgr.available_nodes:
            playing += node.stats.playing_players
        if playing==0:
            for node in nodemgr.nodes:
                nodemgr.remove_node(node)
            del self.bot.lavalink
            self.bot.unload_extension('cogs.music')
            self.bot.load_extension('cogs.music')
            log(type='BOT',status='info',content='Reloaded music cog due to inactivity to keep nodes connected')

    @commands.command()
    async def music_nodes(self,ctx):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        except:
            player = None
        nodemgr = self.bot.lavalink.node_manager
        nodes = nodemgr.nodes
        embed = discord.Embed(title=f'Music Nodes (Total: {len(lavalink_nodes)})',description=None,color=0xb5eeff)
        index = 0
        for regnode in lavalink_nodes:
            for node in nodes:
                if regnode['name']==node.name:
                    try:
                        if regnode['name']==player.node.name:
                            embed.description = f'You are connected to node {regnode["name"]} (`{regnode["id"]}`, ID: `{index}`)'
                            if regnode['type'] < 2:
                                # Performance node, add the zap emoji
                                embed.description = embed.description[:-1]+' :zap:)'
                    except:
                        pass
                    break
                
            avail = True
            try:
                lat = await node.get_rest_latency()
                if lat==-1 or not regnode['enable']:
                    raise ValueError()
            except:
                avail = False
            flag = ':globe_with_meridians:'
            if regnode['region']=='europe' or regnode['region']=='rotterdam':
                flag = ':flag_de:'
            elif regnode['region']=='uk':
                flag = ':flag_gb:'
            elif regnode['region'].startswith('us-'):
                flag = ':flag_us:'
            elif regnode['region']=='sydney':
                flag = ':flag_au:'
            extra = ''
            if regnode['type'] < 2:
                extra = ' :zap:'
            if regnode['type']==0:
                extra = extra + ':house:'
            if regnode['type']==3:
                extra = ':satellite:'
            emoji = ':white_check_mark:'
            stats = f'`{round(lat)}ms` | The node is running normally.'
            if avail and not regnode['name'] in self.bot.nodesready:
                emoji = ':warning:'
                stats = f'`{round(lat)}ms` | The node is starting up.'
            elif not avail:
                if not regnode['enable']:
                    emoji = ':grey_question:'
                    stats = 'The node is disabled.'
                else:
                    emoji = ':x:'
                    stats = 'The node is down and is unreachable.'
            embed.add_field(name=f'{emoji} | {regnode["name"]} ({flag} `{regnode["id"]}`, ID: `{index}`{extra})',value=stats,inline=False)
            index += 1
        if player==None:
            embed.description = 'You are not connected to a node! Play music to connect to one.'
        else:
            try:
                if not ctx.guild.me.voice.channel==ctx.author.voice.channel:
                    embed.description = 'You are not connected to a node! Play music to connect to one.'
            except:
                embed.description = 'You are not connected to a node! Play music to connect to one.'
        embed.description = embed.description + '\n\n:house: Primary node\n:zap: Performance node\n:satellite: Third-party node'
        await ctx.send(embed=await applytheme(ctx.author.id,embed))

    @commands.command()
    async def music_toggle(self,ctx,*,node):
        try:
            node = int(node)
        except:
            return await ctx.send('this aint a node dumbass')
        lavalink_nodes[node]['enable'] = not lavalink_nodes[node]['enable']
        await ctx.send('Toggled node status. This will reset back to default on next reload.')

    @commands.command()
    async def music_hardreload(self,ctx):
        if not ctx.author.id==356456393491873795:
            return
        nodemgr = self.bot.lavalink.node_manager
        for node in nodemgr.nodes:
            nodemgr.remove_node(node)
        del self.bot.lavalink
        self.bot.unload_extension('cogs.music')
        self.bot.load_extension('cogs.music')
        await ctx.send('Hardreloaded music extension')

    @commands.command()
    async def music_8d(self,ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.is_connected:
            return await ctx.send('**OOPS**: I\'m not in a voice channel. :x:')
        effect = player.get_filter(lavalink.filters.Rotation)
        if effect==None:
            isactive = False
        else:
            isactive = True
        if isactive==False:
            rotation = lavalink.filters.Rotation()
            rotation.update(rotationHz=0.1)
            await player.set_filter(rotation)
            return await ctx.send('**SUCCESS**: 8D audio is now on. :white_check_mark:')
        elif isactive==True:
            await player.remove_filter(lavalink.filters.Rotation)
            return await ctx.send('**SUCCESS**: 8D audio is now off. :white_check_mark:')

    @commands.command()
    async def music_spatial(self,ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        if not player.is_connected:
            return await ctx.send('**OOPS**: I\'m not in a voice channel. :x:')
        effect = player.get_filter(lavalink.filters.Echo)
        if effect==None:
            isactive = False
        else:
            isactive = True
        if isactive==False:
            echo = lavalink.filters.Echo()
            echo.update(delay=0.05,decay=0.3)
            await player.set_filter(echo)
            return await ctx.send('**SUCCESS**: Spatial audio is now on. :white_check_mark:\n**WARNING**: This feature is experimental - don\'t expect it to work perfectly.')
        elif isactive==True:
            await player.remove_filter(lavalink.filters.Echo)
            return await ctx.send('**SUCCESS**: Spatial audio is now off. :white_check_mark:')

    @commands.command()
    async def music_speed(self, ctx, *, speed):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if len(ctx.author.voice.channel.members) > 3:
            role = discord.utils.get(ctx.guild.roles, name='DJ')
            if role==None:
                if ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='However, it seems like this role is missing on this server. Please notify your server administrator.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
            else:
                if role in ctx.author.roles or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
                    pass
                else:
                    embed = discord.Embed(title='You need to have the DJ role first.',description='It seems like you do not have this role. Please ask your server administrator for this role.\nAlternatively, you can bypass this with the `Manage Server` permission or when there are less than three listeners in the voice channel.',color=0xff0000)
                    return await ctx.send(embed=await applytheme(ctx.author.id,embed))
        try:
            speed = float(speed)
        except:
            return await ctx.send('**OOPS**: Invalid parameter: `<speed>`. :x:')
        if speed > 5:
            return await ctx.send('**OOPS**: That\'s a bit too fast, sorry...:c :x:')
        elif speed <= 0:
            return await ctx.send('excuse me what the fuck')
        elif speed < 0.5:
            return await ctx.send('**OOPS**: That\'s a bit too slow, sorry...:c :x:')
        playspeed = lavalink.filters.Timescale()
        playspeed.update(speed=speed)
        await player.set_filter(playspeed)
        return await ctx.send('**SUCCESS**: Set speed to {0}x. :white_check_mark:'.format(speed))

def setup(bot):
    bot.add_cog(Music(bot))
