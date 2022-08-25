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
    background_red = Column(Integer, nullable=False, default=255)
    background_green = Column(Integer, nullable=False, default=255)
    background_blue = Column(Integer, nullable=False, default=255)

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
        self.setStyleSheet(f'background-color: rgb({self.note.background_red}, {self.note.background_green}, {self.note.background_blue});')


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

        background_colour = QAction("colour", self)
        background_colour.setShortcut(QKeySequence("Ctrl+l"))
        background_colour.triggered.connect(self.setBackgroundWindowColour)
        self.addAction(background_colour)

        font = QAction("font", self)
        font.setShortcut(QKeySequence("Ctrl+t"))
        font.triggered.connect(self.setFont)
        self.addAction(font)

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

        agendaAction = QAction('agenda dates', self)
        agendaAction.setShortcut(QKeySequence("Ctrl+d"))
        self.agenda = Agenda(self)
        agendaAction.triggered.connect(self.agenda.show)
        self.addAction(agendaAction)

        toolbar.setFixedHeight(10)
        self.addToolBar(toolbar)

    def setBackgroundWindowColour(self):
        self.colour = QColorDialog.getColor()
        self.note.background_red = self.colour.red()
        self.note.background_green = self.colour.green()
        self.note.background_blue = self.colour.blue()
        self.setStyleSheet(f'background-color: rgb({self.note.background_red}, {self.note.background_green}, {self.note.background_blue});')
        self.save()

    def setFont(self):
        font, ok = QFontDialog.getFont()
        self.editor.setCurrentFont(font)
        # don't save because is in the text box

        # self.editor.setFontPointSize(value)

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

class Agenda(QWidget):
    def __init__(self, parent=None):
        super(Agenda, self).__init__(parent=None)
        self.parent = parent

        self.setWindowTitle("Agenda View")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setStyleSheet(f'background-color: rgb({self.parent.note.background_red}, {self.parent.note.background_green}, {self.parent.note.background_blue});')
        self.move(self.parent.note.position_x, self.parent.note.position_y)

        self.button = QPushButton("done")
        self.button.clicked.connect(self.close)

        self.layout = QVBoxLayout()
        message = QLabel("This is the agenda view\nDate 1\nDate2\nDate3")
        self.layout.addWidget(message)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)


app = QApplication(sys.argv)
app.setApplicationName("Kira's agenda")
app.setStyle("Fusion")

existing_note = session.query(Note).first()
window = MainWindow(obj=existing_note)
window.show()
sys.exit(app.exec())


# cal.parse("aug 31", datetime.datetime(2022, 8, 11, 0, 0, 0))
# cal.parseDT("aug 31", datetime.datetime(2022, 8, 11, 0, 0, 0))
# cal = pdt.Calendar()