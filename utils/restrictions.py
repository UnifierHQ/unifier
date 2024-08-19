from nextcord.ext import commands

class Restrictions:
    def __init__(self, bot=None):
        self.__bot = bot
        self.__attached = (not bot is None)

    @property
    def attached(self):
        return self.__attached

    def attach_bot(self, bot):
        if self.__bot:
            raise ValueError('Bot already attached')
        self.__bot = bot
        self.__attached = True

    def owner(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def admin(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id in self.__bot.admins or ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def moderator(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id in self.__bot.moderators or ctx.author.id in self.__bot.admins or ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def under_attack(self):
        async def predicate(ctx: commands.Context):
            if f'{ctx.guild.id}' in self.__bot.db['underattack']:
                return ctx.author.guild_permissions.manage_channels
            else:
                return ctx.author.guild_permissions.ban_members or ctx.author.guild_permissions.manage_channels

        return commands.check(predicate)

    def demo_error(self):
        """A demo check which will always fail, intended for development use only."""

        async def predicate(_ctx: commands.Context):
            return False

        return commands.check(predicate)
