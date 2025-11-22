"""Discord-Youtube player and discord bot cog housing script with Premium UI
"""

import os
import asyncio
import discord
from discord.ext import commands
from discord.ui import Button, View
from .yt_utils import download


class MusicControlView(View):
    """Premium UI with interactive buttons for music control"""
    
    def __init__(self, player, guild_id):
        super().__init__(timeout=None)
        self.player = player
        self.guild_id = guild_id
    
    # @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.secondary, custom_id="pause_btn")
    # async def pause_button(self, interaction: discord.Interaction, button: Button):
    #     """Pause/Resume the current track"""
    #     # Note: Implement pause/resume functionality in YoutubeDiscordPlayer if needed
    #     await interaction.response.send_message("⏸️ Pause feature coming soon!", ephemeral=True)
    
    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.primary, custom_id="skip_btn")
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        """Skip the current track"""
        if self.guild_id in self.player and len(self.player[self.guild_id].queue) > 0:
            current = self.player[self.guild_id].queue[0]
            self.player[self.guild_id].skip()
            
            embed = discord.Embed(title="⏭️ Skipped", color=0x00ff00)
            embed.add_field(
                name=current["download_data"]["title"], 
                value=f"[Link]({current['url']})",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing playing!", ephemeral=True)
    
    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.danger, custom_id="stop_btn")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        """Stop playback and clear queue"""
        if self.guild_id in self.player:
            await self.player[self.guild_id].stop()
            embed = discord.Embed(title="⏹️ Stopped", description="Queue cleared!", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing playing!", ephemeral=True)
    
    @discord.ui.button(label="📋 Queue", style=discord.ButtonStyle.secondary, custom_id="queue_btn")
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        """Show current queue"""
        if self.guild_id not in self.player or len(self.player[self.guild_id].queue) == 0:
            embed = discord.Embed(title="📋 Queue", description="No items in queue", color=0x808080)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            queue_text = ""
            for index, item in enumerate(self.player[self.guild_id].queue[:10]):  # Show max 10
                status = "▶️" if index == 0 else f"{index}."
                queue_text += f"{status} **{item['download_data']['title']}**\n"
            
            embed = discord.Embed(title="📋 Current Queue", description=queue_text, color=0x3498db)
            if len(self.player[self.guild_id].queue) > 10:
                embed.set_footer(text=f"And {len(self.player[self.guild_id].queue) - 10} more...")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)


class YoutubeDiscordPlayer:
    """Class for keeping track of youtube music/sound queue"""

    def __init__(self):
        self.queue = []
        self.is_playing = False
        self.is_stopping = False
        self.skip_song = False

    def _can_play(self, queue_item) -> bool:
        if (
            "channel" in queue_item
            and "download_data" in queue_item
            and "file" in queue_item["download_data"]
        ):
            return True
        return False

    def add(self, url, channel, download_data, context=None, interaction=None):
        """Add song to queue"""
        self.queue.append(
            {
                "url": url,
                "context": context,
                "channel": channel,
                "download_data": download_data,
                "interaction": interaction,
            }
        )

    def skip(self):
        """Sets skip_song which gets checked while song is running"""
        self.skip_song = True

    async def start(self):
        """Starts playing from the queue. Ends once the queue is empty"""
        self.is_playing = True
        self.is_stopping = False

        while len(self.queue) != 0:
            next_video = self.queue[0]
            if self._can_play(next_video):
                await self.play_and_pop(next_video)

        self.is_playing = False

    async def stop(self):
        """Stops the queue and resets"""
        self.queue = []
        self.is_stopping = True
        self.is_playing = False
        self.skip_song = True

    async def play_and_pop(self, play_info):
        """Plays audio file from play_info and then removes from the queue"""
        file = play_info["download_data"]["file"]
        if not os.path.exists(file):
            download_data = await download(play_info["url"])
            file = download_data["file"]

        vc = await play_info["channel"].connect()
        source = discord.FFmpegPCMAudio(file)

        try:
            vc.play(source)
            while vc.is_playing():
                if self.skip_song:
                    vc.stop()
                    self.skip_song = False
                await asyncio.sleep(1.0)
        except Exception as e:
            print(e)
        finally:
            if not self.is_stopping:
                self.queue.pop(0)

            files = [
                item["download_data"]["file"]
                for item in self.queue
                if self._can_play(item)
            ]
            if not file in files:
                os.remove(file)

            await vc.disconnect()


class YoutubeCommands(commands.Cog):
    """Youtube Bot Cog with Premium UI"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}

    def create_premium_embed(self, download_data, user, action="Added to Queue"):
        """Create a premium styled embed with thumbnail"""
        embed = discord.Embed(
            title=f"🎵 {action}",
            description=f"**{download_data['title']}**",
            color=0x9b59b6,
            url=download_data['url']
        )
        
        embed.set_author(
            name=user.display_name,
            icon_url=user.display_avatar.url
        )
        
        # Add thumbnail if available
        if 'thumbnail' in download_data and download_data['thumbnail']:
            embed.set_thumbnail(url=download_data['thumbnail'])
        
        # Add video details
        if 'duration' in download_data:
            embed.add_field(name="⏱️ Duration", value=download_data['duration'], inline=True)
        if 'uploader' in download_data:
            embed.add_field(name="👤 Uploader", value=download_data['uploader'], inline=True)
        
        embed.set_footer(text="Music Player • Use buttons below to control playback")
        
        return embed

    async def _get_channel_by_context(
        self, context: commands.Context, channel_name: commands.clean_content = None
    ):
        try:
            if channel_name is None:
                channel = context.author.voice.channel
            else:
                channels = context.guild.channels
                channel = next(
                    c
                    for c in channels
                    if c.name == channel_name and isinstance(c, discord.VoiceChannel)
                )
            return channel
        except StopIteration:
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value=f"Failed to find voice channel named `{channel_name}`",
            )
            await context.send(embed=embed)
            return None
        except AttributeError:
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Either join a channel or specify one after the url",
            )
            await context.send(embed=embed)
            return None
        except Exception as ex:
            print(type(ex), ex.args, ex)
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            embed.add_field(name="Failure", value="UNKNOWN ISSUE")
            await context.send(embed=embed)
            return None

    async def _get_channel_by_interaction(
        self, interaction: discord.Interaction, channel_name: str = None
    ):
        try:
            if channel_name is None:
                channel = interaction.user.voice.channel
            else:
                channels = interaction.guild.channels
                channel = next(
                    c
                    for c in channels
                    if c.name == channel_name and isinstance(c, discord.VoiceChannel)
                )
            return channel
        except StopIteration:
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value=f"Failed to find voice channel named `{channel_name}`",
            )
            await interaction.followup.send(embed=embed)
            return None
        except AttributeError:
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(
                name="Failure",
                value="Either join a channel or specify one after the url",
            )
            await interaction.followup.send(embed=embed)
            return None
        except Exception as ex:
            print(type(ex), ex.args, ex)
            embed = discord.Embed(title="❌ Failed to add to queue", color=0xe74c3c)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            embed.add_field(name="Failure", value="UNKNOWN ISSUE")
            await interaction.followup.send(embed=embed)
            return None

    ### SYNC SECTION ###

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, sync_type: str) -> None:
        """Sync the application commands"""
        async with ctx.typing():
            if sync_type == "guild":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Berhasil Synced guild Beb !")
                return
            await self.bot.tree.sync()
            await ctx.reply(f"Berhasil Synced global Beb !")

    @commands.command()
    @commands.is_owner()
    async def unsync(self, ctx: commands.Context, unsync_type: str) -> None:
        """Unsync the application commands"""
        async with ctx.typing():
            if unsync_type == "guild":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Un-Synced guild !")
                return
            self.bot.tree.clear_commands()
            await self.bot.tree.sync()
            await ctx.reply(f"Un-Synced global !")

    ### PLAY SECTION ###

    @commands.command(
        name="play",
        description="Play Youtube audio lewat url beb",
        help="Play Youtube audio lewat url beb",
        usage="!steve play <url> <target_channel?>",
    )
    async def play(
        self, context: commands.Context, url: str, *, channel_name: str = None
    ):
        """Play YouTube audio with premium UI"""
        guild_id = context.author.guild.id

        channel = await self._get_channel_by_context(context, channel_name)
        if channel is None:
            return

        download_data = await download(url, str(guild_id))

        # Create premium embed with thumbnail
        embed = self.create_premium_embed(download_data, context.author)
        
        # Create control view
        view = MusicControlView(self.players, guild_id)
        
        await context.send(embed=embed, view=view)

        if guild_id not in self.players:
            self.players[guild_id] = YoutubeDiscordPlayer()

        self.players[guild_id].add(
            url=download_data["url"],
            channel=channel,
            download_data=download_data,
            context=context,
            interaction=None,
        )
        if not self.players[guild_id].is_playing:
            await self.players[guild_id].start()

    @discord.app_commands.command(
        name="p",
        description="Play Youtube audio lewat url beb",
    )
    @discord.app_commands.describe(url="url", channel_name="channel name")
    async def qplay(
        self, interaction: discord.Interaction, url: str, channel_name: str = None
    ):
        """Play YouTube audio with premium UI (slash command)"""
        await interaction.response.defer()
        guild_id = interaction.guild.id

        channel = await self._get_channel_by_interaction(interaction, channel_name)
        if channel is None:
            return

        download_data = await download(url, str(guild_id))

        # Create premium embed with thumbnail
        embed = self.create_premium_embed(download_data, interaction.user)
        
        # Create control view
        view = MusicControlView(self.players, guild_id)
        
        await interaction.followup.send(embed=embed, view=view)

        if guild_id not in self.players:
            self.players[guild_id] = YoutubeDiscordPlayer()

        self.players[guild_id].add(
            url=download_data["url"],
            channel=channel,
            download_data=download_data,
            context=None,
            interaction=interaction,
        )
        if not self.players[guild_id].is_playing:
            await self.players[guild_id].start()

    ### STOP SECTION ###

    @commands.command(name="stop", help="Stops semua musik yang lagi diputar termasuk kuewe beb")
    async def stop(self, context: commands.Context):
        """Stops all and clears queue"""
        embed = discord.Embed(title="⏹️ Stopping Playback", color=0xe74c3c)
        embed.set_author(
            name=context.author.display_name, icon_url=context.author.display_avatar.url
        )
        embed.description = "Queue cleared and playback stopped"
        await context.send(embed=embed)

        guild_id = context.author.guild.id
        if guild_id in self.players:
            await self.players[guild_id].stop()

    @discord.app_commands.command(
        name="st", description="Stops semua musik yang lagi diputar termasuk kuewe beb"
    )
    async def qstop(self, interaction: discord.Interaction):
        """Stops all and clears queue (slash command)"""
        await interaction.response.defer()
        embed = discord.Embed(title="⏹️ Stopping Playback", color=0xe74c3c)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.description = "Queue cleared and playback stopped"
        await interaction.followup.send(embed=embed)

        guild_id = interaction.user.guild.id
        if guild_id in self.players:
            await self.players[guild_id].stop()

    ### SKIP SECTION ###

    @commands.command(name="skip", help="Skips current musik yang lagi diputar beb")
    async def skip(self, context: commands.Context):
        """Skips current audio playing in the queue"""
        guild_id = context.author.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            embed = discord.Embed(title="❌ Nothing in Queue", color=0x95a5a6)
            embed.set_author(
                name=context.author.display_name,
                icon_url=context.author.display_avatar.url,
            )
            await context.send(embed=embed)
            return

        current = self.players[guild_id].queue[0]
        download_data = current["download_data"]
        url = current["url"]
        
        embed = discord.Embed(title="⏭️ Skipping Track", color=0x3498db)
        embed.set_author(
            name=context.author.display_name,
            icon_url=context.author.display_avatar.url,
        )
        embed.add_field(name=download_data["title"], value=f"[Link]({url})", inline=False)
        
        if 'thumbnail' in download_data and download_data['thumbnail']:
            embed.set_thumbnail(url=download_data['thumbnail'])
        
        await context.send(embed=embed)
        self.players[guild_id].skip()

    @discord.app_commands.command(name="sk", description="Skips current musik yang lagi diputar beb")
    async def qskip(self, interaction: discord.Interaction):
        """Skips current audio playing in the queue (slash command)"""
        await interaction.response.defer()
        guild_id = interaction.user.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            embed = discord.Embed(title="❌ Nothing in Queue", color=0x95a5a6)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            await interaction.followup.send(embed=embed)
            return

        current = self.players[guild_id].queue[0]
        download_data = current["download_data"]
        url = current["url"]
        
        embed = discord.Embed(title="⏭️ Skipping Track", color=0x3498db)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name=download_data["title"], value=f"[Link]({url})", inline=False)
        
        if 'thumbnail' in download_data and download_data['thumbnail']:
            embed.set_thumbnail(url=download_data['thumbnail'])
        
        await interaction.followup.send(embed=embed)
        self.players[guild_id].skip()

    ### QUEUE SECTION ###

    @commands.command(name="queue", help="Nunjukin kuewe ada sekarang beb")
    async def queue(self, context: commands.Context):
        """Gets current queue with premium UI"""
        guild_id = context.author.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            embed = discord.Embed(title="📋 Queue", color=0x95a5a6)
            embed.add_field(name="Empty", value="No items in queue")
            await context.send(embed=embed)
        else:
            for index, item in enumerate(self.players[guild_id].queue):
                status = "▶️ Now Playing" if index == 0 else f"#{index} in Queue"
                embed = discord.Embed(title=f"📋 {status}", color=0x9b59b6)
                embed.set_author(
                    name=context.author.display_name,
                    icon_url=context.author.display_avatar.url,
                )
                
                if 'thumbnail' in item["download_data"] and item["download_data"]['thumbnail']:
                    embed.set_thumbnail(url=item["download_data"]['thumbnail'])
                
                embed.add_field(
                    name="🎵 Title", value=item["download_data"]["title"], inline=False
                )
                embed.add_field(name="🔗 URL", value=f"[Link]({item['url']})", inline=False)
                embed.add_field(
                    name="🔊 Voice Channel",
                    value=f"`{item['channel'].name}`",
                    inline=False
                )
                await context.send(embed=embed)

    @discord.app_commands.command(name="q", description="Nunjukin kuewe yang ada sekarang beb")
    async def qqueue(self, interaction: discord.Interaction):
        """Gets current queue with premium UI (slash command)"""
        await interaction.response.defer()
        guild_id = interaction.user.guild.id

        if guild_id not in self.players or len(self.players[guild_id].queue) == 0:
            embed = discord.Embed(title="📋 Queue", color=0x95a5a6)
            embed.add_field(name="Empty", value="No items in queue")
            await interaction.followup.send(embed=embed)
        else:
            embeds = []
            for index, item in enumerate(self.players[guild_id].queue):
                status = "▶️ Now Playing" if index == 0 else f"#{index} in Queue"
                embed = discord.Embed(title=f"📋 {status}", color=0x9b59b6)
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url,
                )
                
                if 'thumbnail' in item["download_data"] and item["download_data"]['thumbnail']:
                    embed.set_thumbnail(url=item["download_data"]['thumbnail'])
                
                embed.add_field(
                    name="🎵 Title",
                    value=item["download_data"]["title"],
                    inline=False,
                )
                embed.add_field(name="🔗 URL", value=f"[Link]({item['url']})", inline=False)
                embed.add_field(
                    name="🔊 Voice Channel",
                    value=f"`{item['channel'].name}`",
                    inline=False
                )
                embeds.append(embed)
            await interaction.followup.send(embeds=embeds)


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog"""
    await bot.add_cog(YoutubeCommands(bot))