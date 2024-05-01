import discord
from discord.ext import commands
from utils import log
import aiohttp
import json
import requests

class SpySlayer: # NOT THE COG ITSELF, JUST THE SCANNER AND ID CACHER.
    def __init__(self,bot,logger):
        self.bot = bot
        self.ids = {}
        self.logger = logger
        try:
            self.ids = requests.get('https://kickthespy.pet/ids',timeout=10).json()
            with open('spypet_cache.json','w+') as file:
                json.dump(self.ids,file,indent=4)
        except:
            try:
                with open('spypet_cache.json', 'r') as file:
                    self.ids = json.load(file)
            except:
                logger.exception('Could not get spy.pet IDs!')

    async def scan(self,guild=None):
        positive = {}
        if not guild:
            for guild in self.bot.guilds:
                found = []
                for member in guild.members:
                    if str(member.id) in self.ids:
                        found.append(member.id)
                if len(found) > 0:
                    positive.update({f'{guild.id}':found})
        else:
            found = []
            for member in guild.members:
                if str(member.id) in self.ids:
                    found.append(member.id)
            if len(found) > 0:
                positive.update({f'{guild.id}': found})
        return positive

    async def disconnect(self,guild):
        if str(guild.id) in self.bot.db['banned']:
            if self.bot.db['banned'][f'{guild.id}']==0:
                # Guild is already banned, return False (cannot ban)
                return False
        else:
            # Guild is not banned
            self.bot.db['banned'].update({f'{guild.id}':0})
        self.bot.db['spybot'].append(guild.id)
        return True


"""
if the ban is permanent (expire time = 0), don't do anything

if the ban is temporary (expire time > 0), warn the servers but don't change the ban, but add the server id to self.bot.db['spybot']

if there are no bans, warn the servers and add a permanent ban and the server id to self.bot.db['spybot']
"""

class SpyPetGuard(commands.Cog, name="SpyPet Guard"):
    """Cog to check for potential web scraper users on member join."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(
            self.bot.package, "spypet_guard", self.bot.loglevel
        )
        self.bot.spyslayer = SpySlayer(self.bot,self.logger)

    async def fetch_spypet_ids(self):
        """Fetch potential web scraper user IDs from kickthespy.pet/ids."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://kickthespy.pet/ids') as response:
                if response.status == 200:
                    data = await response.json()
                    spypet_ids = data.get('ids', [])
                    return spypet_ids
                else:
                    self.logger.error(f"Failed to fetch SpyPet IDs: {response.status}")
                    return []

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if len(self.bot.spyslayer.ids)==0:
            # No IDs found on API or cache, return
            return

        if member.id in self.bot.spyslayer.ids:
            # Trigger the function if a potential scraper user joins
            result = await self.bot.spyslayer.disconnect(member.guild)
            if result:
                self.logger.warning(f'Guild {member.guild.id} has a scraper bot!')
                room = self.bot.config['main_room']
                if room in list(self.bot.db['rooms'].keys()):
                    for guild_id in list(room.keys()):
                        guild = self.bot.get_guild(int(guild_id))
                        webhook: discord.Webhook = await guild.fetch_webhook(room[f'{member.guild.id}'][0])
                        if guild.id==member.guild.id:
                            embed = discord.Embed(
                                color=0xff0000,
                                title="WARNING: A scraper bot was detected!",
                                description="A scraper bot was detected in your server. Unifier has automatically "+
                                            "disconnected your server for users' safety.\n\n"+
                                            "Bots detected:\n"+
                                            f"- <@{member.id}>\n\n"+
                                            "Source: [kickthespy.pet ID list](https://kickthespy.pet/ids)"



                            )
                            await webhook.send(
                                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
                                username=self.bot.user.name + ' (system)',
                                embed=embed
                            )
                        else:
                            embed = discord.Embed(
                                color=0xff0000,
                                description="A scraper bot was found in a server!"
                            )

def setup(bot):
    bot.add_cog(SpyPetGuard(bot))
