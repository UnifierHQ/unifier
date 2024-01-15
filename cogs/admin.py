import discord
from discord.ext import commands
import aiofiles
import inspect
import asyncio
import aiohttp
from discord import File
import inspect
import io
import textwrap
import traceback
import aiohttp
from contextlib import redirect_stdout
import base64
import platform
import psutil
import cpuinfo
import os
import time

noeval = '''```-------------No eval?-------------
⠀⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀```'''

def cleanup_code(content):
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    return content.strip('` \n')

def set_author(embed,**kwargs):
    try:
        embed.set_author(name=kwargs['name'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_author(name=kwargs['name'])

def set_footer(embed,**kwargs):
    try:
        embed.set_footer(text=kwargs['text'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_footer(text=kwargs['text'])

class Admin(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author.id==356456393491873795:
            if message.content.lower()=='nevira delete this shit' or message.content.lower()=='nevira silently delete this shit':
                if message.content.lower()=='nevira silently delete this shit':
                    silent = True
                else:
                    silent = False
                if message.reference==None:
                    return
                if message.reference.cached_message==None:
                    try:
                        msg = await message.channel.fetch_message(message.reference.message_id)
                        if not msg.author.id==853979577156501564:
                            return await message.channel.send('never gonna ~~give you up~~ delete msgs that arent mine unless you ask me to purge')
                        await msg.delete()
                        if not silent:
                            await message.channel.send('gone, reduced to atoms')
                        return
                    except:
                        return await message.channel.send('what the fuck')
                if not message.reference.cached_message.author.id==853979577156501564:
                    return await message.channel.send('never gonna ~~give you up~~ delete msgs that arent mine unless you ask me to purge')
                try:
                    await message.reference.cached_message.delete()
                    if not silent:
                        await message.channel.send('gone, reduced to atoms')
                    return
                except:
                    return await message.channel.send('what the fuck')
            elif message.content=='its nv! not Nv!' or message.content=='it\'s nv! not Nv!' or message.content=='its nv not Nv' or message.content=='it\'s nv not Nv':
                try:
                    async with aiofiles.open('%s_prefix.txt' % message.guild.id,'r',encoding='utf-8') as x:
                        prefix = await x.read()
                        await x.close()
                except:
                    prefix = ''
                if not prefix=='Nv!':
                    await message.channel.send('# FOR THE LAST TIME, IT\'S ALL LOWERCASE\nr/foundthemobileuser moment\n\nnot even the custom prefix is set to Nv! so please stop trying and use all lowercase for once',reference=message)
                else:
                    await message.channel.send('uhh the custom prefix is set to Nv! so it doesnt matter',reference=message)

    @commands.command(hidden=True)
    async def dashboard(self,ctx):
        if ctx.author.id==356456393491873795:
            async with aiofiles.open('uptime.txt','r',encoding='utf-8') as x:
                startup = await x.read()
                startup = int(startup)
                await x.close()
            embed = discord.Embed(title='Nevira dashboard',description='<a:loading0:697470120246902806> Just a moment...',color=0xb5eeff)
            before = time.monotonic()
            msg = await ctx.send(embed=embed)
            ping = (time.monotonic() - before) * 1000
            pingspeed = round(ping, 1)
            current = round(time.time())
            uptime = current - startup
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            seconds = (uptime % 3600) % 60
            import platform
            import psutil
            arch = platform.machine()
            osinfo = platform.platform()
            cpu = await self.bot.loop.run_in_executor(None, lambda: cpuinfo.get_cpu_info()['brand_raw'])
            ghz = await self.bot.loop.run_in_executor(None, lambda: round(cpuinfo.get_cpu_info()['hz_actual'][0]/1000000000,2))
            ram = round(psutil.virtual_memory().total / (1024.0 **3))
            cpuusage = psutil.cpu_percent()
            ramusage = psutil.virtual_memory()[2]
            membercount = 0
            for guild in self.bot.guilds:
                try:
                    membercount = membercount + guild.member_count
                except:
                    pass
            embed = discord.Embed(title='Nevira Dashboard',color=0xb5eeff)
            embed.add_field(name='Latency',value='%s ms' % round(ping, 1),inline=True)
            embed.add_field(name='CPU',value='{0} ({1} GHz, currently using {2}%)'.format(cpu,ghz,cpuusage),inline=True)
            embed.add_field(name='RAM',value='{0} GB (currently using {1}%)'.format(ram,ramusage),inline=True)
            embed.add_field(name='Architecture',value=arch,inline=True)
            embed.add_field(name='OS',value=osinfo,inline=True)
            guildcount = len(self.bot.guilds)
            if guildcount == 69:
                guildcount = '69 :smirk:'
            embed.add_field(name='Server count',value='%s' % guildcount,inline=True)
            embed.add_field(name='User count',value='{0} ({1} cached)'.format(membercount,len(set(self.bot.get_all_members())),inline=True))
            embed.add_field(name='Up since',value=f'<t:{startup}:f>',inline=False)
            embed.add_field(name='Uptime',value=f'`{hours}` hours, `{minutes}` minutes, `{seconds}` seconds',inline=False)
            await msg.edit(embed=embed)

    @commands.command(hidden=True)
    async def serverload(self,ctx):
        try:
            page = int(page)
        except:
            page = 1
        pid = None
        if ctx.author.id==356456393491873795:
            import platform
            import psutil
            def bars(num):
                num = round(num)
                num = num / 5
                num = int(num)
                string = ''
                for x in range(0,num):
                    string = '%s|' % string
                num = 20 - num
                for x in range(0,num):
                    string = '%s ' % string
                return string
            def bars2(num):
                num = round(num)
                num = num / 10
                num = int(num)
                string = ''
                for x in range(0,num):
                    string = '%s|' % string
                num = 10 - num
                for x in range(0,num):
                    string = '%s ' % string
                return string
            cpu = await self.bot.loop.run_in_executor(None, lambda: cpuinfo.get_cpu_info()['brand_raw'])
            ram = await self.bot.loop.run_in_executor(None, lambda: round(psutil.virtual_memory().total / (1024.0 **3)))
            swap = await self.bot.loop.run_in_executor(None, lambda: round(psutil.swap_memory().total / (1024.0 **3)))
            ghz = await self.bot.loop.run_in_executor(None, lambda: round(cpuinfo.get_cpu_info()['hz_actual'][0]/1000000000,2))
            try:
                pid = int(pid)
            except:
                pid = os.getpid()
            cpu_chart = ['','','','','','','','','','']
            ram_chart = ['','','','','','','','','','']
            swap_chart = ['','','','','','','','','','']
            action_row = discord.ui.MessageComponents(discord.ui.ActionRow(discord.ui.Button(style=discord.ButtonStyle.red, label='Destroy', custom_id='destroy')))
            while True:
                found = False
                for proc in psutil.process_iter():
                    if proc.pid==pid:
                        pInfoDict = await self.bot.loop.run_in_executor(None, lambda: proc.as_dict(attrs=['pid', 'name', 'cpu_percent']))
                        found = True
                        break
                if found==True:
                    try:
                        process = await self.bot.loop.run_in_executor(None, lambda: psutil.Process(pid))
                        mem = process.memory_info().rss
                        mem = round(mem/(1024.0 **3),2)
                        memusage = mem / ram
                    except:
                        pass
                cpuusage = await self.bot.loop.run_in_executor(None, lambda: psutil.cpu_percent(percpu=True))
                cpu_all = await self.bot.loop.run_in_executor(None, lambda: psutil.cpu_percent())
                corecount = await self.bot.loop.run_in_executor(None, lambda: psutil.cpu_count(logical=False))
                ramusage = await self.bot.loop.run_in_executor(None, lambda: psutil.virtual_memory()[2])
                ramgb = await self.bot.loop.run_in_executor(None, lambda: round(psutil.virtual_memory().used/1000000000,2))
                swpgb = await self.bot.loop.run_in_executor(None, lambda: round(psutil.swap_memory().used/(1024.0 **3),2))
                swpusage = await self.bot.loop.run_in_executor(None, lambda: round(psutil.swap_memory().percent))
                embed = discord.Embed(title='Server load',color=0xb5eeff)
                text = ''
                count = 0
                warn = False
                for num in cpuusage:
                    if num >= 70:
                        warn = True
                    count = count + 1
                    toadd = bars2(num)
                    num2 = f'{round(num)}'
                    if len(num2)==1:
                        num2 = f' {num2}%'
                    elif len(num2)==3:
                        pass
                    else:
                        num2 = f'{num2}%'
                    if text=='':
                        if num >= 70:
                            if cpu_all >= 70:
                                if len(cpuusage) > 10:
                                    text = '```diff\n-  C LD% LD Bar\n-  {0} {1} {2}'.format(count,num2,toadd)
                                else:
                                    text = '```diff\n- C LD% LD Bar\n- {0} {1} {2}'.format(count,num2,toadd)
                            else:
                                if len(cpuusage) > 10:
                                    text = '```diff\n   C LD% LD Bar\n-  {0} {1} {2}'.format(count,num2,toadd)
                                else:
                                    text = '```diff\n  C LD% LD Bar\n- {0} {1} {2}'.format(count,num2,toadd)
                                
                        else:
                            if len(cpuusage) > 10:
                                if cpu_all >= 70:
                                    text = '```diff\n-  C LD% LD Bar\n+  {0} {1} {2}'.format(count,num2,toadd)
                                else:
                                    text = '```diff\n   C LD% LD Bar\n+  {0} {1} {2}'.format(count,num2,toadd)
                            else:
                                if cpu_all >= 70:
                                    text = '```diff\n- C LD% LD Bar\n+ {0} {1} {2}'.format(count,num2,toadd)
                                else:
                                    text = '```diff\n  C LD% LD Bar\n+ {0} {1} {2}'.format(count,num2,toadd)
                    else:
                        if len(cpuusage) > 10 and count < 10:
                            if num >= 70:
                                text = '{0}\n-  {1} {2} {3}'.format(text,count,num2,toadd)
                            else:
                                text = '{0}\n+  {1} {2} {3}'.format(text,count,num2,toadd)
                        else:
                            if num >= 70:
                                text = '{0}\n- {1} {2} {3}'.format(text,count,num2,toadd)
                            else:
                                text = '{0}\n+ {1} {2} {3}'.format(text,count,num2,toadd)
                num4 = f'{round(ramusage)}'
                num5 = f'{round(swpusage)}'
                if len(num4)==1:
                    num4 = f' {num4}%'
                elif len(num4)==3:
                    pass
                else:
                    num4 = f'{num4}%'
                if len(num5)==1:
                    num5 = f' {num5}%'
                elif len(num5)==3:
                    pass
                else:
                    num5 = f'{num5}%'
                if ramusage >= 70:
                    text1 = '```diff\n- TYPE GB  LD% LD Bar\n- PHYS {0} {1} {2}'.format(round(ramgb,1),num4,bars2(ramusage))
                else:
                    text1 = '```diff\n  TYPE GB  LD% LD Bar\n+ PHYS {0} {1} {2}'.format(round(ramgb,1),num4,bars2(ramusage))
                if swpusage > 100:
                    text1 = '{0}\n- SWAP {1} XXX |INVALID||```'.format(text1,round(swpgb,1))
                elif swpusage >= 70:
                    text1 = '{0}\n- SWAP {1} {2} {3}```'.format(text1,round(swpgb,1),num5,bars2(swpusage))
                else:
                    text1 = '{0}\n+ SWAP {1} {2} {3}```'.format(text1,round(swpgb,1),num5,bars2(swpusage))
                graph = bars(cpu_all)
                num3 = f'{round(cpu_all)}'
                if len(num3)==1:
                    num3 = f' {num3}%'
                elif len(num3)==3:
                    pass
                else:
                    num3 = f'{num3}%'
                if cpu_all >= 70:
                    addtograph = '- {0} {1}'.format(num3,graph)
                else:
                    addtograph = '+ {0} {1}'.format(num3,graph)
                cpu_chart.pop(0)
                cpu_chart.append(addtograph)
                cpu_graph = ''
                for line in cpu_chart:
                    if cpu_graph=='':
                        cpu_graph = '```diff\nHistorical load (all cores)\n  LD% LD Bar\n{0}'.format(line)
                    else:
                        cpu_graph = '{0}\n{1}'.format(cpu_graph,line)
                cpu_graph = f'{cpu_graph}```'
                text = f'{text}```'
                
                graph = bars2(ramusage)
                mem1 = round(ramgb,1)
                if ramusage >= 70:
                    addtograph = '- {0} {1} {2}'.format(mem1,num4,graph)
                else:
                    addtograph = '+ {0} {1} {2}'.format(mem1,num4,graph)
                ram_chart.pop(0)
                ram_chart.append(addtograph)
                ram_graph = ''
                for line in ram_chart:
                    if ram_graph=='':
                        ram_graph = '```diff\nHistorical load (RAM only)\n  GB  LD% LD Bar\n{0}'.format(line)
                    else:
                        ram_graph = '{0}\n{1}'.format(ram_graph,line)
                ram_graph = f'{ram_graph}```'
                try:
                    cpustats = f'```fix\n{corecount}-core {cpu} ({ghz} GHz)\nUsage: {round(cpu_all)}%\nP.Usg: {round(pInfoDict["cpu_percent"])}%```'
                except:
                    cpustats = f'```fix\n{corecount}-core {cpu} ({ghz} GHz)\nUsage: {round(cpu_all)}%\nP.Usg: ?%```'
                content1 = f'{cpustats}{text}{cpu_graph}'
                try:
                    ramstats = f'```fix\n{ram}GB RAM\n{swap}GB SWAP\nUsage: {round(ramusage)}%\nSwp.U: {round(swpusage)}%\nUsgGB: {ramgb} GB\nP.Usg: {round(memusage*100)}%```'
                except:
                    ramstats = f'```fix\n{ram}GB RAM\nUsage: {round(ramusage)}%\nUsgGB: {ramgb} GB\nP.Usg: ?%```'
                content2 = f'{ramstats}{text1}{ram_graph}'
                if warn==True:
                    embed.add_field(name='CPU Status <:warn:623591112879374356>',value=content1,inline=True)
                else:
                    embed.add_field(name='CPU Status',value=content1,inline=True)
                if ramusage >= 70:
                    embed.add_field(name='Memory Status <:warn:623591112879374356>',value=content2,inline=True)
                else:
                    embed.add_field(name='Memory Status',value=content2,inline=True)
                try:
                    await msg.edit(embed=embed,components=action_row)
                except:
                    msg = await ctx.send(embed=embed,components=action_row)
                def check(interaction):
                    return interaction.user.id==356456393491873795 and interaction.message.id==msg.id
                try:
                    interaction = await self.bot.wait_for("component_interaction", check=check, timeout=5.0)
                except:
                    pass
                else:
                    try:
                        await msg.delete()
                    except:
                        pass
                    break

    @commands.command(hidden=True)
    async def eval(self,ctx,*,body):
        if ctx.author.id==356456393491873795:
            import io
            import traceback
            env = {
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                'source': inspect.getsource,
                'session':self.bot.session,
                'bot':self.bot
            }

            env.update(globals())

            body = cleanup_code(body)
            stdout = io.StringIO()
            err = out = None

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                if 'bot.token' in body:
                    raise ValueError('Blocked phrase')
                exec(to_compile, env)
            except Exception as e:
                pass

            try:
                func = env['func']
            except Exception as e:
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` your code sucks <@356456393491873795>\n`2.` no megamind?')
                await ctx.author.send(f'```py\n{e.__class__.__name__}: {e}\n```')
                return
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` your code sucks <@356456393491873795>\n`2.` no megamind?')
                await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                if value=='':
                    pass
                else:
                    await ctx.send('```%s```' % value)
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @eval.error
    async def eval_error(self,ctx,error):
        if ctx.author.id==356456393491873795:
            if isinstance(error, commands.MissingRequiredArgument):
                try:
                    await ctx.send('no shit youre a certified dumbass <@356456393491873795> **YOU FORGOT THE DAMN CODE LMFAOOOOO**',file=discord.File(fp='nocode.png'))
                except:
                    try:
                        await ctx.send('no shit youre a certified dumbass <@356456393491873795> **YOU FORGOT THE DAMN CODE LMFAOOOOO**\nalso you (or the server mods) forgor :skull: to give me attach files perms so pls do that i guess')
                    except:
                        await ctx.author.send('ok green how dumb can you be, you forgot your code AND **YOU TRIED TO EVAL IN A CHANNEL WHERE I CANT SEND SHIT BRUHHHHHH**')
            else:
                try:
                    await ctx.send('<@356456393491873795> id call you an idiot but something terribly went wrong here and idk what it is')
                    raise
                except:
                    raise
                    await ctx.author.send('i cant send shit in that channel lol you fucking idiot')
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @commands.command(hidden=True)
    async def reload(self,ctx,*,extensions):
        if ctx.author.id==356456393491873795:
            extensions = extensions.split(' ')
            msg = await ctx.send('Reloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    self.bot.reload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Reload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run reload! <:error:623591109016420365>')

    @commands.command(hidden=True)
    async def load(self,ctx,*,extensions):
        if ctx.author.id==356456393491873795:
            extensions = extensions.split(' ')
            msg = await ctx.send('Loading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    self.bot.load_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Load completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run load! <:error:623591109016420365>')

    @commands.command(hidden=True)
    async def unload(self,ctx,*,extensions):
        if ctx.author.id==356456393491873795:
            extensions = extensions.split(' ')
            msg = await ctx.send('Unloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    if extension=='admin':
                        raise ValueError('Cannot unload the admin extension, let\'s not break the bot here!')
                    self.bot.unload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Unload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run unload! <:error:623591109016420365>')

    @commands.command(hidden=True)
    async def setpfp(self,ctx,*,pfpchoice=None):
        if ctx.author.id==356456393491873795:
            from random import randint, choice
            pfplist = ['nevcry','neverror','neveyebrowraise','nevhappy','neviraldi','nevloading','nevmogus','nevohno','nevsmile','nevsus','nevwink']
            pfp = choice(pfplist)
            if pfpchoice in pfplist:
                pfp = pfpchoice
            await self.bot.user.edit(avatar=open(f'{pfp}.png','rb').read())
            await ctx.send(f'Set profile picture to `{pfp}`')

def setup(bot):
    bot.add_cog(Admin(bot))
