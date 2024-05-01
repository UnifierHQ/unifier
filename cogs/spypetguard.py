import discord
from discord.ext import commands
from utils import log
import aiohttp
import json
import requests

class SpySlayer:
    """A spy.pet scraper bot detector."""
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
                        try:
                            webhook: discord.Webhook = await self.bot.fetch_webhook(room[f'{guild_id}'][0])
                        except:
                            continue
                        if int(guild_id)==member.guild.id:
                            embed = discord.Embed(
                                color=0xff0000,
                                title="WARNING: A scraper bot was detected!",
                                description="A scraper bot was detected in your server. Unifier has automatically "+
                                            "global banned your server for users' safety.\n\n"+
                                            "Bots detected:\n"+
                                            f"- <@{member.id}>\n\n"+
                                            "Source: [kickthespy.pet ID list](https://kickthespy.pet/ids)"
                            )
                            # note to devs: convert each step to individual fields if things get complicated
                            embed.add_field(
                                name='What now?',
                                value='1. Ban all users shown above, as they are scraper bots.\n'+
                                      '2. Run `u!spyscan`.\n'+
                                      '3. If the bots are no longer detected, the ban will be lifted, unless '+
                                      'the server has another ongoing ban.',
                                inline=False
                            )
                            await webhook.channel.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                color=0xff0000,
                                title='Server removed',
                                description="A scraper bot was found in a server! The server was removed from the "+
                                            f"{self.bot.user.global_name} network and they have been informed."
                            )
                            await webhook.send(
                                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
                                username=self.bot.user.global_name + ' (system)',
                                embed=embed
                            )

    @commands.command()
    async def spyscan(self,ctx):
        results = await self.bot.spyslayer.scan(ctx.guild)
        if len(results[f'{ctx.guild.id}'])==0:
            # No bots, ban can be lifted. Check for an existing ban first.
            if ctx.guild.id in self.bot.db['spybot']:
                self.bot.db['spybot'].remove(ctx.guild.id)
                embed = discord.Embed(title="Scraper scan results",
                                      description="**No bots detected**\nNo scraper bots were detected. " +
                                                  f"Your access to {self.bot.user.global_name} has been " +
                                                  "restored successfully!",
                                      color=discord.Color.greyple()
                                      )
                if str(ctx.guild.id) in self.bot.db['banned']:
                    if self.bot.db['banned'][f'{ctx.guild.id}'] > 0:
                        # Guild is temporarily banned, do not lift ban
                        embed = discord.Embed(title="Scraper scan results",
                                              description="**No bots detected**\nNo scraper bots were detected, "+
                                                          "however your server still has an ongoing ban. Your access "+
                                                          f"to {self.bot.user.global_name} will be restored once the "+
                                                          "ban is lifted or expires.",
                                              color=0xffcc00
                        )
                    else:
                        self.bot.db['banned'].pop(f'{ctx.guild.id}')
            else:
                embed = discord.Embed(title="Scraper scan results",
                                      description="**No bots detected**\nNo scraper bots were detected. " +
                                                  "All is well!",
                                      color=discord.Color.greyple()
                                      )
        else:
            embed = discord.Embed(title="Scraper scan results",
                                  description="**Bots detected**\nOne or more scrapers were detected. Server will " +
                                              "be global banned for safety.",
                                  color=0xff0000
                                  )
            await self.bot.spyslayer.disconnect(ctx.guild)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(SpyPetGuard(bot))
