"""Mumble bot
  - executes CLI commands and responds to chat commands
  - monitors actity and sends messages to be written on Discord
  - displays messages coming from Discord bot."""

import pymumble_py3
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_CONNECTED, PYMUMBLE_CLBK_USERCREATED, PYMUMBLE_CLBK_USERREMOVED,
    PYMUMBLE_CLBK_TEXTMESSAGERECEIVED)

from discomblebot import confbot
from discomblebot import commonbot

class MumbleBot:
    """Mumble bot management
    comm_queue is used to receive CLI commands and messages from Discord bot
    otherbot_comm_queue is used to send messages to Discord bot
    config contains the server parameters"""

    def __init__(self, comm_queue, otherbot_comm_queue, config):
        self.comm_queue = comm_queue
        self.otherbot_comm_queue = otherbot_comm_queue
        self.channel = config.channel
        self.mumble = pymumble_py3.Mumble(
            config.server, config.nickname, int(config.port), config.password, reconnect=True)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_CONNECTED, self.connected_cb)
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the end of the connection process
        # mute and deafen the user (just to make clear he don't speak or listen)
        self.mumble.users.myself.mute()
        self.mumble.users.myself.deafen()
        # join output channel
        if self.channel:
            try:
                channel = self.mumble.channels.find_by_name(self.channel)
                channel.move_in()
            except pymumble_py3.errors.UnknownChannelError:
                print("Mumble channel not found: %s" % self.channel)

    def loop(self):
        """Main loop of the mumble bot"""
        while self.mumble.is_alive():
            discord_msg = self.comm_queue.get()
            if cmd_msg := commonbot.parse_bot_command(discord_msg):
                if cmd_msg == commonbot.QUIT_BOTCMD:
                    print("Mumble bot stopping on command: %s" % cmd_msg)
                    break
                elif cmd_msg == commonbot.STATUS_BOTCMD:
                    self.status()
                elif cmd_msg in (commonbot.INVITE_BOTCMD, commonbot.INVITERSP_BOTCMD):
                    param_msg = commonbot.get_bot_cmd_param(discord_msg)
                    params = param_msg.split(";", 2)
                    sender_name = params[0]
                    recipient_name = params[1]
                    invite_url = params[2]
                    print("Mumble bot receiving invite %s from %s for %s" % (
                        invite_url, sender_name, recipient_name))
                    usersdict = {user['name']: userid for userid, user in self.mumble.users.items()}
                    if recipient_name in usersdict:
                        # Send PM to user with invite link
                        self.mumble.users[usersdict[recipient_name]].send_text_message(
                            "%s has invited you to a Discord server: <a href=\"%s\">%s</a>" % (
                                sender_name, invite_url, invite_url))
                        invite_successful = True
                    else:
                        invite_successful = False
                    if invite_successful:
                        success_message = "%s has been invited to Discord." % (recipient_name)
                        if cmd_msg == commonbot.INVITERSP_BOTCMD:
                            # Send OK message to mumble sender
                            if sender_name in usersdict and cmd_msg == commonbot.INVITERSP_BOTCMD:
                                self.mumble.users[usersdict[sender_name]].send_text_message(
                                    success_message)
                        else:
                            # Send OK message to Discord sender
                            self.otherbot_comm_queue.put("!%s|%s;%s" % (
                                commonbot.INVITERSP_BOTCMD, sender_name, success_message))
                    else:
                        if cmd_msg == commonbot.INVITE_BOTCMD:
                            # Send error message to discord sender
                            self.otherbot_comm_queue.put(
                                "!%s|%s;Failed to find user %s in Mumble" % (
                                    commonbot.INVITERSP_BOTCMD, sender_name, recipient_name))
                else:
                    print("Mumble bot unknown command: %s" % cmd_msg)
            else:
                print("Mumble bot read data from queue: %s" % discord_msg)
                my_channel_id = self.mumble.users.myself['channel_id']
                self.mumble.channels[my_channel_id].send_text_message(discord_msg)

    def status(self):
        """Respond to status command"""
        #print(self.mumble.users)
        status_str = "%d users (%s) are connected on the Mumble server" % (
            self.mumble.users.count(),
            ", ".join([user['name'] for _userid, user in self.mumble.users.items()]))
        print(status_str)
        self.otherbot_comm_queue.put(status_str)

    def connected_cb(self):
        """Wait until bot is connected before starting monitoring users"""
        print("Mumble bot connected")
        # Do first status update
        self.status()
        # Start monitoring users and messages
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created_cb)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed_cb)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.msg_received_cb)

    def user_created_cb(self, user):
        """A user is connected on the server."""
        print(user)
        self.otherbot_comm_queue.put("User %s joined the Mumble server" % user['name'])

    def user_removed_cb(self, user, *args):
        """A user has disconnected from the server."""
        print(user)
        self.otherbot_comm_queue.put("User %s left the Mumble server" % user['name'])

    def msg_received_cb(self, message):
        """A text message has been received"""
        print(message)
        # Write response on source channel...
        if message.channel_id:
            output_channel = self.mumble.channels[message.channel_id[0]]
        # ... Or private message depending on message source
        elif message.session:
            output_channel = self.mumble.users[message.actor]
        else:
            print("Mumble bot cannot identify output channel")
            return
        if cmd := commonbot.parse_chat_message(message.message) is None:
            return
        if cmd == commonbot.HELLO_CMD:
            output_channel.send_text_message(
                "Hello %s !" % self.mumble.users[message.actor]['name'])
        elif cmd == commonbot.VERSION_CMD:
            output_channel.send_text_message(
                "Current version: %s" % confbot.VERSION)
        elif cmd == commonbot.HELP_CMD:
            output_channel.send_text_message(commonbot.get_chat_help_message())
        elif cmd == commonbot.STATUS_CMD:
            self.otherbot_comm_queue.put("!%s" % commonbot.STATUS_BOTCMD)
        elif cmd == commonbot.INVITE_CMD:
            sender_name = self.mumble.users[message.actor]['name']
            recipient_name = commonbot.get_chat_cmd_param(message.message)
            print("Mumble bot requesting invite for %s" % recipient_name)
            if recipient_name in [user['name'] for _userid, user in self.mumble.users.items()]:
                self.otherbot_comm_queue.put("!%s|%s;%s" % (
                    commonbot.INVITE_BOTCMD, sender_name, recipient_name))
            else:
                error_msg = "Failed to find user %s" % recipient_name
                print(error_msg)
                output_channel.send_text_message(error_msg)
        else:
            output_channel.send_text_message("I do not understand this command.")


def run(comm_queue, otherbot_comm_queue, config):
    """Launch Mumble bot"""
    bot = MumbleBot(comm_queue, otherbot_comm_queue, config)
    try:
        bot.loop()
    except KeyboardInterrupt:
        print("Mumble bot stopping on its own")
    print("Mumble bot final goodbye")
