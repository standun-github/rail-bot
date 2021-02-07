import discord
from discord.ext import commands
from queue import Queue
import asyncio
from threading import Thread
import concurrent.futures

# enter ur own server token
TOKEN = "NzkzNTc2OTQxNzUyMDI1MTM5.X-uSHg._AGZGP3oNkVHmzBvCOEcKQ6GpFM"

client = commands.Bot(command_prefix="")
inputq = Queue()
outputq = Queue()

show_link = False
url_link = ""

def set_URL(link_string):
    global url_link
    global show_link

    url_link = link_string
    show_link = True

def init():
    loop = asyncio.get_event_loop()
    # print("p3")
    loop.create_task(client.start(TOKEN))
    # print("p4")
    thread = Thread(target=loop.run_forever)
    # print("p5")
    thread.start()

@client.event
async def on_ready():
    print("QueueBot is ready")
    await sendOutQ()

@client.event
async def on_message(message):
    if (message.author.bot):
        return
    else:
        # enter your own text channel ID
        general_channel = client.get_channel(793577994986717194)
        user_input = message.content
        inputq.put(user_input)

async def sendOutQ():
    global show_link
    loop = asyncio.get_running_loop()
    # print("s0")
    general_channel = client.get_channel(793577994986717194)
    # print("s1")
    while True:
        # print("s2")
        with concurrent.futures.ThreadPoolExecutor() as pool:

            result = await loop.run_in_executor(pool, outputq.get)
            await general_channel.send("`" + result + "`")
            if show_link:
                general_embed = discord.Embed(title="Book Now", description="nationalrail.com",url=url_link)
                await general_channel.send(embed=general_embed)
                show_link = False


init()
