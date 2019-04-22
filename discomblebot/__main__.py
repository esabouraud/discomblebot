import argparse
from multiprocessing import Process, Queue

from discomblebot import confbot
from discomblebot import discobot
from discomblebot import mumbot


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
    q = Queue()
    if options.debug_discord:
        discobot.run(q, discord_config)
    else:
        dbp = Process(target=discobot.run, args=(q, discord_config))
        dbp.start()
    if options.debug_mumble:
        mumbot.run(q, mumble_config)
    else:
        mbp = Process(target=mumbot.run, args=(q, mumble_config))
        mbp.start()
    print("bleigh")
    if not options.debug_discord:
        dbp.join()
    if not options.debug_mumble:
        mbp.join()


if __name__ == "__main__":
    main()
