import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtCore import *

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
class Note(Base):
    __tablename__ = 'note'
    id = Column(Integer, primary_key=True)
    text = Column(String(64000), nullable=False)
    position_x = Column(Integer, nullable=False, default=0)
    position_y = Column(Integer, nullable=False, default=0)
    position_right = Column(Integer, nullable=False, default=100)
    position_bottom = Column(Integer, nullable=False, default=100)

engine = create_engine('sqlite:///notes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

_ACTIVE_NOTES = {}

class MainWindow(QMainWindow):

    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__()
        self.editor = QTextEdit()

        # Load/save note data, store this notes db reference.
        if obj:
            self.note = obj
            self.load()
        else:
            self.note = Note()
            self.save()

        font = QFont('Times', 18)
        self.editor.setFont(font)
        self.fontSizeBox = QSpinBox()
        self.path = ""
        self.setCentralWidget(self.editor)
        self.setWindowTitle("Kira's Agenda")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.grip = QSizeGrip(self)
        self.gripSize = 16

        self.create_tool_bar()
        # self.create_status_bar()

        self.editor.setFontPointSize(18)
        self.editor.textChanged.connect(self.save)

        self.setGeometry(self.note.position_x, self.note.position_y, self.note.position_right, self.note.position_bottom)
        # self.grip.move(self.note.position_right, self.note.position_bottom)
        # self.move(self.note.position_x, self.note.position_y)


    def load(self):
        # print(f"loading {self.note.text}")
        self.editor.setHtml(self.note.text)
        _ACTIVE_NOTES[self.note.id] = self

    def save(self):
        self.note.text = self.editor.toHtml()
        # print(f"SAVING:\n{self.note.text}\n")
        session.add(self.note)
        session.commit()
        _ACTIVE_NOTES[self.note.id] = self

    def create_status_bar(self):
        self.statusbar = self.statusBar()
        # Adding a temporary message
        self.statusbar.showMessage("Ready", 3000)

    def create_tool_bar(self):
        toolbar = QToolBar()

        closeButton = QAction("bold", self)
        closeButton.setShortcut(QKeySequence("Ctrl+k"))
        closeButton.triggered.connect(self.closeApp)
        self.addAction(closeButton)

        boldBtn = QAction("bold", self)
        boldBtn.setShortcut(QKeySequence("Ctrl+b"))
        boldBtn.triggered.connect(self.boldText)
        self.addAction(boldBtn)

        underlineBtn = QAction('underline', self)
        underlineBtn.setShortcut(QKeySequence("Ctrl+u"))
        underlineBtn.triggered.connect(self.underlineText)
        self.addAction(underlineBtn)

        italicBtn = QAction('italic', self)
        italicBtn.setShortcut(QKeySequence("Ctrl+i"))
        italicBtn.triggered.connect(self.italicText)
        self.addAction(italicBtn)

        italicBtn = QAction('text', self)
        italicBtn.setShortcut(QKeySequence("Ctrl+t"))
        italicBtn.triggered.connect(self.italicText)
        self.addAction(italicBtn)

        # self.fontBox = QComboBox(self)
        # self.fontBox.addItems(["Courier Std", "Hellentic Typewriter Regular", "Helvetica", "Arial", "SansSerif", "Helvetica", "Times", "Monospace"])
        # self.fontBox.activated.connect(self.setFont)
        # toolbar.addWidget(self.fontBox)
        #
        # self.fontSizeBox.setValue(24)
        # self.fontSizeBox.valueChanged.connect(self.setFontSize)
        # toolbar.addWidget(self.fontSizeBox)

        toolbar.setFixedHeight(10)
        self.addToolBar(toolbar)
        
    def setFontSize(self):
        value = self.fontSizeBox.value()
        self.editor.setFontPointSize(value)
        
    def setFont(self):
        font = self.fontBox.currentText()
        self.editor.setCurrentFont(QFont(font))    
        
    def italicText(self):
        state = self.editor.fontItalic()
        self.editor.setFontItalic(not(state)) 
    
    def underlineText(self):
        state = self.editor.fontUnderline()
        self.editor.setFontUnderline(not(state))   

    @property
    def isBold(self):
        return self.editor.fontWeight() == QFont.Bold

    def boldText(self):
        if not self.isBold:
            # self.statusbar.showMessage("BOLD", 3000)
            self.editor.setFontWeight(QFont.Bold)
        else:
            # self.statusbar.showMessage("NOT BOLD", 3000)
            self.editor.setFontWeight(QFont.Normal)

    def mousePressEvent(self, event):
        # print(f"mousepress globalPos: {event.globalPos()}")
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "oldPos"):
            delta = QPoint(event.globalPos() - self.oldPos)
            if delta.x() or delta.y():
                self.note.position_x = self.x() + delta.x()
                self.note.position_y = self.y() + delta.y()
                self.move(self.note.position_x, self.note.position_y)
        self.oldPos = event.globalPos()
        self.save()

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        rect = self.rect()
        self.note.position_right = rect.right() - self.gripSize
        self.note.position_bottom = rect.bottom() - self.gripSize
        self.grip.move(self.note.position_right, self.note.position_bottom)
        self.save()

    def closeApp(self, event):
        self.save()
        self.close()

app = QApplication(sys.argv)
app.setApplicationName("Kira's agenda")
app.setStyle("Fusion")

existing_note = session.query(Note).first()
window = MainWindow(obj=existing_note)
window.show()
sys.exit(app.exec_())
