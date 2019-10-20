"""discomblebot launcher, either interactive or daemon-like."""

import argparse
import time
from multiprocessing import Process, Queue

from discomblebot import commonbot
from discomblebot import confbot
from discomblebot import discobot
from discomblebot import mumbot
from discomblebot.bot_msg_pb2 import BotMessage


def interactive_loop(discobot_cmd_queue, mumbot_cmd_queue):
    """Interactive loop waiting for user input commands."""
    while True:
        #print("bleigh")
        try:
            cmd = input("Enter command:")
        # handle bad KeyboardInterrupt/input() interactions (https://stackoverflow.com/a/31131378)
        except EOFError:
            time.sleep(1)
        if cmd == "!quit":
            print("Quitting")
            break
        if cmd == "!status":
            bot_message = BotMessage()
            bot_message.type = BotMessage.Type.STATUS
            bot_message.direction = BotMessage.Direction.REQUEST
            bot_message.source = BotMessage.Source.CLI
            if bot_message_str := commonbot.write_bot_message(bot_message):
                discobot_cmd_queue.put_nowait(bot_message_str)
                mumbot_cmd_queue.put_nowait(bot_message_str)
        else:
            print("Unknown command %s" % cmd)
            print("Supported commands are: !quit, !status")

def handle_options():
    """Read and check CLI options"""
    parser = argparse.ArgumentParser(
        prog="discomblebot", description="Run discord and mumble bots.")
    parser.add_argument(
        "-f", "--file", dest="conf_file", default=None, help="Configuration file path")
    parser.add_argument(
        "-e", "--environment", dest="environment", action="store_true", default=False,
        help="Load configuration from DISCOMBLE_CONF environment variable")
    parser.add_argument(
        "-i", "--interactive", dest="interactive", action="store_true", default=False,
        help="Enable interactive mode")
    parser.add_argument(
        "--version", action="version", version="discomblebot %s" % confbot.VERSION)
    debug_options = parser.add_argument_group("Debug options")
    debug_options.add_argument(
        "--debug-discord", dest="debug_discord", action="store_true", default=False,
        help="Debug Discord bot")
    debug_options.add_argument(
        "--debug-mumble", dest="debug_mumble", action="store_true", default=False,
        help="Debug Mumble bot")
    options = parser.parse_args()

    if options.environment:
        if options.conf_file:
            parser.error("Configuration cannot be read from both file and environment")
    else:
        if not options.conf_file:
            parser.error("Missing configuration file")
    if options.interactive and (options.debug_discord or options.debug_mumble):
        parser.error("Cannot debug a bot in interactive mode")
    if options.debug_discord and options.debug_mumble:
        parser.error("Cannot debug both bots simultaneously")

    return options

def main():
    """Program launcher"""
    options = handle_options()
    print("discomblebot start")
    discord_config, mumble_config = confbot.load_configuration(
        options.conf_file, options.environment)

    discobot_comm_queue = Queue()
    mumbot_comm_queue = Queue()
    if not options.debug_discord:
        dbp = Process(target=discobot.run, args=(
            discobot_comm_queue, mumbot_comm_queue, discord_config))
        dbp.start()
    if not options.debug_mumble:
        mbp = Process(target=mumbot.run, args=(
            mumbot_comm_queue, discobot_comm_queue, mumble_config))
        mbp.start()
    if options.debug_discord:
        discobot.run(discobot_comm_queue, mumbot_comm_queue, discord_config)
    if options.debug_mumble:
        mumbot.run(mumbot_comm_queue, discobot_comm_queue, mumble_config)

    if options.interactive:
        try:
            interactive_loop(discobot_comm_queue, mumbot_comm_queue)
        except KeyboardInterrupt:
            print("Terminating discomblebot")

        #Give bots a chance to exit gracefully
        bot_message = BotMessage()
        bot_message.type = BotMessage.Type.QUIT
        bot_message.direction = BotMessage.Direction.REQUEST
        bot_message.source = BotMessage.Source.CLI
        if bot_message_str := commonbot.write_bot_message(bot_message):
            discobot_comm_queue.put_nowait(bot_message_str)
            mumbot_comm_queue.put_nowait(bot_message_str)

        dbp.join(5)
        if dbp.is_alive():
            print("Force Discord bot exit")
            dbp.terminate()
        mbp.join(5)
        if mbp.is_alive():
            print("Force Mumble bot exit")
            mbp.terminate()
    else:
        if not options.debug_discord:
            dbp.join()
        if not options.debug_mumble:
            mbp.join()

    print("discomblebot end")


if __name__ == "__main__":
    main()
