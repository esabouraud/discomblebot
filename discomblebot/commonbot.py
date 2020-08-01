"""Common code used by both bots."""

import re
from google.protobuf import message as _message
from discomblebot import bot_msg_pb2

# Display a simple hello message
HELLO_CMD = "hello"
# Display inline help message
HELP_CMD = "help"
# Query other bot for status and display response
STATUS_CMD = "status"
# Display program version
VERSION_CMD = "version"
# Invite user to other server
INVITE_CMD = "invite"
# Subscribe to output text channel (Discord only)
SUBSCRIBE_CMD = "subscribe"
# Unsubscribe to output text channel (Discord only)
UNSUBSCRIBE_CMD = "unsubscribe"
# All supported chat commands (start with $)
CHAT_COMMANDS = [
    (HELP_CMD, "Display this help message"),
    (VERSION_CMD, "Get the current version of the bot"),
    (HELLO_CMD, "Greet the bot"),
    (STATUS_CMD, "List users connected to voice chat"),
    (INVITE_CMD, "[Mumble user name] Send an invite to the Discord Server, to a Mumble user"),
    (SUBSCRIBE_CMD, "[Discord only] Subscribe to the voice chat activity monitoring channel"),
    (UNSUBSCRIBE_CMD, "[Discord only] Unsubscribe to the voice chat activity monitoring channel")]
# Regexp matching supported commands
CHAT_CMD_RX = re.compile("^\\$(%s)(?:\\s.*)?$" % "|".join(
    [command[0] for command in CHAT_COMMANDS]))
# Regexp matching a command, to extract a following parameter (separator=whitespace)
CHAT_PARAM_RX = re.compile("^\\$.+\\s+([^\\s]+).*$")

# Fetch current server status and send it to other bot
STATUS_BOTCMD = "status"
# Generate an invite and send it to the other bot
INVITE_BOTCMD = "invite"
# Send response to an invite command to the other bot
INVITERSP_BOTCMD = "invitersp"
# Stop the bot gracefully
QUIT_BOTCMD = "quit"
# All supported Bot/CLI commands (start with !)
BOT_COMMANDS = [STATUS_BOTCMD, INVITE_BOTCMD, INVITERSP_BOTCMD, QUIT_BOTCMD]
# Regexp matching supported commands
BOTCMD_RX = re.compile("^!(%s)(?:\\|.*)?$" % "|".join(BOT_COMMANDS))
# Regexp matching a command, to extract a following parameter (separator=|)
BOTCMD_PARAM_RX = re.compile("^!.+\\|(.*)$")

def parse_chat_message(message):
    """Handle user commands sent in chat"""
    return parse_command("$", CHAT_CMD_RX, message)

def get_chat_cmd_param(message):
    """Get single param from command message"""
    return get_cmd_param(CHAT_PARAM_RX, message)

def get_chat_help_message():
    """Return inline help string"""
    help_message = [
        "discomble is a 2-in-1 Mumble and Discord Bot.",
        "It monitors voice chat activity on a Mumble and a Discord server.",
        "Available commands are:"]
    for command in CHAT_COMMANDS:
        help_message.append("\t$%s: %s" % command)
    return "\n".join(help_message)

def parse_bot_command(message):
    """Handle user or bot commands sent in queue"""
    return parse_command("!", BOTCMD_RX, message)

def get_bot_cmd_param(message):
    """Get single param from command message"""
    return get_cmd_param(BOTCMD_PARAM_RX, message)

def parse_command(start_char, cmd_rx, message):
    """Handle user or bot commands sent in queue or chat"""
    if message.startswith(start_char):
        if match_cmd := cmd_rx.match(message):
            return match_cmd.group(1)
        return "unknown"
    return None

def get_cmd_param(param_rx, message):
    """Get single param from command message"""
    if match_param := param_rx.match(message):
        return match_param.group(1)
    return None

def read_bot_message(message_string):
    """Unmarshal protobuf message"""
    bot_message = bot_msg_pb2.BotMessage()
    try:
        bot_message.ParseFromString(message_string)
        return bot_message
    except _message.Error as error:
        print("Error unmarshalling bot protobuf message: %s" % error)
        return None

def write_bot_message(bot_message):
    """Marshal protobuf message"""
    try:
        return bot_message.SerializeToString()
    except _message.Error as error:
        print("Error marshalling bot protobuf message: %s" % error)
        return None
