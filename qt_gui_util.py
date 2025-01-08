
from PySide6.QtCore import QRectF, QRect, Qt
from PySide6.QtGui import QResizeEvent, QTextCursor, QPaintEvent, QPainter, QColor
from PySide6.QtWidgets import QTextEdit, QApplication
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget


class QTextEditHighlighter(QTextEdit):
    # this class was edited from https://stackoverflow.com/a/74117643 
    def __init__(self):
        # Line numbers
        QTextEdit.__init__(self)
        self.lineNumberArea = QTLineNumberArea(self)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        m = max(1, self.document().blockCount())
        while m >= 10:
            m /= 10
            digits += 1
        space = 13 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, newBlockCount: int):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberAreaRect(self, rect_f: QRectF):
        self.updateLineNumberArea()

    def updateLineNumberAreaInt(self, slider_pos: int):
        self.updateLineNumberArea()

    def updateLineNumberArea(self):
        """        
        When the signal is emitted, the sliderPosition has been adjusted according to the action,
        but the value has not yet been propagated (meaning the valueChanged() signal was not yet emitted),
        and the visual display has not been updated. In slots connected to self signal you can thus safely
        adjust any action by calling setSliderPosition() yourself, based on both the action and the
        slider's value.
        """
        
        # Make sure the sliderPosition triggers one last time the valueChanged() signal with the actual value !!!!
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
    
        # Since "QTextEdit" does not have an "updateRequest(...)" signal, we chose
        # to grab the imformations from "sliderPosition()" and "contentsRect()".
        # See the necessary connections used (Class constructor implementation part).
    
        rect = self.contentsRect()

        self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        self.updateLineNumberAreaWidth(0)
        
        dy = self.verticalScrollBar().sliderPosition()
        if dy > -1:
            self.lineNumberArea.scroll(0, dy)
    
        # Addjust slider to alway see the number of the currently being edited line...
        first_block_id = self.getFirstVisibleBlockId()
        if first_block_id == 0 or self.textCursor().block().blockNumber() == first_block_id-1:
            self.verticalScrollBar().setSliderPosition(dy-self.document().documentMargin())
    
    #    # Snap to first line (TODO...)
    #    if first_block_id > 0:
    #        slider_pos = self.verticalScrollBar().sliderPosition()
    #        prev_block_height = (int) self.document().documentLayout().blockBoundingRect(self.document().findBlockByNumber(first_block_id-1)).height()
    #        if (dy <= self.document().documentMargin() + prev_block_height)
    #            self.verticalScrollBar().setSliderPosition(slider_pos - (self.document().documentMargin() + prev_block_height))

    def resizeEvent(self, event: QResizeEvent):
        QTextEdit.resizeEvent(self, event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def getFirstVisibleBlockId(self) -> int:
        # Detect the first block for which bounding rect - once translated
        # in absolute coordinated - is contained by the editor's text area
    
        # Costly way of doing but since "blockBoundingGeometry(...)" doesn't
        # exists for "QTextEdit"...
    
        curs = QTextCursor(self.document())
        curs.movePosition(QTextCursor.Start)
        for i in range(self.document().blockCount()):
            block = curs.block()
    
            r1 = self.viewport().geometry()
            r2 = self.document().documentLayout().blockBoundingRect(block).translated(
                    self.viewport().geometry().x(), self.viewport().geometry().y() - (
                        self.verticalScrollBar().sliderPosition()
                        )).toRect()
    
            if r1.contains(r2, True):
                return i
    
            curs.movePosition(QTextCursor.NextBlock)
        return 0
    
    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())

        painter = QPainter(self.lineNumberArea)
        base = QColor(32, 33, 36)
        painter.fillRect(event.rect(), base)
        blockNumber = self.getFirstVisibleBlockId()

        block = self.document().findBlockByNumber(blockNumber)
        prev_block = self.document().findBlockByNumber(blockNumber - 1) if blockNumber > 0 else block

        translate_y = -self.verticalScrollBar().sliderPosition() if blockNumber > 0 else 0
        top = self.viewport().geometry().top()

        # Adjust starting position based on visibility
        additional_margin = self.document().documentLayout().blockBoundingRect(prev_block) \
                            .translated(0, translate_y).intersected(self.viewport().geometry()).height() \
                            if blockNumber > 0 else self.document().documentMargin() - 1 - self.verticalScrollBar().sliderPosition()

        top += additional_margin
        bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())

        col_1 = QColor(248,249,250)  # Current line
        col_0 = QColor(137,138,143)   # Other lines

        # Loop through blocks and draw numbers for each line
        while block.isValid() and top <= event.rect().bottom():
            # Draw line number even if the block has no text
            number = f"{blockNumber + 1}"
            painter.setPen(col_1 if self.textCursor().blockNumber() == blockNumber else col_0)
            painter.drawText(-5, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                            Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
            blockNumber += 1

        painter.end()  # Ensure QPainter is properly closed
        

class QTLineNumberArea(QWidget):
    def __init__(self, editor):
        QWidget.__init__(self, editor)
        self.codeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)