"""Discord bot
  - executes CLI commands and responds to chat commands
  - sends messages to be written on Mumble
  - displays messages coming from Mumble bot."""

import asyncio
import concurrent.futures
import re
import discord

from discomblebot import confbot
from discomblebot import commonbot

client = discord.Client()
channel_id = None
channel = None

otherbot_comm_queue = None


@client.event
async def on_ready():
    """Finalize bot connection to Discord"""
    global channel
    print("We have logged in as {0.user}".format(client))
    channel = client.get_channel(channel_id)
    print("Output channel is '%s'" % channel)

@client.event
async def on_message(message):
    """Handle chat user commands sent in Discord"""
    if message.author == client.user:
        return
    cmd = commonbot.parse_message(message.content)
    if cmd is None:
        return
    if cmd == commonbot.HELLO_CMD:
        await message.channel.send("Hello %s!" % message.author)
    elif cmd == commonbot.VERSION_CMD:
        await message.channel.send("Current version: %s" % confbot.VERSION)
    elif cmd == commonbot.STATUS_CMD:
        otherbot_comm_queue.put_nowait("!status")
    else:
        await message.channel.send("I do not understand this command.")

async def read_comm_queue(comm_queue):
    """Read queue expecting Mumble-bot issued messages or CLI commands (start with !).
    Read operation is blocking, so run in a dedicated executor."""
    global channel
    while channel is None:
        await asyncio.sleep(1)
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            mumble_msg = await client.loop.run_in_executor(pool, comm_queue.get)
            if mumble_msg.startswith("!"):
                cmd_msg = mumble_msg[1:]
                if cmd_msg == "quit":
                    print("Discord bot stopping on command: %s" % cmd_msg)
                    # Does not seem to make client.run() stop
                    await client.close()
                    break
                elif cmd_msg == "status":
                    #print(client.users)
                    voice_channels = [channel for channel in client.get_all_channels() if isinstance(channel, discord.VoiceChannel)]
                    voice_members = [member.name for channel in voice_channels for member in channel.members]
                    status_str = "%d users (%s) are connected on the Discord server" % (
                        len(voice_members),
                        ", ".join(voice_members))
                    print(status_str)
                    otherbot_comm_queue.put_nowait(status_str)
                else:
                    print("Discord bot unknown command: %s" % cmd_msg)
            else:
                print("Discord bot read data from queue: %s" % mumble_msg)
                if channel:
                    await channel.send(mumble_msg)


def run(comm_queue, mumbot_comm_queue, config):
    """Launch Discord bot
    comm_queue is used to receive CLI commands and messages from Mumble bot
    mumbot_comm_queue is used to send messages to Mumble bot
    config contains the server parameters"""

    global channel_id
    global otherbot_comm_queue
    otherbot_comm_queue = mumbot_comm_queue
    channel_id = int(config.channel)
    client.loop.create_task(read_comm_queue(comm_queue))
    try:
        client.run(config.token)
    except KeyboardInterrupt:
        print("Discord bot stopping on its own")
    print("Discord bot final goodbye")
