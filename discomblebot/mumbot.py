import time
import pymumble_py3
from pymumble_py3.constants import PYMUMBLE_CLBK_USERCREATED, PYMUMBLE_CLBK_USERREMOVED

class MumbleBot:
    def __init__(self, dm_queue, server, port, nickname, password):
        self.dm_queue = dm_queue
        self.mumble = pymumble_py3.Mumble(server, nickname, int(port), password)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed)

        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the end of the connection process
        self.mumble.users.myself.mute() # mute the user (just to make clear he don't speak)

    def loop(self):
        while self.mumble.is_alive():
            time.sleep(1)

    def user_created(self, user):
        """A user is connected on the server.  Create the specific structure with the local informations"""
        print(user)
        self.dm_queue.put("User %s joined the Mumble server" % user['name'])
            
    def user_removed(self, user, *args):
        """a user has disconnected"""
        print(user)
        self.dm_queue.put("User %s left the Mumble server" % user['name'])

def run(dm_queue, config):
    bot = MumbleBot(dm_queue, config.server, config.port, config.nickname, config.password)
    bot.loop()
