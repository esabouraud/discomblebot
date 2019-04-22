import argparse
import time
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
    bot_comm_queue = Queue()
    discobot_cmd_queue = Queue()
    mumbot_cmd_queue = Queue()
    dbp = Process(target=discobot.run, args=(bot_comm_queue, discobot_cmd_queue, discord_config))
    dbp.start()
    mbp = Process(target=mumbot.run, args=(bot_comm_queue, mumbot_cmd_queue, mumble_config))
    mbp.start()

    try:
        while True:
            print("bleigh")
            time.sleep(60)
    except KeyboardInterrupt:
        print("Terminating discomblebot")

    #Give bots a chance to exit gracefully
    discobot_cmd_queue.put_nowait("quit")
    dbp.join(5)
    if dbp.is_alive():
        print("Force Discord bot exit")
        dbp.terminate()
    mumbot_cmd_queue.put_nowait("quit")
    mbp.join(5)
    if mbp.is_alive():
        print("Force Mumble bot exit")
        mbp.terminate()


if __name__ == "__main__":
    main()
