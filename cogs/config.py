import discord
from discord.ext import commands
import ast
from discord.ext import commands
#Db auto update thingy
import json

class AutoSaveDict(dict):
    def __init__(self, file_path='data.json', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            self.update(data)
        except FileNotFoundError:
            pass  # If the file is not found, initialize an empty dictionary

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=2)

# Load data from db.json into an existing dictionary
sample_db = {"rules": {
    'main': ['Be civil and follow Discord ToS and guidelines.',
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
    'pr': ['Follow all main room rules.',
            'Only PRs in here - no comments allowed.'],
    'prcomments': ['Follow all main room rules.',
                    'Don\'t make PRs in here - this is for comments only.'],
    'liveries': ['Follow all main room rules.',
                  'Please keep things on topic and post liveries or comments on liveries only.'],
    'test': ['test your heart out']
    }
}
db = AutoSaveDict(sample_db)



admin_ids = [356456393491873795, 549647456837828650]

restricted_rooms = ["test"]

def is_user_admin(id):
    try:
        global admin_ids
        if id in admin_ids:
            return True
        else:
            return False
    except:
        print("There was an error in 'is_user_admin(id)', for security reasons permission was resulted into denying!")
        return False

def is_room_restricted(room):
    try:
        global restricted_rooms
        if room in restricted_rooms:
            return True
        else:
            return False
    except:
        print("There was an error in 'is_room_restricted(room)', for security reasons permission was resulted into answering as restricted!")
        return False

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
        if not ctx.author.guild_permissions.administrator and not is_user_admin(ctx.author.id):
            return await ctx.send('You don\'t have the necessary permissions.')
        if is_room_restricted(room) and not is_user_admin(ctx.author.id):
            return await ctx.send('Only Green and ItsAsheer can bind channels to restricted rooms.')
        if room=='' or not room: #Added "not room" as a failback
            room = 'main'
            await ctx.send('**No room was given, defaulting to main**')
        try:
            data = db[f"room_{room}"]
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
            for rule in rules[room]:
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
            data = db[f"room_{room}"]
            guild = []
            guild.append(webhook.id)
            data.update({f'{ctx.guild.id}':guild})
            db[f"room_{room}"] = data
            await ctx.send('Linked channel with network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command(aliases=['unlink','disconnect'])
    async def unbind(self,ctx,*,room=''):
        if room=='':
            return await ctx.send('You must specify the room to unbind from.')
        if not ctx.author.guild_permissions.administrator and not is_user_admin(ctx.author.id):
            return await ctx.send('You don\'t have the necessary permissions.')
        try:
            data = db[f"room_{room}"]
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
            db[f"room_{room}"] = data
            await ctx.send('Unlinked channel from network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command()
    async def rules(self,ctx,*,room):
        '''Displays room rules.'''
        room = room #removed '_' + room, now works without it
        if is_room_restricted(room) and not is_user_admin(ctx.author.id):
            return await ctx.send(':eyes:')
        if room=='' or not room:
            room = 'main'

        index = 0
        text = ''
        try:
            for rule in rules[room]:
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
