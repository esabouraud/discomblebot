"""Bots configuration management"""

import os
import configparser
from collections import namedtuple

VERSION = "0.4.5"

CONF_ENV = "DISCOMBLE_CONF"
DISCORD_SECTION = "discord"
MUMBLE_SECTION = "mumble"
DiscordConf = namedtuple("DiscordConf", ["token", "channel"])
MumbleConf = namedtuple("MumbleConf", ["server", "port", "nickname", "password", "channel"])

def load_configuration(path, environment):
    "Load configuration from INI file or environment variable"

    if environment:
        configstr = os.environ[CONF_ENV]
    else:
        configstr = open(path).read()
    config = configparser.ConfigParser()
    config.read_string(configstr)
    for mandatory_section in [DISCORD_SECTION, MUMBLE_SECTION]:
        if not config.has_section(mandatory_section):
            raise ValueError(
                "Configuration file '%s' has no section '%s'" % (path, mandatory_section))
    discord_config = DiscordConf._make(
        [config[DISCORD_SECTION][field] for field in DiscordConf._fields])
    mumble_config = MumbleConf._make(
        [config[MUMBLE_SECTION][field] for field in MumbleConf._fields])

    return discord_config, mumble_config
