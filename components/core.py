from components.networking import Networking
from components.database import Database
from components.site import Site
from threading import Thread

class Core:
    def __init__(self):
        pass

    def start(self):

        db = Database()
        nw = Networking(db)
        site_thread = Thread(target=Site)
        site_thread.start()
        nw.startserving()

