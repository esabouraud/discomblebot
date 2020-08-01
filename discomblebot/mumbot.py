"""Mumble bot
  - executes CLI commands and responds to chat commands
  - monitors actity and sends messages to be written on Discord
  - displays messages coming from Discord bot."""

import pymumble_py3
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_CONNECTED, PYMUMBLE_CLBK_USERCREATED, PYMUMBLE_CLBK_USERREMOVED,
    PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, PYMUMBLE_CONN_STATE_CONNECTED)

from discomblebot import confbot
from discomblebot import commonbot
from discomblebot.bot_msg_pb2 import BotMessage

class MumbleBot:
    """Mumble bot management
    comm_queue is used to receive CLI commands and messages from Discord bot
    otherbot_comm_queue is used to send messages to Discord bot
    config contains the server parameters"""

    def __init__(self, comm_queue, otherbot_comm_queue, config):
        self.comm_queue = comm_queue
        self.otherbot_comm_queue = otherbot_comm_queue
        self.channel = config.channel
        self.config = config
        self.mumble = None

    def start_client(self):
        """Start or restart Mumble client"""
        self.mumble = pymumble_py3.Mumble(
            self.config.server, self.config.nickname, int(self.config.port), self.config.password)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_CONNECTED, self.connected_cb)
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the end of the connection process
        # mute and deafen the user (just to make clear he don't speak or listen)
        if self.mumble.connected != PYMUMBLE_CONN_STATE_CONNECTED:
            print("Mumble bot failed to connect to server %s:%s" % (
                self.config.server, self.config.port))
            return False
        self.mumble.users.myself.mute()
        self.mumble.users.myself.deafen()
        # join output channel
        if self.channel:
            try:
                channel = self.mumble.channels.find_by_name(self.channel)
                channel.move_in()
            except pymumble_py3.errors.UnknownChannelError:
                print("Mumble channel not found: %s" % self.channel)
        return True

    def loop(self):
        """Main loop of the mumble bot"""
        while discord_msg := self.comm_queue.get():
            if not self.mumble.is_alive():
                print("Mumble bot thread died, restarting")
                self.start_client()
            if bot_message := commonbot.read_bot_message(discord_msg):
                print("Mumble bot: message received with type %d direction %s source %d" % (
                    bot_message.type, bot_message.direction, bot_message.source))
                if bot_message.type == bot_message.Type.QUIT:
                    print("Mumble bot stopping on command")
                    break
                if bot_message.type == bot_message.Type.STATUS:
                    if bot_message.direction == bot_message.Direction.REQUEST:
                        print("Status request from discord bot: %s" % bot_message.std.text)
                        self.status(bot_message.channel)
                    else:
                        print("Status response from discord bot: %s" % bot_message.std.text)
                        if bot_message.channel:
                            channel_id = int(bot_message.channel)
                            if channel_id in self.mumble.users:
                                output_channel = self.mumble.users[channel_id]
                            else:
                                output_channel = self.mumble.channels[channel_id]
                        else:
                            output_channel = self.mumble.channels[self.mumble.users.myself['channel_id']]
                        if output_channel:
                            output_channel.send_text_message(bot_message.std.text)
                elif bot_message.type == bot_message.Type.ACTIVITY:
                    print("Notification received from discord bot: %s" % bot_message.std.text)
                    my_channel_id = self.mumble.users.myself['channel_id']
                    self.mumble.channels[my_channel_id].send_text_message(bot_message.std.text)
                elif bot_message.type == bot_message.Type.INVITE:
                    if bot_message.direction in [bot_message.Direction.INFO, bot_message.Direction.RESPONSE]:
                        sender_name = bot_message.invite.sender
                        recipient_name = bot_message.invite.recipient
                        invite_url = bot_message.invite.url
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
                        if bot_message.direction == bot_message.Direction.RESPONSE:
                            if invite_successful:
                                success_message = "%s has been invited to Discord." % (recipient_name)
                                # Send OK message to mumble sender
                                if sender_name in usersdict:
                                    self.mumble.users[usersdict[sender_name]].send_text_message(
                                        success_message)
                        else:
                            new_bot_message = BotMessage()
                            new_bot_message.type = BotMessage.Type.ACTIVITY
                            new_bot_message.direction = BotMessage.Direction.INFO
                            new_bot_message.source = BotMessage.Source.MUMBLE
                            new_bot_message.channel = bot_message.channel
                            # TODO improve invite response to discord text
                            if invite_successful:
                                # Send OK message to Discord sender
                                new_bot_message.std.text = "Invite OK"
                            else:
                                # Send error message to discord sender
                                new_bot_message.std.text = "Invite KO"
                            if bot_message_str := commonbot.write_bot_message(new_bot_message):
                                self.otherbot_comm_queue.put_nowait(bot_message_str)

    def status(self, channel=None):
        """Respond to status command"""
        #print(self.mumble.users)
        status_str = "%d users (%s) are connected on the Mumble server" % (
            self.mumble.users.count(),
            ", ".join([user['name'] for _userid, user in self.mumble.users.items()]))
        print(status_str)
        bot_message = BotMessage()
        bot_message.type = BotMessage.Type.STATUS
        bot_message.direction = BotMessage.Direction.RESPONSE
        bot_message.source = BotMessage.Source.MUMBLE
        bot_message.std.text = status_str
        if channel:
            bot_message.channel = channel
        if bot_message_str := commonbot.write_bot_message(bot_message):
            self.otherbot_comm_queue.put(bot_message_str)

    def connected_cb(self):
        """Wait until bot is connected before starting monitoring users"""
        print("Mumble bot connected")
        # Do first status update
        self.status()
        # Start monitoring users and messages
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created_cb)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed_cb)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.msg_received_cb)

    def send_notification(self, text):
        """Send unrequested message to other bot"""
        # Notify Discord bot of Mumble activity
        bot_message = BotMessage()
        bot_message.type = BotMessage.Type.ACTIVITY
        bot_message.direction = BotMessage.Direction.INFO
        bot_message.source = BotMessage.Source.MUMBLE
        bot_message.std.text = text
        if bot_message_str := commonbot.write_bot_message(bot_message):
            self.otherbot_comm_queue.put_nowait(bot_message_str)
        # Also log activity in Mumble
        my_channel_id = self.mumble.users.myself['channel_id']
        self.mumble.channels[my_channel_id].send_text_message(text)

    def user_created_cb(self, user):
        """A user is connected on the server."""
        print(user)
        self.send_notification("User %s joined the Mumble server" % user['name'])

    def user_removed_cb(self, user, *args):
        """A user has disconnected from the server."""
        print(user)
        self.send_notification("User %s left the Mumble server" % user['name'])

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
        if (cmd := commonbot.parse_chat_message(message.message)) is None:
            return
        #print("Mumble bot CMD: %s" % cmd)
        if cmd == commonbot.HELLO_CMD:
            output_channel.send_text_message(
                "Hello %s !" % self.mumble.users[message.actor]['name'])
        elif cmd == commonbot.VERSION_CMD:
            output_channel.send_text_message(
                "Current version: %s" % confbot.VERSION)
        elif cmd == commonbot.HELP_CMD:
            output_channel.send_text_message(commonbot.get_chat_help_message())
        elif cmd == commonbot.STATUS_CMD:
            bot_message = BotMessage()
            bot_message.type = BotMessage.Type.STATUS
            bot_message.direction = BotMessage.Direction.REQUEST
            bot_message.source = BotMessage.Source.MUMBLE
            if message.channel_id:
                bot_message.channel = "%d" % message.channel_id[0]
            elif message.session:
                bot_message.channel = "%d" % message.actor
            if bot_message_str := commonbot.write_bot_message(bot_message):
                self.otherbot_comm_queue.put_nowait(bot_message_str)
        elif cmd == commonbot.INVITE_CMD:
            sender_name = self.mumble.users[message.actor]['name']
            recipient_name = commonbot.get_chat_cmd_param(message.message)
            print("Mumble bot requesting invite for %s" % recipient_name)
            if recipient_name in [user['name'] for _userid, user in self.mumble.users.items()]:
                bot_message = BotMessage()
                bot_message.type = BotMessage.Type.INVITE
                bot_message.direction = BotMessage.Direction.REQUEST
                bot_message.source = BotMessage.Source.MUMBLE
                bot_message.invite.sender = sender_name
                bot_message.invite.recipient = recipient_name
                if bot_message_str := commonbot.write_bot_message(bot_message):
                    self.otherbot_comm_queue.put_nowait(bot_message_str)
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
        if bot.start_client():
            bot.loop()
    except KeyboardInterrupt:
        print("Mumble bot stopping on its own")
    print("Mumble bot final goodbye")
