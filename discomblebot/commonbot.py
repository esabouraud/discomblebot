"""Common code used by both bots."""

import re

# Display a simple hello message
HELLO_CMD = "hello"
# Query other bot for status and display response
STATUS_CMD = "status"
# Display program version
VERSION_CMD = "version"
# Regexp matching supported commands
CMDE_RX = re.compile("^\\$(%s|%s|%s)(?:\\s.*)?$" % (HELLO_CMD, STATUS_CMD, VERSION_CMD))


def parse_message(message):
    """Handle user commands sent in chat (start with $)"""
    if message.startswith("$"):
        match_cmd = CMDE_RX.match(message)
        if match_cmd:
            return match_cmd.group(1)
        return "unknown"
    return None
