import discord
from discord.ext import commands
import ast
import json

admin_ids = [356456393491873795, 549647456837828650]

restricted_rooms = ["test"]

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

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = 'data.json'
        
        # Ensure necessary keys exist
        self.update({'rules':{},'rooms':{},'emojis':[],'nicknames':{},
                     'restricted':[],'locked':[],'superlocked':[],
                     'blocked':{},'banned':{}})

        # Load data
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
            json.dump(self, file, indent=4)

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
        if not hasattr(bot, 'db'):
            self.bot.db = AutoSaveDict(sample_db)
        if not hasattr(self.bot, 'bridged_emojis'):
            if not 'emojis' in list(self.bot.db.keys()):
                self.bot.db.update({'emojis':[]})
                self.bot.db.save_data()
            self.bot.bridged_emojis = self.bot.db['emojis']

    @commands.command()
    async def make(self,ctx,*,room):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can create rooms!')
        if room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room already exists!')
        self.bot.db['rooms'].update({room:{}})
        self.bot.db['rules'].update({room:[]})
        self.bot.db.save_data()
        await ctx.send(f'Created room `{room}`!')
    
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
            data = self.bot.db['rooms'][room]
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
            if len(self.bot.db['rules'][room])==0:
                text = f'No rules exist yet for this room! For now, follow the main room\'s rules.\nYou can always view rules if any get added using `u!rule {room}`.'
            else:
                for rule in self.bot.db['rules'][room]:
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
            data = self.bot.db['rooms'][room]
            guild = []
            guild.append(webhook.id)
            data.update({f'{ctx.guild.id}':guild})
            self.bot.db['rooms'][room] = data
            self.bot.db.save_data()
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
            data = self.bot.db['rooms'][room]
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
            self.bot.db['rooms'][room] = data
            self.bot.db.save_data()
            await ctx.send('Unlinked channel from network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command()
    async def rules(self,ctx,*,room):
        '''Displays room rules.'''
        if is_room_restricted(room) and not is_user_admin(ctx.author.id):
            return await ctx.send(':eyes:')
        if room=='' or not room:
            room = 'main'

        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room doesn\'t exist! Run `u!rooms` to get a full list.')
        
        index = 0
        text = ''
        if room in list(self.bot.db['rules'].keys()):
            rules = self.bot.db['rules'][room]
            if len(rules)==0:
                return await ctx.send('The room creator hasn\'t added rules yet. For now, follow `main` room rules.')
        else:
            return await ctx.send('The room creator hasn\'t added rules yet. For now, follow `main` room rules.')
        for rule in rules:
            if text=='':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        embed = discord.Embed(title='Room rules',description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        await ctx.send(embed=embed)

    @commands.command()
    async def addrule(self,ctx,*,args):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rules!')
        try:
            room, rule = args.split(' ',1)
        except:
            return await ctx.send('Rule is missing.')
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send('This room does not exist!')
        self.bot.db['rules'][room].append(rule)
        self.bot.db.save_data()
        await ctx.send('Added rule!')

    @commands.command()
    async def delrule(self,ctx,*,args):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rules!')
        try:
            room, rule = args.split(' ',1)
        except:
            return await ctx.send('Rule is missing.')
        try:
            rule = int(rule)
            if rule <= 0:
                raise ValueError()
        except:
            return await ctx.send('Rule must be a number higher than 0.')
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send('This room does not exist!')
        self.bot.db['rules'][room].pop(rule-1)
        self.bot.db.save_data()
        await ctx.send('Removed rule!')

    @commands.command()
    async def rooms(self,ctx):
        embed = discord.Embed(title=f'UniChat rooms (Total: `{len(self.bot.db["rooms"])}`)',description='Use `u!bind <room>` to bind to a room.')
        if len(self.bot.db['rooms'])==0:
            embed.add_field(value='No rooms here <:notlikenevira:1144718936986882088>')
            return await ctx.send(embed=embed)
        for room in self.bot.db['rooms']:
            embed.add_field(name=f'`{room}` - '+str(len(self.bot.db['rooms'][room]))+' servers',value='Descriptions coming soon!',inline=False)
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
        self.bot.db['emojis'] = self.bot.bridged_emojis
        self.bot.db.save_data()
    
def setup(bot):
    bot.add_cog(Config(bot))
