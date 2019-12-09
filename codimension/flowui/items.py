# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2015-2017  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Various items used to represent a control flow on a virtual canvas"""

from html import escape
from ui.qt import (Qt, QPointF, QPen, QBrush, QGraphicsRectItem, QGraphicsItem,
                   QGraphicsPathItem, QStyleOptionGraphicsItem, QStyle)
from utils.globals import GlobalData
from .auxitems import Connector, Text, BadgeItem
from .cml import CMLVersion, CMLsw
from .routines import getCommentBoxPath, distance
from .colormixin import ColorMixin
from .iconmixin import IconMixin
from .cellelement import CellElement


class CodeBlockCell(CellElement, ColorMixin, QGraphicsRectItem):

    """Represents a single code block"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.codeBlockBGColor,
                            self.canvas.settings.codeBlockFGColor,
                            self.canvas.settings.codeBlockBorderColor)
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.CODE_BLOCK
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        vPadding = 2 * (settings.vCellPadding + settings.vTextPadding)
        self.minHeight = self.__textRect.height() + vPadding
        hPadding = 2 * (settings.hCellPadding + settings.hTextPadding)
        self.minWidth = max(self.__textRect.width() + hPadding,
                            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + self.height)
        scene.addItem(self.connector)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)
        scene.addItem(self)

    def paint(self, painter, option, widget):
        """Draws the code block"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        rectWidth = self.minWidth - 2 * settings.hCellPadding
        rectHeight = self.minHeight - 2 * settings.vCellPadding

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            painter.setPen(pen)
        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawRect(self.baseX + settings.hCellPadding,
                         self.baseY + settings.vCellPadding,
                         rectWidth, rectHeight)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)

        textWidth = self.__textRect.width() + 2 * settings.hTextPadding
        textShift = (rectWidth - textWidth) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding +
            settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return 'Code block at lines ' + \
               str(lineRange[0]) + "-" + str(lineRange[1])


class ReturnCell(CellElement, ColorMixin, IconMixin, QGraphicsRectItem):

    """Represents a single return statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.returnBGColor,
                            self.canvas.settings.returnFGColor,
                            self.canvas.settings.returnBorderColor)
        IconMixin.__init__(self, canvas, 'return.svg', 'return')
        QGraphicsRectItem.__init__(self)
        self.kind = CellElement.RETURN
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def _getText(self):
        """Provides the text"""
        if self._text is None:
            self._text = self.getReplacementText()
            displayText = self.ref.getDisplayValue()
            if self._text is None:
                self._text = displayText
                if not self._text:
                    self._text = "None"
            else:
                if displayText:
                    self.setToolTip("<pre>" + escape(displayText) + "</pre>")
            if self.canvas.settings.noContent:
                if displayText:
                    self.setToolTip("<pre>" + escape(displayText) + "</pre>")
                self._text = ''
        return self._text

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        vPadding = 2 * (settings.vCellPadding + settings.vTextPadding)
        self.minHeight = self.__textRect.height() + vPadding
        self.minWidth = max(
            self.__textRect.width() + 2 * settings.hCellPadding +
            settings.hTextPadding + settings.returnRectRadius +
            2 * settings.hTextPadding + self.iconItem.iconWidth(),
            settings.minWidth)

        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + settings.vCellPadding)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)

        self.iconItem.setPos(
            baseX + settings.hCellPadding + settings.hTextPadding,
            baseY + self.minHeight/2 - self.iconItem.iconHeight()/2)

        scene.addItem(self.connector)
        scene.addItem(self)
        scene.addItem(self.iconItem)

    def paint(self, painter, option, widget):
        """Draws the code block"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            pen = QPen(settings.selectColor)
            pen.setWidth(settings.selectPenWidth)
        else:
            pen = QPen(self.borderColor)
        painter.setPen(pen)

        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawRoundedRect(
            self.baseX + settings.hCellPadding,
            self.baseY + settings.vCellPadding,
            self.minWidth - 2 * settings.hCellPadding,
            self.minHeight - 2 * settings.vCellPadding,
            settings.returnRectRadius, settings.returnRectRadius)
        lineXBase = self.baseX + settings.hCellPadding
        lineXPos = lineXBase + self.iconItem.iconWidth() + 2 * settings.hTextPadding
        lineYBase = self.baseY + settings.vCellPadding
        painter.drawLine(
            lineXPos, lineYBase,
            lineXPos, lineYBase + self.minHeight - 2 * settings.vCellPadding)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)

        availWidth = self.minWidth - 2 * settings.hCellPadding - \
                     self.iconItem.iconWidth() - 2 * settings.hTextPadding - \
                     settings.hTextPadding - settings.returnRectRadius
        textShift = (availWidth - self.__textRect.width()) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding + self.iconItem.iconWidth() +
            3 * settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getLineRange(self):
        """Provides the item line range"""
        if self.ref.value is not None:
            return [self.ref.body.beginLine, self.ref.value.endLine]
        return [self.ref.body.beginLine, self.ref.body.endLine]

    def getAbsPosRange(self):
        """Provides the absolute position range"""
        if self.ref.value is not None:
            return [self.ref.body.begin, self.ref.value.end]
        return [self.ref.body.begin, self.ref.body.end]

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return "Return at lines " + str(lineRange[0]) + "-" + str(lineRange[1])

    def getDistance(self, absPos):
        """Provides a distance between the absPos and the item"""
        if self.ref.value is not None:
            return distance(absPos, self.ref.body.begin, self.ref.value.end)
        return distance(absPos, self.ref.body.begin, self.ref.body.end)

    def getLineDistance(self, line):
        """Provides a distance between the line and the item"""
        if self.ref.value is not None:
            return distance(line, self.ref.body.beginLine,
                            self.ref.value.endLine)
        return distance(line, self.ref.body.beginLine, self.ref.body.endLine)


class RaiseCell(CellElement, ColorMixin, IconMixin, QGraphicsRectItem):

    """Represents a single raise statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.raiseBGColor,
                            self.canvas.settings.raiseFGColor,
                            self.canvas.settings.raiseBorderColor)
        IconMixin.__init__(self, canvas, 'raise.svg', 'raise')
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.RAISE
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        vPadding = 2 * (settings.vCellPadding + settings.vTextPadding)
        self.minHeight = self.__textRect.height() + vPadding
        self.minWidth = max(
            self.__textRect.width() + 2 * settings.hCellPadding +
            settings.hTextPadding + settings.returnRectRadius +
            2 * settings.hTextPadding + self.iconItem.iconWidth(),
            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + settings.vCellPadding)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)

        self.iconItem.setPos(
            baseX + settings.hCellPadding + settings.hTextPadding,
            baseY + self.minHeight/2 - self.iconItem.iconHeight()/2)

        scene.addItem(self.connector)
        scene.addItem(self)
        scene.addItem(self.iconItem)

    def paint(self, painter, option, widget):
        """Draws the raise statement"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            painter.setPen(pen)

        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawRoundedRect(self.baseX + settings.hCellPadding,
                                self.baseY + settings.vCellPadding,
                                self.minWidth - 2 * settings.hCellPadding,
                                self.minHeight - 2 * settings.vCellPadding,
                                settings.returnRectRadius,
                                settings.returnRectRadius)
        lineXBase = self.baseX + settings.hCellPadding
        lineXPos = lineXBase + self.iconItem.iconWidth() + 2 * settings.hTextPadding
        lineYBase = self.baseY + settings.vCellPadding
        painter.drawLine(
            lineXPos, lineYBase,
            lineXPos, lineYBase + self.minHeight - 2 * settings.vCellPadding)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)
        availWidth = self.minWidth - 2 * settings.hCellPadding - \
                     self.iconItem.iconWidth() - 2 * settings.hTextPadding - \
                     settings.hTextPadding - settings.returnRectRadius
        textShift = (availWidth - self.__textRect.width()) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding + self.iconItem.iconWidth() +
            3 * settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getLineRange(self):
        """Provides the line range"""
        if self.ref.value is not None:
            return [self.ref.body.beginLine, self.ref.value.endLine]
        return [self.ref.body.beginLine, self.ref.body.endLine]

    def getAbsPosRange(self):
        """Provides the absolute position range"""
        if self.ref.value is not None:
            return [self.ref.body.begin, self.ref.value.end]
        return [self.ref.body.begin, self.ref.body.end]

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return "Raise at lines " + str(lineRange[0]) + "-" + str(lineRange[1])

    def getDistance(self, absPos):
        """Provides a distance between the absPos and the item"""
        if self.ref.value is not None:
            return distance(absPos, self.ref.body.begin, self.ref.value.end)
        return distance(absPos, self.ref.body.begin, self.ref.body.end)

    def getLineDistance(self, line):
        """Provides a distance between the line and the item"""
        if self.ref.value is not None:
            return distance(line,
                            self.ref.body.beginLine, self.ref.value.endLine)
        return distance(line, self.ref.body.beginLine, self.ref.body.endLine)


class AssertCell(CellElement, ColorMixin, IconMixin, QGraphicsRectItem):

    """Represents a single assert statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.assertBGColor,
                            self.canvas.settings.assertFGColor,
                            self.canvas.settings.assertBorderColor)
        IconMixin.__init__(self, canvas, 'assert.svg', 'assert')
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.ASSERT
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        # for an arrow box
        singleCharRect = self.getBoundingRect('W')
        self.__diamondHeight = singleCharRect.height() + 2 * settings.vTextPadding
        self.__diamondWidth = settings.ifWidth * 2 + singleCharRect.width() + 2 * settings.hTextPadding

        self.minHeight = self.__textRect.height() + \
                         2 * settings.vCellPadding + 2 * settings.vTextPadding
        self.minWidth = max(
            self.__textRect.width() + 2 * settings.hCellPadding +
            2 * settings.hTextPadding + self.__diamondWidth,
            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + self.height)
        scene.addItem(self.connector)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)

        settings = self.canvas.settings
        self.iconItem.setPos(
            baseX + self.__diamondWidth / 2 +
            settings.hCellPadding - self.iconItem.iconWidth() / 2,
            baseY + self.minHeight / 2 - self.iconItem.iconHeight() / 2)

        scene.addItem(self)
        scene.addItem(self.iconItem)

    def paint(self, painter, option, widget):
        """Draws the code block"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            painter.setPen(pen)

        dHalf = int(self.__diamondHeight / 2.0)
        dx1 = self.baseX + settings.hCellPadding
        dy1 = self.baseY + int(self.minHeight / 2)
        dx2 = dx1 + settings.ifWidth
        dy2 = dy1 - dHalf
        dx3 = dx1 + self.__diamondWidth - settings.ifWidth
        dy3 = dy2
        dx4 = dx3 + settings.ifWidth
        dy4 = dy1
        dx5 = dx3
        dy5 = dy2 + 2 * dHalf
        dx6 = dx2
        dy6 = dy5

        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawPolygon(QPointF(dx1, dy1), QPointF(dx2, dy2),
                            QPointF(dx3, dy3), QPointF(dx4, dy4),
                            QPointF(dx5, dy5), QPointF(dx6, dy6))

        painter.drawRect(dx4 + 1, self.baseY + settings.vCellPadding,
                         self.minWidth - 2 * settings.hCellPadding -
                         self.__diamondWidth,
                         self.minHeight - 2 * settings.vCellPadding)


        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)
        availWidth = \
            self.minWidth - 2 * settings.hCellPadding - self.__diamondWidth
        textWidth = self.__textRect.width() + 2 * settings.hTextPadding
        textShift = (availWidth - textWidth) / 2
        painter.drawText(
            dx4 + settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getLineRange(self):
        """Provides the line range"""
        if self.ref.message is not None:
            return [self.ref.body.beginLine, self.ref.message.endLine]
        if self.ref.test is not None:
            return[self.ref.body.beginLine, self.ref.test.endLine]
        return [self.ref.body.beginLine, self.ref.body.endLine]

    def getAbsPosRange(self):
        """Provides the absolute position range"""
        if self.ref.message is not None:
            return [self.ref.body.begin, self.ref.message.end]
        if self.ref.test is not None:
            return[self.ref.body.begin, self.ref.test.end]
        return [self.ref.body.begin, self.ref.body.end]

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return "Assert at lines " + str(lineRange[0]) + "-" + str(lineRange[1])

    def getDistance(self, absPos):
        """Provides a distance between the absPos and the item"""
        if self.ref.message is not None:
            return distance(absPos, self.ref.body.begin, self.ref.message.end)
        if self.ref.test is not None:
            return distance(absPos, self.ref.body.begin, self.ref.test.end)
        return distance(absPos, self.ref.body.begin, self.ref.body.end)

    def getLineDistance(self, line):
        """Provides a distance between the line and the item"""
        if self.ref.message is not None:
            return distance(line,
                            self.ref.body.beginLine, self.ref.message.endLine)
        if self.ref.test is not None:
            return distance(line,
                            self.ref.body.beginLine, self.ref.test.endLine)
        return distance(line, self.ref.body.beginLine, self.ref.body.endLine)


class SysexitCell(CellElement, ColorMixin, IconMixin, QGraphicsRectItem):

    """Represents a single sys.exit(...) statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.sysexitBGColor,
                            self.canvas.settings.sysexitFGColor,
                            self.canvas.settings.sysexitBorderColor)
        IconMixin.__init__(self, canvas, 'sysexit.svg', 'sys.exit()')
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.SYSEXIT
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        self.minHeight = \
            self.__textRect.height() + \
            2 * (settings.vCellPadding + settings.vTextPadding)
        self.minWidth = max(
            self.__textRect.width() + 2 * settings.hCellPadding +
            settings.hTextPadding + settings.returnRectRadius +
            2 * settings.hTextPadding + self.iconItem.iconWidth(),
            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + settings.vCellPadding)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)

        self.iconItem.setPos(
            baseX + settings.hCellPadding + settings.hTextPadding,
            baseY + self.minHeight/2 - self.iconItem.iconHeight() / 2)

        scene.addItem(self.connector)
        scene.addItem(self)
        scene.addItem(self.iconItem)

    def paint(self, painter, option, widget):
        """Draws the sys.exit call"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            painter.setPen(pen)

        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawRoundedRect(self.baseX + settings.hCellPadding,
                                self.baseY + settings.vCellPadding,
                                self.minWidth - 2 * settings.hCellPadding,
                                self.minHeight - 2 * settings.vCellPadding,
                                settings.returnRectRadius,
                                settings.returnRectRadius)
        lineXBase = self.baseX + settings.hCellPadding
        lineXPos = lineXBase + self.iconItem.iconWidth() + 2 * settings.hTextPadding
        lineYBase = self.baseY + settings.vCellPadding
        painter.drawLine(
            lineXPos, lineYBase,
            lineXPos, lineYBase + self.minHeight - 2 * settings.vCellPadding)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)
        availWidth = \
            self.minWidth - 2 * settings.hCellPadding - self.iconItem.iconWidth() - \
            2 * settings.hTextPadding - \
            settings.hTextPadding - settings.returnRectRadius
        textShift = (availWidth - self.__textRect.width()) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding + self.iconItem.iconWidth() +
            3 * settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getSelectTooltip(self):
        """Provides tooltip"""
        lineRange = self.getLineRange()
        return "Sys.exit() at lines " + str(lineRange[0]) + \
               "-" + str(lineRange[1])


class ImportCell(CellElement, ColorMixin, IconMixin, QGraphicsRectItem):

    """Represents a single import statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.importBGColor,
                            self.canvas.settings.importFGColor,
                            self.canvas.settings.importBorderColor)
        IconMixin.__init__(self, canvas, 'import.svg', 'import')
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.IMPORT
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())
        self.minHeight = \
            self.__textRect.height() + 2 * settings.vCellPadding + \
            2 * settings.vTextPadding
        self.minWidth = max(
            self.__textRect.width() + 2 * settings.hCellPadding +
            2 * settings.hTextPadding + self.iconItem.iconWidth() +
            2 * settings.hTextPadding, settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + self.height)
        scene.addItem(self.connector)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)

        self.iconItem.setPos(
            baseX + settings.hCellPadding + settings.hTextPadding,
            baseY + self.minHeight / 2 - self.iconItem.iconHeight() / 2)
        scene.addItem(self)
        scene.addItem(self.iconItem)

    def paint(self, painter, option, widget):
        """Draws the import statement"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            painter.setPen(pen)
        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawRect(self.baseX + settings.hCellPadding,
                         self.baseY + settings.vCellPadding,
                         self.minWidth - 2 * settings.hCellPadding,
                         self.minHeight - 2 * settings.vCellPadding)
        painter.drawLine(self.baseX + settings.hCellPadding +
                         self.iconItem.iconWidth() + 2 * settings.hTextPadding,
                         self.baseY + settings.vCellPadding,
                         self.baseX + settings.hCellPadding +
                         self.iconItem.iconWidth() + 2 * settings.hTextPadding,
                         self.baseY + self.minHeight - settings.vCellPadding)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)
        textRectWidth = self.minWidth - 2 * settings.hCellPadding - \
                        4 * settings.hTextPadding - self.iconItem.iconWidth()
        textShift = (textRectWidth - self.__textRect.width()) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding + self.iconItem.iconWidth() +
            3 * settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return "Import at lines " + str(lineRange[0]) + "-" + str(lineRange[1])


class IfCell(CellElement, ColorMixin, QGraphicsRectItem):

    """Represents a single if statement"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, ref, self.canvas.settings.ifBGColor,
                            self.canvas.settings.ifFGColor,
                            self.canvas.settings.ifBorderColor)
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.IF
        self.__textRect = None
        self.vConnector = None
        self.hConnector = None
        self.rightLabel = None
        self.yBelow = False

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        self.minHeight = self.__textRect.height() + \
                         2 * settings.vCellPadding + 2 * settings.vTextPadding
        self.minWidth = max(
            self.__textRect.width() +
            2 * settings.hCellPadding + 2 * settings.hTextPadding +
            2 * settings.ifWidth,
            settings.minWidth)
        self.minWidth += self.hShift * 2 * settings.openGroupHSpacer
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def __calcPolygon(self):
        """Calculates the polygon"""
        settings = self.canvas.settings

        shift = self.hShift * 2 * settings.openGroupHSpacer
        baseX = self.baseX + shift

        self.x1 = baseX + settings.hCellPadding
        self.y1 = self.baseY + self.minHeight / 2
        self.x2 = baseX + settings.hCellPadding + settings.ifWidth
        self.y2 = self.baseY + settings.vCellPadding
        self.x3 = baseX + self.minWidth - \
                  settings.hCellPadding - settings.ifWidth - shift
        self.y3 = self.y2
        self.x4 = self.x3 + settings.ifWidth
        self.y4 = self.y1
        self.x5 = self.x3
        self.y5 = self.baseY + (self.minHeight - settings.vCellPadding)
        self.x6 = self.x2
        self.y6 = self.y5

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        self.__calcPolygon()

        settings = self.canvas.settings
        hShift = self.hShift * 2 * settings.openGroupHSpacer
        self.baseX += hShift

        # Add the connectors as separate scene items to make the selection
        # working properly
        settings = self.canvas.settings
        self.vConnector = Connector(self.canvas,
                                    self.baseX + settings.mainLine,
                                    self.baseY,
                                    self.baseX + settings.mainLine,
                                    self.baseY + self.height)
        scene.addItem(self.vConnector)

        self.hConnector = Connector(self.canvas, self.x4, self.y4,
                                    self.baseX + self.width - hShift,
                                    self.y4)
        scene.addItem(self.hConnector)

        self.yBelow = CMLVersion.find(self.ref.leadingCMLComments,
                                      CMLsw) is not None
        if self.yBelow:
            self.rightBadge = BadgeItem(self, 'n')
            self.leftBadge = BadgeItem(self, 'y')

#            self.rightLabel = Text(self.canvas, "N")
#            f = self.rightLabel.font()
#            f.setBold(True)
#            self.rightLabel.setFont(f)
        else:
            self.rightBadge = BadgeItem(self, 'y')
            self.leftBadge = BadgeItem(self, 'n')

#            self.rightLabel = Text(self.canvas, "Y")

        self.rightBadge.setNeedRectangle(False)
        self.rightBadge.moveTo(self.x4 - self.rightBadge.width / 2,
                               self.y3 - self.rightBadge.height / 2)
        self.leftBadge.setNeedRectangle(False)
        self.leftBadge.moveTo(self.x1 - self.leftBadge.width / 2,
                              self.y3 - self.leftBadge.height / 2)

#        self.rightLabel.setPos(
##            self.x4 + 2,
#            self.y4 - self.rightLabel.boundingRect().height() - 2)
#        scene.addItem(self.rightLabel)

        penWidth = settings.selectPenWidth - 1
        self.setRect(self.x1 - penWidth, self.y2 - penWidth,
                     self.x4 - self.x1 + 2 * penWidth,
                     self.y6 - self.y2 + 2 * penWidth)
        scene.addItem(self)
        scene.addItem(self.rightBadge)
        scene.addItem(self.leftBadge)

        self.baseX -= hShift

    def paint(self, painter, option, widget):
        """Draws the code block"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

        brush = QBrush(self.bgColor)
        painter.setBrush(brush)
        painter.drawPolygon(
            QPointF(self.x1, self.y1), QPointF(self.x2, self.y2),
            QPointF(self.x3, self.y3), QPointF(self.x4, self.y4),
            QPointF(self.x5, self.y5), QPointF(self.x6, self.y6))

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setPen(pen)
        painter.setFont(settings.monoFont)
        availWidth = self.x3 - self.x2
        textWidth = self.__textRect.width() + 2 * settings.hTextPadding
        textShift = (availWidth - textWidth) / 2
        painter.drawText(
            self.x2 + settings.hTextPadding + textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return "If at lines " + str(lineRange[0]) + "-" + str(lineRange[1])


class MinimizedExceptCell(CellElement, QGraphicsPathItem):

    """Represents a minimized except block"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        QGraphicsPathItem.__init__(self)
        self.kind = CellElement.EXCEPT_MINIMIZED
        self.__text = None
        self.__textRect = None
        self.__leftEdge = None
        self.connector = None

        self.__vTextPadding = canvas.settings.vHiddenTextPadding
        self.__hTextPadding = canvas.settings.hHiddenTextPadding

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def __getText(self):
        """Provides the text"""
        if self.__text is None:
            self.__text = self.canvas.settings.hiddenExceptText
            #  + '[' + str(len(self.ref.exceptParts)) + ']'
            self.__setTooltip()
        return self.__text

    def __setTooltip(self):
        """Sets the item tooltip"""
        parts = []
        for part in self.ref.exceptParts:
            lines = part.getDisplayValue().splitlines()
            if len(lines) > 1:
                parts.append('except: ' + lines[0] + '...')
            elif len(lines) == 1:
                parts.append('except: ' + lines[0])
            else:
                parts.append('except:')
        self.setToolTip('<pre>' + escape('\n'.join(parts)) + '</pre>')

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self.__getText())

        self.minHeight = self.__textRect.height() + \
            2 * settings.vCellPadding + 2 * self.__vTextPadding
        self.minWidth = self.__textRect.width() + \
                        2 * settings.hCellPadding + 2 * self.__hTextPadding
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY
        self.__setupPath()
        scene.addItem(self.connector)
        scene.addItem(self)

    def __setupPath(self):
        """Sets the comment path"""
        settings = self.canvas.settings

        cellToTheLeft = self.canvas.cells[self.addr[1]][self.addr[0] - 1]
        boxWidth = self.__textRect.width() + \
                   2 * (settings.hCellPadding + self.__hTextPadding)
        self.__leftEdge = cellToTheLeft.baseX + cellToTheLeft.minWidth
        cellKind = self.canvas.cells[self.addr[1]][self.addr[0] - 1].kind

        self.__leftEdge = cellToTheLeft.baseX + cellToTheLeft.minWidth
        path = getCommentBoxPath(settings, self.__leftEdge, self.baseY,
                                 boxWidth, self.minHeight, True)

        height = min(self.minHeight / 2, cellToTheLeft.minHeight / 2)

        self.connector = Connector(
            self.canvas, self.__leftEdge + settings.hCellPadding,
            self.baseY + height,
            cellToTheLeft.baseX +
            cellToTheLeft.minWidth - settings.hCellPadding,
            self.baseY + height)

        # self.connector.penColor = settings.commentLineColor
        # self.connector.penWidth = settings.commentLineWidth
        self.connector.penStyle = Qt.DotLine

        self.setPath(path)

    def paint(self, painter, option, widget):
        """Draws the side comment"""
        settings = self.canvas.settings

        brush = QBrush(settings.exceptScopeBGColor)
        self.setBrush(brush)

        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            self.setPen(selectPen)
        else:
            pen = QPen(settings.exceptScopeBorderColor)
            pen.setWidth(settings.lineWidth)
            pen.setJoinStyle(Qt.RoundJoin)
            self.setPen(pen)

        # Hide the dotted outline
        itemOption = QStyleOptionGraphicsItem(option)
        if itemOption.state & QStyle.State_Selected != 0:
            itemOption.state = itemOption.state & ~QStyle.State_Selected
        QGraphicsPathItem.paint(self, painter, itemOption, widget)

        # Draw the text in the rectangle
        pen = QPen(settings.exceptScopeFGColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)
        painter.drawText(
            self.__leftEdge + settings.hCellPadding + self.__hTextPadding,
            self.baseY + settings.vCellPadding + self.__vTextPadding,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self.__getText())

    def mouseDoubleClickEvent(self, event):
        """Jump to the appropriate line in the text editor"""
        if self._editor:
            firstExcept = self.ref.exceptParts[0]
            GlobalData().mainWindow.raise_()
            GlobalData().mainWindow.activateWindow()
            self._editor.gotoLine(firstExcept.body.beginLine,
                                  firstExcept.body.beginPos)
            self._editor.setFocus()

    def getLineRange(self):
        """Provides the line range"""
        firstLineRange = self.ref.exceptParts[0].getLineRange()
        lastLineRange = self.ref.exceptParts[-1].getLineRange()
        return [firstLineRange[0], lastLineRange[1]]

    def getAbsPosRange(self):
        """Provides the absolute position range"""
        firstExcept = self.ref.exceptParts[0]
        lastExcept = self.ref.exceptParts[-1]
        return [firstExcept.begin, lastExcept.end]

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        count = len(self.ref.exceptParts)
        if count == 1:
            return 'Minimized except block at lines ' + \
                   str(lineRange[0]) + "-" + str(lineRange[1])
        return str(count) + ' minimized except blocks at lines ' + \
               str(lineRange[0]) + "-" + str(lineRange[1])

    def getDistance(self, absPos):
        """Provides a distance between the absPos and the item"""
        absPosRange = self.getAbsPosRange()
        return distance(absPos, absPosRange[0], absPosRange[1])

    def getLineDistance(self, line):
        """Provides a distance between the line and the item"""
        lineRange = self.getLineRange()
        return distance(line, lineRange[0], lineRange[1])
