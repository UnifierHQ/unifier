import discord
from discord.ext import commands
import ast
import aiofiles
from discord.ext import commands

rules = {
    '_main': ['Be civil and follow Discord ToS and guidelines.',
              'Absolutely no NSFW in here - this is a SFW channel.',
              'Don\'t be a dick and harass others, be a nice fellow to everyone.',
              'Don\'t cause drama, we like to keep things clean.',
              'Don\'t ask for punishments, unless you want to be restricted.',
              'Server and global moderators have the final say, don\'t argue unless there\'s a good reason to.',
              'Don\'t go hating on AM moderators, they\'re still human after all. Just because you got punished (even unfairly) doesn\'t mean you should straightup attack them.',
              'Use common sense. These rules are not comprehensive, don\'t use loopholes or use "it wasn\'t in the rules" as an argument.',
              'Don\'t use server rules as a way of bypassing these rules. Servers violating these rules will be permanently global restricted.',
              'If something doesn\'t break UniChat rules, but breaks your server\'s rules, then it\'s your and your moderators\' responsibility to take action. We only take action if the content violates UniChat rules.'
              ],
    '_pr': ['Follow all main room rules.',
            'Only PRs in here - no comments allowed.'],
    '_prcomments': ['Follow all main room rules.',
                    'Don\'t make PRs in here - this is for comments only.'],
    '_liveries': ['Follow all main room rules.',
                  'Please keep things on topic and post liveries or comments on liveries only.'],
    '_test': ['test your heart out']
    }

class Config(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(self.bot, 'bridged_emojis'):
            x = open('emojis.txt','r',encoding='utf-8')
            emojis = x.read()
            x.close()
            self.bot.bridged_emojis = ast.literal_eval(emojis)
    
    @commands.command(aliases=['link','connect','federate','bridge'])
    async def bind(self,ctx,*,room=''):
        if not ctx.author.guild_permissions.administrator and not ctx.author.id==356456393491873795:
            return await ctx.send('You don\'t have the necessary permissions.')
        roomid = '_'+room
        if room=='test' and not ctx.author.id==356456393491873795:
            return await ctx.send('Only Green can bind channels to test rooms.')
        if room=='':
            roomid = '_main'
        try:
            async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
                data = await x.read()
                data = ast.literal_eval(data)
                await x.close()
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
        try:
            try:
                guild = data[f'{ctx.guild.id}']
            except:
                guild = []
            if len(guild) >= 1:
                return await ctx.send('Your server is already linked to this room.\n**Accidentally deleted the webhook?** `u!unlink` it then `u!link` it back.')
            index = 0
            text = ''
            for rule in rules[roomid]:
                if text=='':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
            text = f'{text}\n\nPlease display these rules somewhere accessible.'
            embed = discord.Embed(title='Please agree to the room rules first:',description=text)
            embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
            ButtonStyle = discord.ButtonStyle
            row = [
                discord.ui.Button(style=ButtonStyle.green, label='Accept and bind', custom_id=f'accept',disabled=False),
                discord.ui.Button(style=ButtonStyle.red, label='No thanks', custom_id=f'reject',disabled=False)
                ]
            btns = discord.ui.ActionRow(row[0],row[1])
            components = discord.ui.MessageComponents(btns)
            msg = await ctx.send(embed=embed,components=components)

            def check(interaction):
                return interaction.user.id==ctx.author.id and (
                    interaction.custom_id=='accept' or
                    interaction.custom_id=='reject'
                    ) and interaction.channel.id==ctx.channel.id

            try:
                resp = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            except:
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0],row[1])
                components = discord.ui.MessageComponents(btns)
                await msg.edit(components=components)
                return await ctx.send('Timed out.')
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0],row[1])
            components = discord.ui.MessageComponents(btns)
            await resp.response.edit_message(components=components)
            if resp.custom_id=='reject':
                return
            webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
            async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
                data = await x.read()
                data = ast.literal_eval(data)
                await x.close()
            guild = []
            guild.append(webhook.id)
            data.update({f'{ctx.guild.id}':guild})
            x = open(f'participants{roomid}.txt','w+',encoding='utf-8')
            x.write(f'{data}')
            x.close()
            await ctx.send('Linked channel with network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command(aliases=['unlink','disconnect'])
    async def unbind(self,ctx,*,room=''):
        if room=='':
            return await ctx.send('You must specify the room to unbind from.')
        if not ctx.author.guild_permissions.administrator and not ctx.author.id==356456393491873795:
            return await ctx.send('You don\'t have the necessary permissions.')
        roomid = '_'+room
        try:
            async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
                data = await x.read()
                data = ast.literal_eval(data)
                await x.close()
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
        try:
            try:
                hooks = await ctx.guild.webhooks()
            except:
                return await ctx.send('I cannot manage webhooks.')
            hook_ids = data.setdefault(f'{ctx.guild.id}', [])
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
            data.pop(f'{ctx.guild.id}')
            x = open(f'participants{roomid}.txt','w+',encoding='utf-8')
            x.write(f'{data}')
            x.close()
            await ctx.send('Unlinked channel from network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command()
    async def rules(self,ctx,*,room):
        '''Displays room rules.'''
        roomid = '_'+room
        if room=='test' and not ctx.author.id==356456393491873795:
            return await ctx.send(':eyes:')
        if room=='':
            roomid = '_main'
        index = 0
        text = ''
        try:
            for rule in rules[roomid]:
                if text=='':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
        embed = discord.Embed(title='Room rules',description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        await ctx.send(embed=embed)

    @commands.command()
    async def toggle_emoji(self,ctx):
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send('You don\'t have the necessary permissions.')
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send('All members can now no longer use your emojis!')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send('All members can now use your emojis!')
        x = open('emojis.txt','w+',encoding='utf-8')
        x.write(f'{self.bot.bridged_emojis}')
        x.close()
    
def setup(bot):
    bot.add_cog(Config(bot))
