import discord
from discord.ext import commands
import asyncio
import aiohttp
import revolt
import json

with open('config.json', 'r') as file:
    data = json.load(file)

owner = data['owner']

class Revolt(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(self.bot, 'revolt_client'):
            self.bot.revolt_client = None
            self.revolt_client_task = asyncio.create_task(self.revolt_boot())

    class Client(revolt.Client):
        async def on_message(self, message):
            print(message.content)

    async def revolt_boot(self):
        if self.bot.revolt_client is None:
            async with aiohttp.ClientSession() as session:
                self.bot.revolt_client = self.Client(session, data['revolt_token'])
                print('booting revolt client')
                await self.bot.revolt_client.start()

    @commands.command(hidden=True)
    async def send_to_revolt(self,ctx,*,message):
        if not ctx.author.id==owner:
            return
        server = self.bot.revolt_client.get_server('01HDS71G78AT18B9DEW3K6KXST')
        channel = server.get_channel('01HDS71G78TTV3J3HMX3FB180Q')
        persona = revolt.Masquerade(name="green. (discord)",avatar=ctx.author.avatar.url)
        await channel.send(message,masquerade=persona)

def setup(bot):
    bot.add_cog(Revolt(bot))
