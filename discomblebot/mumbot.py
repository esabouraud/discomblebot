import time
import pymumble_py3
from pymumble_py3.constants import PYMUMBLE_CLBK_USERCREATED, PYMUMBLE_CLBK_USERREMOVED

class MumbleBot:
    def __init__(self, comm_queue, cmd_queue, server, port, nickname, password):
        self.comm_queue = comm_queue
        self.cmd_queue = cmd_queue
        self.mumble = pymumble_py3.Mumble(server, nickname, int(port), password)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed)

        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the end of the connection process
        # mute and deafen the user (just to make clear he don't speak or listen)
        self.mumble.users.myself.mute()
        self.mumble.users.myself.deafen()

    def loop(self):
        while self.mumble.is_alive():
            str = self.cmd_queue.get()
            if str == "quit":
                print("Mumble bot stopping on command: %s" % str)
                break
            else:
                print("Mumble bot unknown command: %s" % str)

    def user_created(self, user):
        """A user is connected on the server.  Create the specific structure with the local informations"""
        print(user)
        self.comm_queue.put("User %s joined the Mumble server" % user['name'])
            
    def user_removed(self, user, *args):
        """a user has disconnected"""
        print(user)
        self.comm_queue.put("User %s left the Mumble server" % user['name'])

def run(comm_queue, cmd_queue, config):
    bot = MumbleBot(comm_queue, cmd_queue, config.server, config.port, config.nickname, config.password)
    try:
        bot.loop()
    except KeyboardInterrupt:
        print("Mumble bot stopping on its own")
    print("Mumble bot final goodbye")
