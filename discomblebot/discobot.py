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
discord_config = None
guild = None
default_channel = None
subscriber_role = None
otherbot_comm_queue = None


@client.event
async def on_ready():
    """Finalize bot connection to Discord"""
    global guild
    global default_channel
    global subscriber_role
    print("We have logged in as {0.user}".format(client))
    if (guild := client.get_guild(int(discord_config.guild_id))) is None:
        raise Exception("Bot is not connected to guild %s" % discord_config.guild_id)
    roles_dict = {role.name: role for role in guild.roles}
    if discord_config.role_name in roles_dict:
        subscriber_role = roles_dict[discord_config.role_name]
    else:
        subscriber_role = await guild.create_role(name=discord_config.role_name)
    channels_dict = {channel.name: channel for channel in guild.channels}
    if discord_config.channel_name in channels_dict:
        default_channel = channels_dict[discord_config.channel_name]
    else:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            subscriber_role: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        default_channel = await guild.create_text_channel(
            discord_config.channel_name, overwrites=overwrites)
    print("Output default channel is '%s'" % default_channel)
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
        bot_message.channel = "%d" % message.channel.id
        if bot_message_str := commonbot.write_bot_message(bot_message):
            otherbot_comm_queue.put_nowait(bot_message_str)
    elif cmd == commonbot.INVITE_CMD:
        sender = message.author.name
        recipient = commonbot.get_chat_cmd_param(message.content)
        await invite("%d" % message.channel.id, sender, recipient, False)
    elif cmd == commonbot.SUBSCRIBE_CMD:
        if member := guild.get_member(message.author.id):
            await member.add_roles(subscriber_role)
            await message.channel.send(
                "You have been assigned the %s role on server: %s" % (
                    subscriber_role.name, guild.name))
    elif cmd == commonbot.UNSUBSCRIBE_CMD:
        if member := guild.get_member(message.author.id):
            await member.remove_roles(subscriber_role)
            await message.channel.send(
                "You have been unassigned the %s role on server: %s" % (
                    subscriber_role.name, guild.name))
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
        bot_message.std.text = activity_str
        if bot_message_str := commonbot.write_bot_message(bot_message):
            otherbot_comm_queue.put_nowait(bot_message_str)

async def status(channel=None):
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
    bot_message.std.text = status_str
    if channel:
        bot_message.channel = channel
    if bot_message_str := commonbot.write_bot_message(bot_message):
        otherbot_comm_queue.put_nowait(bot_message_str)

async def invite(channel, sender, recipient, from_bot):
    """Invite mumble user to discord"""
    # Invites are channel-level, not guild-level, oddly enough
    channel_invite = await default_channel.create_invite(
        max_age=86400, max_uses=1, unique=True, reason="discomble")
    print(channel_invite)
    bot_message = BotMessage()
    bot_message.type = BotMessage.Type.INVITE
    if from_bot:
        bot_message.direction = BotMessage.Direction.RESPONSE
    else:
        bot_message.direction = BotMessage.Direction.INFO
    bot_message.source = BotMessage.Source.DISCORD
    bot_message.channel = channel
    bot_message.invite.sender = sender
    bot_message.invite.recipient = recipient
    bot_message.invite.url = channel_invite.url
    if bot_message_str := commonbot.write_bot_message(bot_message):
        otherbot_comm_queue.put_nowait(bot_message_str)

async def read_comm_queue(comm_queue):
    """Read queue expecting Mumble-bot issued messages or CLI commands (start with !).
    Read operation is blocking, so run in a dedicated executor."""
    global default_channel
    while default_channel is None:
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
                        await status(bot_message.channel)
                    else:
                        print("Status received from mumble bot: %s" % bot_message.std.text)
                        if bot_message.channel:
                            channel = client.get_channel(int(bot_message.channel))
                            await channel.send(bot_message.std.text)
                        elif default_channel:
                            await default_channel.send(bot_message.std.text)
                elif bot_message.type == bot_message.Type.ACTIVITY:
                    print("Notification received from mumble bot: %s" % bot_message.std.text)
                    if bot_message.channel:
                        channel = client.get_channel(int(bot_message.channel))
                        await channel.send(bot_message.std.text)
                    elif default_channel:
                        await default_channel.send(bot_message.std.text)
                elif bot_message.type == bot_message.Type.INVITE:
                    if bot_message.direction == bot_message.Direction.REQUEST:
                        await invite(
                            bot_message.channel, bot_message.invite.sender,
                            bot_message.invite.recipient, True)


def run(comm_queue, mumbot_comm_queue, config):
    """Launch Discord bot
    comm_queue is used to receive CLI commands and messages from Mumble bot
    mumbot_comm_queue is used to send messages to Mumble bot
    config contains the server parameters"""

    global discord_config
    global otherbot_comm_queue
    otherbot_comm_queue = mumbot_comm_queue
    discord_config = config
    client.loop.create_task(read_comm_queue(comm_queue))
    try:
        client.run(config.token)
    except KeyboardInterrupt:
        print("Discord bot stopping on its own")
    print("Discord bot final goodbye")
