"""Common code used by both bots."""

import re

HELLO_CMD = "hello"
STATUS_CMD = "status"
VERSION_CMD = "version"
CMDE_RX = re.compile("^\\$(%s|%s|%s)(?:\\s.*)?$" % (HELLO_CMD, STATUS_CMD, VERSION_CMD) )


def parse_message(message):
    """Handle user commands sent in chat"""
    if message.content.startswith("$"):
        match_cmd = CMDE_RX.match(message.content)
        if match_cmd:
            return match_cmd.group(1)
        else:
            return "unknown"
    return None
