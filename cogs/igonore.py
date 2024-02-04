    @commands.command()
    async def reportuser(self,ctx,*,target):
        reason = ''
        parts = target.split(' ')
        if len(parts) >= 2:
            if len(parts)==2:
                return await ctx.send("To report a user you need to provide a reason, try: ```u!reportuser @Unifier Reason goes here```")
            else:
                reason = target.replace(f'{parts[0]} ','',1)
            target = parts[0]
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id:
                return await ctx.send('You can\'t report yourself :thinking:')
        except:
            return await ctx.send('Invalid user/server!')

        if userid in self.bot.moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('If you need to report a moderator please refer directly to green. or ItsAsheer as moderators see reports.')

        if ctx.author.discriminator=='0':
            reporter = f'@{ctx.author.name}'
        else:
            reporter = f'{ctx.author.name}#{ctx.author.discriminator}'
        embed = discord.Embed(title=f'A new user has been reported by {reporter}!',description=f'reason',color=0xffcc00,timestamp=datetime.utcnow())
        set_author(embed,name=reporter,icon_url=ctx.author.avatar)

        embed.add_field(name='User reported:',value=f'- :warning: user <@{target}> has been reported',inline=False)
        
        await ctx.send('user has been reported succesfully <:nevheh:990994050607906816>')
def setup(bot):
    bot.add_cog(reportereration(bot))
