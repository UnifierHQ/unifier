<h1 align=center>
  <img width=64 src=https://github.com/greeeen-dev/unifier/assets/41323182/3065245a-28b6-4410-9b07-8b940f4796ae><br>
Unifier</h1>
<p align=center>A sophisticated Discord bot uniting servers and platforms, brought to you by Green and ItsAsheer<br>
Inspired by matrix-t2bot</p>

## What is Unifier?
Unifier is a bot written in Python which allows users to connect their Discord servers together to form one big chat room. 
It is also compatible with Revolt and Guilded with support extensions, meaning that it can also be used as a bridge bot to 
connect servers from different platforms together.

## Features
### Basic features
Like most bridge bots, Unifier has basic commands such as link, unlink, etc., so you can do most of what you'd need to do 
all on your messaging app of choice.

### Fast and responsive bridge
Using threading and optimizations, Unifier is able to bridge messages at speeds up to 20.3 messages a second, so nobody needs 
to wait to see your message.

### Revolt and Guilded support
With [Revolt](https://github.com/greeeen-dev/unifier-revolt) and [Guilded](https://github.com/greeeen-dev/unifier-guilded) 
support extensions, you can bring your communities outside of Discord together, or get a break from Discord without losing 
your community.

### Moderation commands
After you assign bot admins, they can assign moderators, who can help moderate the chat and take action against bad actors. 
Server moderators can also block members and servers from bridging messages to their servers should they find it necessary.

### And more!
- **Message cache backups**: Unifier's message cache is backed up on graceful shutdowns, so it remembers message IDs between
reboots for replying, editing, and deleting.
- **Message reporting**: Users can report messages to Unifier moderators, so they can more easily take action against bad
actors.
- **Database-free**: No need to get a database up and running. Everything is stored locally on the same system you use to run 
Unifier, so the performance is not impacted by slow 10k+ ping database servers.
- **External bridge support**: Unifier supports external bridge services like [matrix-t2bot](https://github.com/t2bot/matrix-appservice-discord), 
so you can connect platforms beyond what we can cover and avoid reconfiguring too much.

## Setup
Please follow our guides on GitBook to set up Unifier.

- [If you're using the official Unifier client](https://unichat-wiki.pixels.onl/setup/getting-started)

- [If you're hosting your own Unifier client](https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started)

## License
Unifier is licensed under the AGPLv3. If you wish to use its source code, please read the license carefully before doing so.

## Acknowledgments
We want to thank:
- [**Voxel Fox**](https://github.com/Voxel-Fox-Ltd), for continuing the discord.py project as Novus when it was discontinued (it
  is now re-continued, but for now we'd like to use Novus)
- [**Rapptz**](https://github.com/Rapptz) and [**discord.py**](https://github.com/Rapptz/discord.py) developers, for creating the
  discord.py library Novus is based on
- [**Revolt**](https://github.com/revoltchat), for creating revolt.py and an awesome open-source Discord alternative
- [**shayypy**](https://github.com/shayypy), for creating guilded.py

We also use the logging logger formatting code from discord.py, which is licensed under the MIT license. You can find more info in 
the `EXTERNAL_LICENSES.txt` file.

## Special thanks
As the project founder and leader, I want to give my special thanks to:
- [**ItsAsheer/NullyIsHere**](https://github.com/NullyIsHere), for joining the team and helping me fix my shitty Python and
  adding a lot of amazing features to Unifier
- **My best friend**, for turning my life around for the better and always supporting me even at my worst

And lastly but *most importantly*, **the late role model of mine I used to know very well**: He's the one that brought me and my 
best friend together, as well as lots of other people together as well. Without him, I don't know if Unifier would have even existed, 
so I want to pick up where he left off and continue uniting people in his honor. I dedicate this project to him by open sourcing the 
code, so people can use it to bring people together just like how he did.

In return, we expect that all users honor those who made this project possible use the code **responsibly**. Please do not organize 
any hate groups or whatever with Unifier.

## Note
Unifier's icon was co-created by @green. and @thegodlypenguin on Discord.

Unifier and UnifierHQ developers are not affiliated or associated with, or endorsed by Discord Inc., Guilded Inc. and Revolt.
