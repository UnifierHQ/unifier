import discord
from discord.ext import commands
import requests
import time

def download_image(url, destination_path):
    try:
        response = requests.get(url, timeout=None)
        response.raise_for_status()

        with open(destination_path, 'wb') as file:
            file.write(response.content)

        print(f"Image downloaded successfully to {destination_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")


class InuAI(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,message):
        pass
    
    @commands.command()
    async def inuai(self, ctx, *, args):
        start_time = time.time()
        embed = discord.Embed(
        title="InuAi",
        description=f"<@{ctx.author.id}> asked me to generate '{args}', generating please wait...\n\n ETA: 30 seconds or less (if cached)",
        color=discord.Color.blurple()  # You can change the color to your preference
        )

        await ctx.send(embed=embed)

        api_key = "unifier-v3h45269890y"
        image_path = 'inuai.png'

        turl = f"https://inuai.altex.page/?api_key={api_key}&gen={args}"
        download_image(turl, image_path)

        embed = discord.Embed(
            title=f"Generated '{args}' with InuAi",
            color=discord.Color.blurple()  # You can change the color to your preference
        )

        embed.set_footer(text="Powered by InuAI")  # Replace "icon_url_here" with the actual icon URL

        with open(image_path, 'rb') as image_file:
            image = discord.File(image_file, filename="inuai.png")
            embed.set_image(url=f"attachment://inuai.png")
            end_time = time.time()
            duration_seconds = end_time - start_time
            embed.description = f"Operation took {duration_seconds} seconds."
            await ctx.send(f"<@{ctx.author.id}>", embed=embed, file=image)

    
        

def setup(bot):
    bot.add_cog(InuAI(bot))
