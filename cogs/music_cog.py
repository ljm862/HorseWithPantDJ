import discord
from discord.ext import commands

from yt_dlp import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False
        self.vc = None

        self.music_queue = []
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
            return {'source': info['url'], 'title': info['title']}
        
    def load_next_video(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            url = self.music_queue[0]['source']
            print("url: %s" % url)
        return url
    
    def play_next_video(self):
        if len(self.music_queue) > 0:
            url = self.load_next_video()
            self.music_queue.pop(0)

            self.play_music(url)
        else:
            self.is_playing = False
    
    def play_music(self, url):
        self.vc.play(discord.FFmpegPCMAudio(url, **self.ffmpeg_options), after=lambda e: self.play_next_video())
        
    async def start_playing(self, ctx):
        if len(self.music_queue) > 0:
            url = self.load_next_video()

            #Check if connected to channel
            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()
                print("joined vc")

                if self.vc ==None:
                    await ctx.send("Unable to join channel")
                    return
            # Maybe else here to move to the called channel?

            self.music_queue.pop(0)
            self.play_music(url)
            

    @commands.command(name="play", aliases=['p'], help="Play the song from youtube")
    async def command_play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send("First join a voice channel")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.find_video(query)
            if type(song) == type(True):
                await ctx.send("Couldn't find the video")
            else:
                self.music_queue.append(song)
                await ctx.send("Added: %s to the queue at position %s" % (query, len(self.music_queue)))

                if self.is_playing == False:
                    await self.start_playing(ctx)

    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx, *args):
        #TODO
        print("todo")

    @commands.command(name="resume", aliases=["r"], help="Resumes the current song")
    async def resume(self, ctx, *args):
        #TODO
        print("todo")

    @commands.command(name="skip", aliases=["next", "s"], help="Skips the current song")
    async def skip(self, ctx, *args):
        #TODO
        print("todo")


    @commands.command(name="clear", help="Clears the queue")
    async def clear(self,ctx, *args):
        #TODO
        print("todo")

    @commands.command(name="queue", aliases=["list"], help="Displays the list of songs in order")
    async def queue(self, ctx, *args):
        #TODO
        print("todo")


    @commands.command(name="stop", aliases=["quit", "leave", "disconnect"], help="Kicks the bot from the channel")
    async def stop(self, ctx, *args):
        #TODO
        print("todo")
