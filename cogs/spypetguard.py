import discord
from discord.ext import commands
from utils import log
import aiohttp

class SpyPetGuard(commands.Cog, name="SpyPet Guard"):
    """Cog to check for potential web scraper users on member join."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(
            self.bot.package, "spypet_guard", self.bot.loglevel
        )

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

    async def check_scraper_users(self):
        """Check for potential web scraper users on member join."""
        scraper_ids = self.bot.spypetids

        if not scraper_ids:
            scraper_ids = await self.fetch_spypet_ids()
            if scraper_ids:
                self.bot.spypetids = scraper_ids
            else:
                self.logger.error("Failed to fetch SpyPet IDs. Check logs for details.")
                return

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id in scraper_ids:
                    # Trigger the function if a potential scraper user is found
                    await self.trigger_scraper_user_function(member)

    async def trigger_scraper_user_function(self, user):
        # Implement your function logic here
        if user.discriminator != 0:
            self.logger.info(f"Potential web scraper user detected: {user.name}#{user.discriminator}")
        else:
            self.logger.info(f"Potential web scraper user detected: {user.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_scraper_users()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        scraper_ids = self.bot.spypetids

        if not scraper_ids:
            scraper_ids = await self.fetch_spypet_ids()
            if scraper_ids:
                self.bot.spypetids = scraper_ids
            else:
                self.logger.error("Failed to fetch SpyPet IDs. Check logs for details.")
                return

        if member.id in scraper_ids:
            # Trigger the function if a potential scraper user joins
            await self.trigger_scraper_user_function(member)

def setup(bot):
    bot.add_cog(SpyPetGuard(bot))
