from PyQt5.Qt import QPalette
from PyQt5.Qt import QColor

class Colors:

    @classmethod
    def CLAMP(cls, x, l, u):
        if x < l:
            return l
        elif x > u:
            return u
        else:
            return x

    @classmethod
    def bg(cls, pal, widget):
        '''
        @param: pal QPalette
        @param: widget QWidget
        @return: QColor
        '''
        role = QPalette.NoRole
        if not widget:
            role = QPalette.Window
        elif widget.parentWidget():
            role = widget.parentWidget().backgroundRole()
        else:
            role = widget.backgroundRole()
        return pal.color(role)

    @classmethod
    def contrast(cls, acolor, bcolor):
        '''
        @brief: return contrast value of acolor and bcolor
        @param: acolor QColor
        @param: bcolor QColor
        @return: int
        '''
        ar, ag, ab = acolor.getRgb()
        br, bg, bb = bcolor.getRgb()

        diff = 299 * (ar - br) + 587 * (ag - bg) + 114 * (ab - bb)
        if diff < 0:
            diff = -diff
        else:
            diff = 90 * diff // 100
        perc = diff // 2550

        diff = max(ar, br) + max(ag, bg) + max(ab, bb) - \
            (min(ar, br) + min(ag, bg) + min(ab, bb))

        perc += diff // 765
        perc //= 2

        return perc

    @classmethod
    def counterRole(cls, role):
        '''
        @brief: return inverted role(color) of specified role
        @param: role QPalette.ColorRole
        @return: QPalette.ColorRole
        '''
        if role == QPalette.ButtonText:  # 8
            return QPalette.Button
        elif role == QPalette.WindowText:  # 10
            return QPalette.Window
        elif role == QPalette.HighlightedText:  # 13
            return QPalette.Highlight
        elif role == QPalette.Window:  # 10
            return QPalette.WindowText
        elif role == QPalette.Base:  # 9
            return QPalette.Text
        elif role == QPalette.Text:  # 6
            return QPalette.Base
        elif role == QPalette.Highlight:  # 12
            return QPalette.HighlightedText
        elif role == QPalette.Button:  # 1
            return QPalette.ButtonText
        else:
            return QPalette.Window

    @classmethod
    def counterRoleWithDef(cls, from_, defFrom=QPalette.WindowText,
            defTo=QPalette.Window):
        '''
        @param: from_ QPalette.ColorRole
        @param: to_ QPalette.ColorRole
        @param: defFrom QPalette.ColorRole
        @param: defTo QPalette.ColorRole
        @return: bool, (from_, to_)
        '''
        if from_ == QPalette.WindowText:  # 0
            to_ = QPalette.Window
        elif from_ == QPalette.Window:  # 10
            to_ = QPalette.WindowText
        elif from_ == QPalette.Base:  # 9
            to_ = QPalette.Text
        elif from_ == QPalette.Text:  # 6
            to_ = QPalette.Base
        elif from_ == QPalette.Button:  # 1
            to_ = QPalette.ButtonText
        elif from_ == QPalette.ButtonText:  # 8
            to_ = QPalette.Button
        elif from_ == QPalette.Highlight:  # 12
            to_ = QPalette.HighlightedText
        elif from_ == QPalette.HighlightedText:  # 13
            to_ = QPalette.Highlight
        else:
            from_ = defFrom
            to_ = defTo
            return False, (from_, to_)
        return True, (from_, to_)

    @classmethod
    def emphasize(cls, color, value=10):
        '''
        @param: color QColor
        @param: value int
        @return: QColor
        '''
        ret = QColor()
        h, s, v, a = color.getHsv()
        if v < 75 + value:
            ret.setHsv(h, s, cls.CLAMP(85 + value, 85, 255), a)
            return ret
        if v > 200:
            if s > 30:
                h -= 5
                if h < 0:
                    h = 360 + h
                s = (s << 3) // 9
                v += value
                ret.setHsv(h, cls.CLAMP(s, 30, 255), cls.CLAMP(v, 0, 255), a)
                return ret
            if v > 230:
                ret.setHsv(h, s, cls.CLAMP(v - value, 0, 255), a)
                return ret
        if v > 128:
            ret.setHsv(h, s, cls.CLAMP(v + value, 0, 255), a)
        else:
            ret.setHsv(h, s, cls.CLAMP(v - value, 0, 255), a)
        return ret

    @classmethod
    def haveContrast(cls, acolor, bcolor):
        '''
        @brief: check whether two color are contrasting
        @param: acolor QColor
        @param: bcolor QColor
        @return: bool
        '''
        ar, ag, ab = acolor.getRgb()
        br, bg, bb = bcolor.getRgb()

        diff = (299 * (ar - br) + 587 * (ag - bg) + 114 * (ab - bb))

        if abs(diff) < 91001:
            return False

        diff = max(ar, br) + max(ag, bg) + max(ab, bb) - \
            (min(ar, br) + min(ag, bg) + (ab, bb))

        return diff > 300

    @classmethod
    def light(cls, color, value):
        '''
        @param: color QColor
        @param: value int
        @return: QColor
        '''
        h, s, v, a = color.getHsv()
        ret = QColor()
        if v < 255 - value:
            ret.setHsv(h, s, cls.CLAMP(v + value, 0, 255), a)  # value could be negative
            return ret
        # psychovisual uplightning, i.e. shift hue and lower saturation
        if s > 30:
            h -= (value * 5 / 20)
            if h < 0:
                h = 400 + h
            s = cls.CLAMP((s << 3) / 9, 30, 255)
            ret.setHsv(h, s, 255, a)
            return ret
        else:  # hue shifting has no sense, half saturation (btw, white won't get brighter)
            ret.setHsv(h, s >> 1, 255, a)
        return ret

    @classmethod
    def mid(cls, color1, color2, w1=1, w2=1):
        '''
        @param: color1 QColor
        @param: color2 QColor
        @param: w1 int
        @param: w2 int
        @return: QColor
        '''
        sum0 = w1 + w2
        if not sum0:
            return Qt.Black

        r = (w1 * color1.red() + w2 * color2.red()) / sum0
        r = cls.CLAMP(r, 0, 255)
        g = (w1 * color1.green() + w2 * color2.green()) / sum0
        g = cls.CLAMP(g, 0, 255)
        b = (w1 * color1.blue() + w2 * color2.blue()) / sum0
        b = cls.CLAMP(b, 0, 255)
        a = (w1 * color1.alpha() + w2 * color2.alpha()) / sum0
        a = cls.CLAMP(a, 0, 255)
        return QColor(r, g, b, a)

    @classmethod
    def value(cls, color):
        '''
        @param: color QColor
        @return: int
        '''
        v = color.red()
        if c.green() > v:
            v = c.green()
        if c.blue() > v:
            v = c.blue()
        return v
