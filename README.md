<h1 align=center>
  <img width=64 src=https://github.com/UnifierHQ/unifier/assets/41323182/3065245a-28b6-4410-9b07-8b940f4796ae><br>
Unifier</h1>
<p align=center>A cross-server and cross-platform bridge bot that works just as fast as you can type 🚀</p>
<p align=center><a href='#-setup'>🔧 Setup</a> •
  <a href='https://wiki.unifierhq.org'>📘 Wiki</a> • <a href='#%EF%B8%8F-support'>⛑️ Support</a></sub>

## ✨ Meet Unifier!
Unifier is a versatile and performant bridge bot built for communities across platforms.

## 🎨 Features
### Basic features
Like most bridge bots, Unifier has basic commands such as link, unlink, etc., so you can do most of what you'd need to do 
all on your messaging app of choice.

### Fast and responsive bridge
Using threading and optimizations, Unifier has been tested to be able to send up to 33 messages a second through webhooks, so 
nobody needs to wait to see your messages. Do note that this speed will vary depending on lots of factors.
###### * Performance may vary depending on factors such as system resources and network speed.

### External platforms support
With support for external platforms, you can bring your communities outside of Discord together, or get a break from Discord 
without losing your community. Unifier supports virtually any platform with the help of support Plugins, so the possibilities
are endless.

We've written a platform support Plugin for [Revolt](https://github.com/UnifierHQ/unifier-revolt), so give that a try!

### Moderation commands
After you assign bot admins, they can assign moderators, who can help moderate the chat and take action against bad actors. 
Server moderators can also block members and servers from bridging messages to their servers should they find it necessary.

### And more!
- **Message cache backups**: Unifier's message cache is backed up on graceful shutdowns, so it remembers message IDs between
  reboots for replying, editing, and deleting.
- **Easy management**: Unifier comes with a built-in upgrader, so upgrading your instance is a breeze. Even new configuration
  keys are added automatically, so you don't have to worry about them.
- **Message reporting**: Users can report messages to Unifier moderators, so they can more easily take action against bad
  actors.
- **Plugins support**: Anyone can always code and install plugins for Unifier to extend its functionality. If you need help
  making your own plugin, you can always use our [template](https://github.com/UnifierHQ/unifier-plugin).
- **Portable data**: Everything is stored locally on-disk, so it's easy to transfer data if needed.

## 📚 Setup
Please follow our guides on GitBook to set up Unifier.

- [If you're using an existing Unifier client](https://unichat-wiki.pixels.onl/setup/getting-started)

- [If you're hosting your own Unifier client](https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started)

### Managing updates
Unifier comes with a built-in upgrader. Please refer to [this 
guide](https://wiki.unifierhq.org/setup-selfhosted/upgrading-unifier) to learn how to manage Unifier updates.

### Revolt and Guilded support
To install support plugins for Revolt and Guilded, please refer to [this 
guide](https://wiki.unifierhq.org/setup-selfhosted/getting-started/unifier#installing-revolt-support) for Revolt, and
[this guide](https://wiki.unifierhq.org/setup-selfhosted/getting-started/unifier#installing-guilded-support) for Guilded.

## 📜 License
Unifier is licensed under the AGPLv3. If you wish to use its source code, please read the license carefully before doing so.

## ⛑️ Support
Need support? We're always available at our [Discord server](https://discord.unifierhq.org).

### Version matrix
All EoL dates are in dd/mm/yyyy format.
| Version                        | Type     | Supported                    | Status   | EoL        |
| ------------------------------ | -------- | ---------------------------- | -------- | ---------- |
| 4.x (`fearless-feijoa`)        | dev      | :wrench: In development      | feature  | TBD        |
| 3.x (`elegant-elderberry`)     | release  | :white_check_mark: Supported | feature  | TBD        |
| 2.x LTS (`daring-dragonfruit`) | legacy   | :white_check_mark: Supported | security | 17/07/2025 |
| 1.2.x (`cheerful-cranberry`)   | eol      | :x: Unsupported              | eol      | 05/12/2024 |
| 1.1.x (`brave-blueberry`)      | eol      | :x: Unsupported              | eol      | 05/07/2024 |
| 1.0.x (`adept-apricot`)        | eol      | :x: Unsupported              | eol      | unknown    |

## 🙏 Acknowledgments
We want to thank:
- [**Nextcord**](https://github.com/nextcord), for continuing the discord.py project as Nextcord when it was discontinued, and also
  supporting context menu commands in a Cog
- [**Voxel Fox**](https://github.com/Voxel-Fox-Ltd), for continuing the discord.py project as Novus when it was discontinued, which
  is the library we used to use until we moved to Nextcord
- [**Rapptz**](https://github.com/Rapptz) and [**discord.py**](https://github.com/Rapptz/discord.py) developers, for creating the
  discord.py library Novus and Nextcord are based on
- [**Revolt**](https://github.com/revoltchat), for creating revolt.py and an awesome open-source Discord alternative
- [**shayypy**](https://github.com/shayypy), for creating guilded.py

We also use the logging logger formatting code from discord.py, which is licensed under the MIT license. You can find more info in 
the `EXTERNAL_LICENSES.txt` file.

## 🫂 Special thanks
As the project founder and leader, I want to give my special thanks to:
- [**The entire UnifierHQ team**](https://github.com/UnifierHQ), for helping me make Unifier what it is today
- [**ItsAsheer/NullyIsHere**](https://github.com/NullyIsHere), for helping me fix my shitty Python during the early says of the
  project
- [**Ente Community**](https://github.com/ente-io), for offering me invaluable advice for open sourcing this project
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
