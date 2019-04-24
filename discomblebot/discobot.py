import asyncio
import concurrent.futures
import discord
import re

client = discord.Client()
channel_id = None
channel = None

CMDE_RX = re.compile("^\\$([^\\s]+).*$")
otherbot_cmd_queue = None


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

    if message.content.startswith("$"):
        match_cmd = CMDE_RX.match(message.content)
        if match_cmd:
            cmd = match_cmd.group(1)
            if cmd == "hello":
                await message.channel.send("Hello %s!" % message.author)
            elif cmd == "status":
                otherbot_cmd_queue.put_nowait("status")
            else:
                await message.channel.send("I do not understand this command.")

async def read_comm_queue(comm_queue):
    global channel
    while channel is None:
        await asyncio.sleep(1)
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            mumble_msg = await client.loop.run_in_executor(pool, comm_queue.get)
            print("Discord bot read data from queue: %s" % mumble_msg)
            if channel:
                await channel.send(mumble_msg)

async def read_cmd_queue(cmd_queue):
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            cmd_msg = await client.loop.run_in_executor(pool, cmd_queue.get)
            if cmd_msg == "quit":
                print("Discord bot stopping on command: %s" % cmd_msg)
                # Does not seem to make client.run() stop
                await client.close()
                break
            else:
                print("Discord bot unknown command: %s" % cmd_msg)

def run(comm_queue, cmd_queue, mumbot_cmd_queue, config):
    global channel_id
    global otherbot_cmd_queue
    otherbot_cmd_queue = mumbot_cmd_queue
    channel_id = int(config.channel)
    client.loop.create_task(read_comm_queue(comm_queue))
    client.loop.create_task(read_cmd_queue(cmd_queue))
    try:
        client.run(config.token)
    except KeyboardInterrupt:
        print("Discord bot stopping on its own")
    print("Discord bot final goodbye")
