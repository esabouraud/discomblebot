import configparser
from collections import namedtuple

DISCORD_SECTION = "discord"
MUMBLE_SECTION = "mumble"
DiscordConf = namedtuple("DiscordConf", ["token", "channel"])
MumbleConf = namedtuple("MumbleConf", ["server", "port", "nickname", "password"])

def load_configuration(path):
    "Load configuration from INI file"

    config = configparser.ConfigParser()
    config.read(path)
    for mandatory_section in [DISCORD_SECTION, MUMBLE_SECTION]:
        if not config.has_section(mandatory_section):
            raise ValueError("Configuration file '%s' has no section '%s'")
    discord_config = DiscordConf._make([config[DISCORD_SECTION][field] for field in DiscordConf._fields])
    mumble_config = MumbleConf._make([config[MUMBLE_SECTION][field] for field in MumbleConf._fields])

    return discord_config, mumble_config
