import sys
import argparse

from discomblebot import bot

def main():
    parser = argparse.ArgumentParser(description="Run discord bot")
    parser.add_argument("-t", "--token", dest="discord_token", default=None, help="Discord access token")
    options = parser.parse_args()

    if options.discord_token is None:
        print("Error: missing mandatory discord access token")
        sys.exit(-1)
    bot.run(options.discord_token)

if __name__ == "__main__":
    main()
