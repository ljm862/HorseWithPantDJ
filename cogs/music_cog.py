import discord
from discord.ext import commands

from yt_dlp import YoutubeDL

import asyncio

import validators

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False
        self.vc = None

        self.timeout_task = None
        self.timing_out = False

        self.music_queue = []
        self.current_song = None
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.yt_options = {'format': 'm4a/bestaudio.best', 'noplaylist': 'True', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]}


    def find_video(self, query):
        with YoutubeDL(self.yt_options) as ytdl:
            try:
                info = ytdl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
            except:
                print("Error retrieving video: [%s]" % query)
                return False
            #print(info['formats'])
            return {'source': info['url'], 'title': info['title'], 'id': info['id']}
        
    def load_next_video(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            url = self.music_queue[0]['source']
            #print("url: %s" % url)
        return url
    
    def play_next_video(self, ctx):
        if len(self.music_queue) > 0:
            url = self.load_next_video()
            self.current_song = self.music_queue.pop(0)
            asyncio.run_coroutine_threadsafe(self.send_playing_message(ctx), self.bot.loop)

            self.play_music(url, ctx)
        else:
            self.is_playing = False
            self.current_song = None
            if not self.timing_out:
                asyncio.run_coroutine_threadsafe(self.create_timeout(), self.bot.loop)

    async def create_timeout(self):
        # start a cancellable timeout
        self.timeout_task = asyncio.create_task(self.begin_timeout())
        await self.timeout_task

    async def begin_timeout(self):
            t = 600  # time in seconds for bot to timeout after being idle
            self.timing_out = True
            await asyncio.sleep(t)
            await self.disconnect()
            self.timing_out = False

    def cancel_timeout(self):
        if self.timing_out and self.timeout_task != None:
            self.timeout_task.cancel()
            self.timing_out = False

    def play_music(self, url, ctx):
        self.vc.play(discord.FFmpegPCMAudio(url, **self.ffmpeg_options), after=lambda e: self.play_next_video(ctx))
        
    async def start_playing(self, ctx):
        if len(self.music_queue) > 0:
            url = self.load_next_video()

            #Check if connected to channel
            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()
                print("joined vc")

                if self.vc == None:
                    await ctx.send("Unable to join channel")
                    return
            # Maybe else here to move to the called channel?

            self.current_song = self.music_queue.pop(0)
            await self.send_playing_message(ctx)
            self.play_music(url, ctx)

    async def send_playing_message(self, ctx):
            await ctx.send("Now playing: %s https://www.youtube.com/watch?v=%s" % (self.current_song['title'], self.current_song['id']))

    def is_url(self, query):
        return validators.url(query)

    def strip_url(self, url):
        if "&" in url:
            return url[:url.index("&")]
        return url

    @commands.command(name="play", aliases=['p'], help="Play the song from youtube")
    async def command_play(self, ctx, *args):
        query = " ".join(args)
        if self.is_url(query):
            query = self.strip_url(query)
        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send("First join a voice channel")
        elif self.is_paused:
            self.vc.resume()
        else:
            self.cancel_timeout()
            song = self.find_video(query)
            if type(song) == type(True):
                await ctx.send("Couldn't find the video")
            else:
                self.music_queue.append(song)
                if self.current_song != None:
                    await ctx.send("Added: %s https://www.youtube.com/watch?v=%s to the queue at position %s" % (song['title'], song['id'], len(self.music_queue)))

                if self.is_playing == False:
                    await self.start_playing(ctx)

    def resume_playing(self):
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()

    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.resume_playing()

    @commands.command(name="resume", aliases=["r"], help="Resumes the current song")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.resume_playing()

    @commands.command(name="skip", aliases=["next", "s"], help="Skips the current song")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            if self.current_song != None:
                skipped_song = self.current_song['title']
                await ctx.send(str(skipped_song) + " skipped")

    @commands.command(name="clear", help="Clears the queue")
    async def clear(self, ctx, *args):
        self.music_queue.clear()
        await ctx.send("Queue cleared")

    @commands.command(name="queue", aliases=["list"], help="Displays the list of songs in order")
    async def queue(self, ctx, *args):
        queue = ""
        x = 10 # number of songs in the queue to display
        for i in range(len(self.music_queue)):
            if i >= x:
                queue += f"{len(self.music_queue)-x} more songs in the queue"
                break
            queue += self.music_queue[i]['title'] + "\n"

        if queue != "":
            await ctx.send(queue)
        else:
            await ctx.send("Nothing in queue")

    @commands.command(name="stop", aliases=["quit", "leave", "disconnect"], help="Kicks the bot from the channel")
    async def stop(self, ctx, *args):
        await self.disconnect()

    async def disconnect(self):
        self.is_playing = False
        self.is_paused = False
        self.current_song = None
        self.music_queue.clear()
        await self.vc.disconnect()
