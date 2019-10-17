from PyQt5.Qt import QColor
from PyQt5.Qt import QPoint
from PyQt5.Qt import Qt
from PyQt5.Qt import QApplication
from PyQt5.Qt import QLinearGradient
from PyQt5.Qt import QPixmapCache
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QPainter
from PyQt5.Qt import QRect
from PyQt5.Qt import QSize
from PyQt5.Qt import QImage
from PyQt5 import sip

from mc.common import const
from mc.common.globalvars import gVar

def clamp(x):
    '''
    @param: x float
    @return: int
    '''
    val = x > 255 and 255 or int(x)
    return max(0, val)

class StyleHelper(object):
    DEFAULT_BASE_COLOR = 0x666666

    def __init__(self):
        # Invalid by default, setBaseColor needs to be called at least once
        self._baseColor = QColor()
        self._requestedBaseColor = QColor()

    def sidebarFontSize(self):
        '''
        @brief: Height of the project explorer navigation bar
        '''
        if const.OS_MACOS:
            return 10
        else:
            return 7.5

    def requestedBaseColor(self):
        '''
        @brief: This is our color table, all colors derive from baseColor
        @return: QColor
        '''
        return self._requestedBaseColor

    def baseColor(self, lightColored=False):
        '''
        @return: QColor
        '''
        if not lightColored:
            return self._baseColor
        else:
            return self._baseColor.lighter(230)

    def panelTextColor(self, lightColored=False):
        '''
        @return: QColor
        '''
        if not lightColored:
            return Qt.white
        else:
            return Qt.black

    def highlightColor(self, lightColored=False):
        '''
        @return: QColor
        '''
        result = self.baseColor(lightColored)
        if not lightColored:
            result.setHsv(result.hue(), clamp(result.saturation()),
                    clamp(result.value() * 1.16))
        else:
            result.setHsv(result.hue(), clamp(result.saturation()),
                    clamp(result.value() * 1.06))
        return result

    def shadowColor(self, lightColored=False):
        '''
        @return: QColor
        '''
        result = self.baseColor(lightColored)
        result.setHsv(result.hue(), clamp(result.saturation() * 1.1),
                clamp(result.value() * 0.70))
        return result

    def borderColor(self, lightColored=False):
        '''
        @return: QColor
        '''
        result = self.baseColor(lightColored)
        result.setHsv(result.hue(), result.saturation(),
                clamp(result.value() / 2))
        return result

    def sidebarHighlight(self):
        '''
        @return: QColor
        '''
        return QColor(255, 255, 255, 40)

    def sidebarShadow(self):
        '''
        @return: QColor
        '''
        return QColor(0, 0, 0, 40)

    def setBaseColor(self, newColor):
        '''
        @brief: Sets the base color and makes sure all top level widgets are updated
        @note: We try to ensure that the actual color used are within
            reasonable bounds while generating the actual baseColor
            from the import user request.
        @param: color QColor
        '''
        self._requestedBaseColor = newColor

        color = QColor()
        color.setHsv(newColor.hue(), newColor.saturation() * 0.7,
                64 + newColor.value() / 3)

        if color.isValid() and color != self._baseColor:
            self._baseColor = color
            for widget in QApplication.topLevelWidgets():
                widget.update()

    def verticalGradientHelper(self, painter, spanRect, rect, lightColored=False):
        '''
        @brief: Gradients used for panels
        @param: painter QPainter
        @param: spanRect QRect
        @param: rect QRect
        @param: lightColored bool
        '''
        highlight = self.highlightColor(lightColored)
        shadow = self.shadowColor(lightColored)
        grad = QLinearGradient(spanRect.topRight(), spanRect.topLeft())
        grad.setColorAt(0, highlight.lighter(117))
        grad.setColorAt(1, shadow.darker(109))
        painter.fillRect(rect, grad)

        light = QColor(255, 255, 255, 80)
        painter.setPen(light)
        painter.drawLine(rect.topRight() - QPoint(1, 0), rect.bottomRight() - QPoint(1, 0))
        dark = QColor(0, 0, 0, 90)
        painter.setPen(dark)
        painter.drawLine(rect.topLeft(), rect.bottomLeft())

    def verticalGradient(self, painter, spanRect, clipRect, lightColored=False):
        '''
        @brief: Gradients used for panels
        @param: painter QPainter
        @param: spanRect QRect
        @param: clipRect QRect
        @param: lightColored bool
        '''
        if self.usePixmapCache():
            key = ''
            keyColor = self.baseColor(lightColored)
            key = 'mh_vertical %s %s %s %s %s' % (
                spanRect.width(), spanRect.height(), clipRect.width(),
                clipRect.height(), keyColor.rgb())

            pixmap = QPixmapCache.find(key)
            if not pixmap:
                pixmap = QPixmap(clipRect.size())
                p = QPainter(pixmap)
                rect = QRect(0, 0, clipRect.width(), clipRect.height())
                self.verticalGradientHelper(p, spanRect, rect, lightColored)
                p.end()
                QPixmapCache.insert(key, pixmap)

            painter.drawPixmap(clipRect.topLeft(), pixmap)
        else:
            self.verticalGradientHelper(painter, spanRect, clipRect, lightColored)

    def usePixmapCache(self):
        return False

    def drawIconWithShadow(self, icon, rect, painter, iconMode, radius=3,
            color=QColor(0, 0, 0, 130), offset=QPoint(1, -2)):
        '''
        @brief: Draw a cached pixmap with shadow
        @param: icon QIcon
        @param: rect QRect
        @param: painter QPainter
        @param: iconMode QIcon.Mode
        @param: radius int
        @param: color QColor
        @param: offset QPoint
        '''
        cache = QPixmap()
        pixmapName = 'icon %s %s %s' % (icon.cacheKey(), iconMode, rect.height())

        cache = QPixmapCache.find(pixmapName)
        if not cache:
            px = icon.pixmap(rect.size(), iconMode)
            px.setDevicePixelRatio(gVar.app.devicePixelRatio())
            cache = QPixmap(px.size() + QSize(radius * 2, radius * 2))
            cache.setDevicePixelRatio(px.devicePixelRatioF())
            cache.fill(Qt.transparent)

            cachePainter = QPainter(cache)

            # Draw shadow
            tmp = QImage(px.size() + QSize(radius * 2, radius * 2 + 1),
                    QImage.Format_ARGB32_Premultiplied)
            tmp.setDevicePixelRatio(px.devicePixelRatioF())
            tmp.fill(Qt.transparent)

            tmpPainter = QPainter(tmp)

            tmpPainter.setCompositionMode(QPainter.CompositionMode_Source)
            tmpPainter.drawPixmap(QPoint(radius, radius), px)
            tmpPainter.end()

            # blur the alpha channel
            blurred = QImage(tmp.size(), QImage.Format_ARGB32_Premultiplied)
            blurred.fill(Qt.transparent)
            blurPainter = QPainter(blurred)
            # TODO:
            #qt_blurImage(blurPainter, tmp, radius, False, True)
            blurPainter.end()

            tmp = blurred

            # blacken the image...
            tmpPainter.begin(tmp)
            tmpPainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tmpPainter.fillRect(tmp.rect(), color)
            tmpPainter.end()

            tmpPainter.begin(tmp)
            tmpPainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tmpPainter.fillRect(tmp.rect(), color)
            tmpPainter.end()

            # draw the blurred drop shadow...
            cachePainter.drawImage(QRect(0, 0, cache.rect().width() / cache.devicePixelRatioF(),
                cache.rect().height() / cache.devicePixelRatioF()), tmp)
            # Draw the actual pixmap...
            cachePainter.drawPixmap(QPoint(radius, radius) + offset, px)
            if self.usePixmapCache():
                QPixmapCache.insert(pixmapName, cache)

            sip.delete(cachePainter)
            sip.delete(tmpPainter)
            sip.delete(blurPainter)

        targetRect = QRect(cache.rect())
        targetRect.setWidth(cache.rect().width() / cache.devicePixelRatioF())
        targetRect.setHeight(cache.rect().height() / cache.devicePixelRatioF())
        targetRect.moveCenter(rect.center())
        painter.drawPixmap(targetRect.topLeft() - offset, cache)

styleHelper = StyleHelper()
