"""Discord bot
  - executes CLI commands and responds to chat commands
  - monitors actity and sends messages to be written on Mumble
  - displays messages coming from Mumble bot."""

import asyncio
import concurrent.futures
import discord

from discomblebot import confbot
from discomblebot import commonbot
from discomblebot.bot_msg_pb2 import BotMessage

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
    await status()

@client.event
async def on_message(message):
    """Handle chat user commands sent in Discord"""
    if message.author == client.user:
        return
    cmd = commonbot.parse_chat_message(message.content)
    if cmd is None:
        return
    if cmd == commonbot.HELLO_CMD:
        await message.channel.send("Hello %s !" % message.author)
    elif cmd == commonbot.VERSION_CMD:
        await message.channel.send("Current version: %s" % confbot.VERSION)
    elif cmd == commonbot.HELP_CMD:
        await message.channel.send(commonbot.get_chat_help_message())
    elif cmd == commonbot.STATUS_CMD:
        bot_message = BotMessage()
        bot_message.type = BotMessage.Type.STATUS
        bot_message.direction = BotMessage.Direction.REQUEST
        bot_message.source = BotMessage.Source.DISCORD
        if bot_message_str := commonbot.write_bot_message(bot_message):
            otherbot_comm_queue.put_nowait(bot_message_str)
    # elif cmd == commonbot.INVITE_CMD:
    #     sender = message.author
    #     recipient = commonbot.get_chat_cmd_param(message.content)
    #     await invite(commonbot.INVITE_BOTCMD, sender, recipient)
    else:
        await message.channel.send("I do not understand this command.")

@client.event
async def on_voice_state_update(member, before, after):
    """Monitor Discord voice join/leave activity"""
    if member == client.user:
        return
    activity_str = None
    if before.channel is None and after.channel is not None:
        activity_str = "User %s enabled voice on the Discord server" % member.name
    elif before.channel is not None and after.channel is None:
        activity_str = "User %s disabled voice on the Discord server" % member.name
    if activity_str:
        bot_message = BotMessage()
        bot_message.type = BotMessage.Type.ACTIVITY
        bot_message.direction = BotMessage.Direction.INFO
        bot_message.source = BotMessage.Source.DISCORD
        bot_message.text = activity_str
        if bot_message_str := commonbot.write_bot_message(bot_message):
            otherbot_comm_queue.put_nowait(bot_message_str)

async def status():
    """Respond to status command"""
    voice_channels = [
        channel for channel in client.get_all_channels()
        if isinstance(channel, discord.VoiceChannel)]
    voice_members = [member.name for channel in voice_channels for member in channel.members]
    status_str = "%d users (%s) are connected on the Discord server" % (
        len(voice_members),
        ", ".join(voice_members))
    print(status_str)
    bot_message = BotMessage()
    bot_message.type = BotMessage.Type.STATUS
    bot_message.direction = BotMessage.Direction.RESPONSE
    bot_message.source = BotMessage.Source.DISCORD
    bot_message.text = status_str
    if bot_message_str := commonbot.write_bot_message(bot_message):
        otherbot_comm_queue.put_nowait(bot_message_str)

async def invite(cmd, sender, recipient):
    """Invite mumble user to discord"""
    # Invites are channel-level, not guild-level, oddly enough
    channel_invite = await channel.create_invite(
        max_age=86400, max_uses=1, unique=True, reason="discomble")
    print(channel_invite)
    otherbot_comm_queue.put_nowait(
        "!%s|%s;%s;%s" % (cmd, sender, recipient, channel_invite.url))

async def read_comm_queue(comm_queue):
    """Read queue expecting Mumble-bot issued messages or CLI commands (start with !).
    Read operation is blocking, so run in a dedicated executor."""
    global channel
    while channel is None:
        await asyncio.sleep(1)
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            mumble_msg = await client.loop.run_in_executor(pool, comm_queue.get)
            if bot_message := commonbot.read_bot_message(mumble_msg):
                print("Discord bot: message received with type %d direction %s source %d" % (
                    bot_message.type, bot_message.direction, bot_message.source))
                if bot_message.type == bot_message.Type.QUIT:
                    print("Discord bot stopping on command")
                    # Does not seem to make client.run() stop
                    await client.close()
                    break
                if bot_message.type == bot_message.Type.STATUS:
                    if bot_message.direction == bot_message.Direction.REQUEST:
                        #print(client.users)
                        await status()
                    else:
                        print("Status received from mumble bot: %s" % bot_message.text)
                        if channel:
                            await channel.send(bot_message.text)
                elif bot_message.type == bot_message.Type.ACTIVITY:
                    print("Notification received from mumble bot: %s" % bot_message.text)
                    if channel:
                        await channel.send(bot_message.text)
                # elif cmd_msg == commonbot.INVITE_BOTCMD:
                #     param_msg = commonbot.get_bot_cmd_param(mumble_msg)
                #     params = param_msg.split(";", 1)
                #     await invite(commonbot.INVITERSP_BOTCMD, params[0], params[1])
                # elif cmd_msg == commonbot.INVITERSP_BOTCMD:
                #     param_msg = commonbot.get_bot_cmd_param(mumble_msg)
                #     params = param_msg.split(";", 1)
                #     sender = params[0]
                #     invite_response = params[1]
                #     usersdict = {str(user): user for user in client.users}
                #     if sender in usersdict:
                #         await usersdict[sender].send(invite_response)
                #     else:
                #         print("User %s not found" % sender)



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
