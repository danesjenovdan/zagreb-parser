import logging
logger = logging.getLogger('base logger')

class BaseParser(object):
    def __init__(self, storage):
        self.storage = storage
