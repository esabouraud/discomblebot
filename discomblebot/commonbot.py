"""Common code used by both bots."""

import re

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
# All supported commands
COMMANDS = [HELLO_CMD, HELP_CMD, STATUS_CMD, VERSION_CMD, INVITE_CMD]
# Regexp matching supported commands
CMD_RX = re.compile("^\\$(%s)(?:\\s.*)?$" % "|".join(COMMANDS))
# Regexp matching a command, to extract a following parameter
PARAM_RX = re.compile("^\\$.+\\s+([^\\s]+).*$")

def parse_message(message):
    """Handle user commands sent in chat (start with $)"""
    if message.startswith("$"):
        match_cmd = CMD_RX.match(message)
        if match_cmd:
            return match_cmd.group(1)
        return "unknown"
    return None

def get_cmd_param(message):
    """Get single param from command message"""
    match_param = PARAM_RX.match(message)
    if match_param:
        return match_param.group(1)
    return None

def get_help_message():
    """Return inline help string"""
    return "Available commands are: %s" % ", ".join(COMMANDS)
