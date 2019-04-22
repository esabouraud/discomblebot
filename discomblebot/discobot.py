import asyncio
import discord
import queue

client = discord.Client()
channel_id = None
channel = None

@client.event
async def on_ready():
    global channel
    print("We have logged in as {0.user}".format(client))
    channel = client.get_channel(channel_id)
    print("Output channel is '%s'" % channel)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

async def read_queue(dm_queue):
    global channel
    while True:
        try:
            str = dm_queue.get_nowait()
            #print("data read from queue: %s" % str)
            if channel:
                await channel.send(str)
        except queue.Empty:
            pass
        await asyncio.sleep(1)

def run(dm_queue, config):
    global channel_id
    channel_id = int(config.channel)
    client.loop.create_task(read_queue(dm_queue))
    client.run(config.token)