import argparse
import threading

from discomblebot import confbot
from discomblebot import discobot
from discomblebot import mumbot

class DiscoThread(threading.Thread):
    def __init__(self, discord_config):
        threading.Thread.__init__(self)
        self.token = discord_config.token

    def run(self):
        discobot.run(self.token)


class MumbThread(threading.Thread):
    def __init__(self, mumble_config):
        threading.Thread.__init__(self)
        self.server = mumble_config.server
        self.port = mumble_config.port
        self.nickname = mumble_config.nickname
        self.password = mumble_config.password

    def run(self):
        mumbot.run(self.server, self.port, self.nickname, self.password)


def main():
    parser = argparse.ArgumentParser(description="Run discord bot")
    parser.add_argument("-f", "--file", dest="conf_file", default=None, help="Discord access token")
    debug_options = parser.add_argument_group("Debug options")
    debug_options.add_argument("--debug-discord", dest="debug_discord", action="store_true", default=False, help="Debug Discord bot")
    debug_options.add_argument("--debug-mumble", dest="debug_mumble", action="store_true", default=False, help="Debug Mumble bot")
    options = parser.parse_args()

    if not options.conf_file:
        parser.error("Missing mandatory configuration file")
    if options.debug_discord and options.debug_mumble:
        parser.error("Cannot debug both bots simultaneously")

    discord_config, mumble_config = confbot.load_configuration(options.conf_file)
    if options.debug_discord:
        discobot.run(discord_config.token)
    elif options.debug_mumble:
        mumbot.run(mumble_config.server, mumble_config.port, mumble_config.nickname, mumble_config.password)
    else:
        dbt = DiscoThread(discord_config)
        mbt = MumbThread(mumble_config)
        dbt.start()
        mbt.start()
        print("bleigh")
        dbt.join()
        mbt.join()


if __name__ == "__main__":
    main()
