"""
argh
"""

import os
import hashlib

class RoamerEntry(object):
    """
    argh
    """
    def __init__(self, name, directory):
        self.directory = directory
        self.name = name
        self.path = os.path.join(str(directory), name)
        self.full_digest = hashlib.sha224(self.path).hexdigest()
        self.digest = self.full_digest[0:7]

    def __str__(self):
        return "%s | %s" % (self.name, self.digest)
