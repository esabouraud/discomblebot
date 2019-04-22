import time
import pymumble_py3
from pymumble_py3.constants import PYMUMBLE_CLBK_CONNECTED, PYMUMBLE_CLBK_USERCREATED, PYMUMBLE_CLBK_USERREMOVED

class MumbleBot:
    def __init__(self, comm_queue, cmd_queue, server, port, nickname, password):
        self.comm_queue = comm_queue
        self.cmd_queue = cmd_queue
        self.mumble = pymumble_py3.Mumble(server, nickname, int(port), password)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_CONNECTED, self.connected_cb)


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
            elif str == "status":
                self.status()
            else:
                print("Mumble bot unknown command: %s" % str)

    def status(self):
        #print(self.mumble.users)
        status_str = "%d users (%s) are connected on the Mumble server" % (
            self.mumble.users.count(),
            ", ".join([user['name'] for _userid, user in self.mumble.users.items()]))
        print(status_str)
        self.comm_queue.put(status_str)

    def connected_cb(self):
        print("Mumble bot connected")
        self.status()
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created_cb)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed_cb)

    def user_created_cb(self, user):
        """A user is connected on the server.  Create the specific structure with the local informations"""
        print(user)
        self.comm_queue.put("User %s joined the Mumble server" % user['name'])
            
    def user_removed_cb(self, user, *args):
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
