import logging


class Log(logging.Logger):
    def __init__(self, name: str):
        super().__init__(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)
        self.setLevel(logging.DEBUG)
