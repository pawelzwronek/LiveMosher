from enum import Enum


class Script:
    class Type(Enum):
        MAIN = 1
        HELPER = 2

    def __init__(self, path = '', parameters='', buildin=False):
        self.path = path
        self.parameters = parameters
        self.type = Script.Type.MAIN
        self.is_filter = False  # -vf script="script.js"
        self.is_in_project = False
        self.buildin = buildin
