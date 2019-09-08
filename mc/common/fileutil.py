from os import makedirs
from os.path import split as pathsplit
from os.path import join as pathjoin, exists as pathexists

class FileUtil(object):
    def ensurefiledir(self, fpath):
        bpath, fname = pathsplit(fpath)
        if not pathexists(bpath):
            makedirs(bpath)

fileUtil = FileUtil()
