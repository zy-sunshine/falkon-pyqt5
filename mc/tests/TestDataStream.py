from sys import argv
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QUrl

class ObjType(object):
    def __init__(self):
        self.test1 = QUrl('http://www.baidu.com')
        self.test2 = 'abc'
        self.test3 = 3

    def __getstate__(self):
        print('__getstate__')
        result = dict(self.__dict__)
        result['test1'] = result['test1'].toEncoded()
        return result

    def __setstate__(self, state):
        print('__setstate__')
        for key, val in state.items():
            if key == 'test1':
                self.test1 = QUrl.fromEncoded(val)
            else:
                setattr(self, key, val)

if argv[1] == 'dump':
    data = QByteArray()
    ds = QDataStream(data, QIODevice.WriteOnly)
    ds.writeInt(1)
    obj = ObjType()
    ds.writeQVariant([obj, obj])
    print(data)
    with open('test.dat', 'wb') as fp:
        fp.write(data)
elif argv[1] == 'load':
    with open('test.dat', 'rb') as fp:
        data = fp.read()
    dsOut = QDataStream(QByteArray(data))
    ver = dsOut.readInt()
    lst = dsOut.readQVariant()
    print(lst[0].test1)
    print(lst)
else:
    raise RuntimeError('action should be dump or load')
