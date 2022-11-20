from asyncio.windows_events import NULL
from queue import Empty
from time import sleep
from typing import Optional
import discord
import youtube_dl
from discord.ext import commands
from discord import app_commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer

import asyncio


song_queue = []
NowPlaying = ""
song_info = Empty
duration = 0
songtitle = ""

ydl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'auto',
    'noplaylist': 'True',
    'quiet': 'True',
    'no_warnings': 'True',
    #'matchtitle': 'True',
    'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredquality': '251',
    }],
    }

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
    }

#BOT SHIT




def run_discord_bot():
    TOKEN = ''
    intents = discord.Intents.all()
    intents.message_content = True
    intents.voice_states = True
    intents.guild_messages = True
    

    bot = commands.Bot(command_prefix='?', intents=intents)

    ydl = youtube_dl.YoutubeDL(ydl_opts)
    newLine = "\n"

    @bot.event
    async def on_ready():
        await bot.change_presence(activity = discord.Game('with your mom'))

        print(f'{bot.user} is now running!')
    
    


        
    def queued(ctx):
        global song_info
        global title
        global duration
        global NowPlaying

        if len(song_queue) > 0:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            NowPlaying = song_queue[0]
            song_info = ydl.extract_info(song_queue.pop(0), download=False)
            if 'entries' in song_info:
                source = discord.FFmpegOpusAudio(song_info['entries'][0]["url"], bitrate=256,**FFMPEG_OPTIONS)
                title = song_info['entries'][0]["title"]
                duration = song_info['entries'][0]["duration"]
            elif 'formats' in song_info:
                source = discord.FFmpegOpusAudio(song_info["formats"][0]["url"], bitrate=256,**FFMPEG_OPTIONS)
                title = song_info["title"]
                duration = song_info["duration"]
                
            voice.play(source, after = (lambda e: queued(ctx)))
    

    
    @bot.command()
    async def test(ctx, *args):
        arguments = ' '.join(args)
        await ctx.send(f'{len(args)} arguments: {arguments}')

 

            
        
    #bot playcommand, added aliases for plays and p. 
    @bot.command(name='play', help = 'Joins voice channel if necessary and plays the specified audio.', aliases=['plays', 'p'], arguments_help = 'Url to video')
    async def play(ctx, *keywords):
        url = " ".join(keywords)
        global song_queue
        global ydl_opts
        global FFMPEG_OPTIONS

        global duration
        global title

        #Checks if User is in voice channel
        if ctx.message.author.voice == None:
            await ctx.message.reply(f"No Voice Channel! You need to be in a voice channel to use this command! {ctx.author}")

        else:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            #checks if bot allready has a connected voice and either plays the song or waits for connection and tries again.
            if voice:
                
                voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

                #check if voice is playing
                if voice.is_playing():
                    #add to the queue if not allready in it
                    if song_queue.__contains__(url):
                        await ctx.message.reply(f"This Song is allready in the queue")
                    else:
                        song_queue.append(url)
                        song_info = ydl.extract_info(song_queue[-1], download=False)
                        if 'entries' in song_info:
                            title = song_info['entries'][0]["title"]
                        elif 'formats' in song_info:
                            title = song_info["title"]

                        
                        await ctx.message.reply(f"Added this song to the queue:{newLine}```{title}```{newLine}Place in queue: {len(song_queue)}")
                #else play the song        
                else:
                    song_queue.append(url) 
                    queued(ctx)

                    hours = (duration - ( duration % 3600))/3600
                    seconds_minus_hours = (duration - hours*3600)
                    minutes = (seconds_minus_hours - (seconds_minus_hours % 60) )/60
                    seconds = seconds_minus_hours - minutes*60
                    
                    await ctx.message.reply(f"Now playing {title}, Duration: {int(minutes)}:{int(seconds)}. ")
                    
            else:
                await connect(ctx)
                await play(ctx,url)


    
    @bot.command(name='skip', help = 'Skips the currently playing song for the next in line and stops playing if there is no queue left.', aliases=['s'])
    async def skip(ctx):
        global song_queue

        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        voice.stop()

        if len(song_queue) >0: 
            await ctx.message.reply(f"Skipped the song!") 
            queued(ctx)
        else:
            await ctx.send(f"Stopped playing because there are no songs in the queue.")




    
    @bot.command(name='queue', help = 'Displays the queue.', aliases=['queues', 'q'])
    async def queue(ctx):
        
        songs = (f"")
        if len(song_queue) > 0:
            for song in range(len(song_queue)):
                song_info = ydl.extract_info(song_queue[song], download=False,)
                if 'entries' in song_info:
                    title = song_info['entries'][0]["title"]
                elif 'formats' in song_info:
                    title = song_info["title"]
                    
                if song == 0:
                    songs += (f"Next in line:{newLine}{song+1}. {title}{newLine}")
                else:
                    songs += (f"{song+1}. {title}{newLine}")
            await ctx.message.reply(f"The current song:{newLine}```{NowPlaying}```The queue is:{newLine}```{songs}```")
        else:
            await ctx.message.reply(f"```The queue is empty.```")
    
    
    @bot.command(name='pause', help = 'Pauses the playing song.')
    async def pause(ctx):
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        elif ctx.message.author.voice == None:
            await ctx.message.reply(f"No Voice Channel! You need to be in a voice channel to use this command! {ctx.author}")
        
    @bot.command(name='resume', help = 'Resumes playing after pause.', aliases=['resumes', 'r'])
    async def resume(ctx):
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
        elif voice.is_playing():
            await ctx.message.reply(f"Audio is still playing! Audio needs to be paused to use this command {ctx.author}")
        elif ctx.message.author.voice == None:
            await ctx.message.reply(f"No Voice Channel! You need to be in a voice channel to use this command! {ctx.author}")


    @bot.command(name='disconnect', help = 'Disconnects the bot.', aliases=['disc'])
    async def disconnect(ctx):
        global song_queue
        song_queue = []
        await ctx.voice_client.disconnect()
        await ctx.message.reply(f"Disconnected")
    
    @bot.command(help = "Makes the bot connect to the voice channel, if not connected allready.")    
    async def connect(ctx):
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice:
            await ctx.message.reply(f"Allready in a channel: {voice.channel}")
        else:
            channel = ctx.message.author.voice.channel
            await channel.connect()
            
    
    # Remember to run your bot with your personal TOKEN
    bot.run(TOKEN)
