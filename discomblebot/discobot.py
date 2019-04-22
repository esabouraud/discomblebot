import sys
import queue
import asyncio
import concurrent.futures
import discord

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

async def read_comm_queue(comm_queue):
    global channel
    while channel is None:
        await asyncio.sleep(1)
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            str = await client.loop.run_in_executor(pool, comm_queue.get)
            print("data read from queue: %s" % str)
            if channel:
                await channel.send(str)

async def read_cmd_queue(cmd_queue):
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            str = await client.loop.run_in_executor(pool, cmd_queue.get)
            if str == "quit":
                print("Discord bot stopping on command: %s" % str)
                # Does not seem to make client.run() stop
                await client.close()
                break
            else:
                print("Discord bot unknown command: %s" % str)

def run(comm_queue, cmd_queue, config):
    global channel_id
    channel_id = int(config.channel)
    client.loop.create_task(read_comm_queue(comm_queue))
    client.loop.create_task(read_cmd_queue(cmd_queue))
    try:
        client.run(config.token)
    except KeyboardInterrupt:
        print("Discord bot stopping on its own")
    print("Discord bot final goodbye")