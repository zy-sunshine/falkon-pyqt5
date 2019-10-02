class QtUtil(object):
    def qDeleteAll(self, objs):
        if not objs:
            return
        for obj in objs:
            obj.deleteLater()

qtUtil = QtUtil()
