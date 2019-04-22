import argparse
import time
from multiprocessing import Process, Queue

from discomblebot import confbot
from discomblebot import discobot
from discomblebot import mumbot


def loop(discobot_cmd_queue, mumbot_cmd_queue):
    while True:
        #print("bleigh")
        try:
            cmd = input("Enter command:")
        # handle bad KeyboardInterrupt/input() interactions (https://stackoverflow.com/a/31131378)
        except EOFError:
            time.sleep(1)
        if cmd == "quit":
            print("Quitting")
            break
        elif cmd == "status":
            discobot_cmd_queue.put_nowait(cmd)
            mumbot_cmd_queue.put_nowait(cmd)
        else:
            print("Unknown command %s" % cmd)
            print("Supported commands are: quit, status")

def main():
    parser = argparse.ArgumentParser(prog="discomblebot", description="Run discord and mumble bots.")
    parser.add_argument("-f", "--file", dest="conf_file", default=None, help="Configuration file path")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    debug_options = parser.add_argument_group("Debug options")
    debug_options.add_argument("--debug-discord", dest="debug_discord", action="store_true", default=False, help="Debug Discord bot (broken)")
    debug_options.add_argument("--debug-mumble", dest="debug_mumble", action="store_true", default=False, help="Debug Mumble bot (broken)")
    options = parser.parse_args()

    if not options.conf_file:
        parser.error("Missing mandatory configuration file")
    if options.debug_discord and options.debug_mumble:
        parser.error("Cannot debug both bots simultaneously")

    print("Staring discomblebot")
    discord_config, mumble_config = confbot.load_configuration(options.conf_file)
    bot_comm_queue = Queue()
    discobot_cmd_queue = Queue()
    mumbot_cmd_queue = Queue()
    dbp = Process(target=discobot.run, args=(bot_comm_queue, discobot_cmd_queue, discord_config))
    dbp.start()
    mbp = Process(target=mumbot.run, args=(bot_comm_queue, mumbot_cmd_queue, mumble_config))
    mbp.start()

    try:
        loop(discobot_cmd_queue, mumbot_cmd_queue)
    except KeyboardInterrupt:
        print("Terminating discomblebot")

    #Give bots a chance to exit gracefully
    discobot_cmd_queue.put_nowait("quit")
    mumbot_cmd_queue.put_nowait("quit")

    dbp.join(5)
    if dbp.is_alive():
        print("Force Discord bot exit")
        dbp.terminate()
    mbp.join(5)
    if mbp.is_alive():
        print("Force Mumble bot exit")
        mbp.terminate()


if __name__ == "__main__":
    main()
