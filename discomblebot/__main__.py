import sys
import os
import argparse

from discomblebot import bot

DISCORD_TOKEN_ENV = "DISCORD_TOKEN"


def main():
    parser = argparse.ArgumentParser(description="Run discord bot")
    parser.add_argument("-t", "--token", dest="discord_token", default=None, help="Discord access token")
    options = parser.parse_args()

    if options.discord_token:
        discord_token = options.discord_token
    else:
        if DISCORD_TOKEN_ENV in os.environ:
            discord_token = os.environ[DISCORD_TOKEN_ENV]
        else:
            print("Error: missing mandatory discord access token")
            sys.exit(-1)

    bot.run(discord_token)


if __name__ == "__main__":
    main()
