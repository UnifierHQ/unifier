import discord
from discord.ext import commands
from utils import log
from enum import Enum


class UserRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    TRUSTED = "trusted"
    BANNED = "banned"
    USER = "user"

class Badge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'badge', self.bot.loglevel)
        self.embed_colors = {
            UserRole.OWNER: (
                self.bot.colors.greens_hair if self.bot.user.id==1187093090415149056 else self.bot.colors.unifier
            ),
            UserRole.ADMIN: discord.Color.green(),
            UserRole.MODERATOR: discord.Color.purple(),
            UserRole.TRUSTED: self.bot.colors.gold,
            UserRole.BANNED: discord.Color.red(),
            UserRole.USER: discord.Color.blurple()
        }

    @commands.command()
    async def badge(self, ctx):
        user_role = self.get_user_role(ctx.author.id)
        embed = discord.Embed(
            title="Unifier",
            description=f"<@{ctx.author.id}> is a Unifier **{user_role.value}**.",
            color=self.embed_colors[user_role]
        )
        # Best easter egg in the world
        #TODO ADD EASTER EGG L BOZO

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def trust(self, ctx, action, user: discord.User):
        if ctx.author.id not in self.bot.admins:
            return await ctx.send("You don't have permission to use this command.")

        action = action.lower()
        if action not in ['add', 'remove']:
            return await ctx.send("Invalid action. Please use 'add' or 'remove'.")

        trusted_group = self.bot.trusted_group
        if action == 'add':
            if user.id not in trusted_group:
                trusted_group.append(user.id)
        elif action == 'remove':
            if user.id in trusted_group:
                trusted_group.remove(user.id)

        self.bot.trusted_group = trusted_group
        self.bot.save_trusted_group()

        user_role = UserRole.TRUSTED if action == 'add' else UserRole.USER
        embed = discord.Embed(
            title="Unifier",
            description=f"{'Added' if action == 'add' else 'Removed'} user {user.mention} from the trust group.",
            color=self.embed_colors[user_role],
        )
        await ctx.send(embed=embed)

    def get_user_role(self, user_id):
        if user_id in self.bot.config['owner']:
            return UserRole.OWNER
        elif user_id in self.bot.admins:
            return UserRole.ADMIN
        elif user_id in self.bot.moderators:
            return UserRole.MODERATOR
        elif user_id in self.bot.trusted_group:
            return UserRole.TRUSTED
        elif user_id in self.bot.db['banned']:
            return UserRole.BANNED
        else:
            return UserRole.USER

def setup(bot):
    bot.add_cog(Badge(bot))
