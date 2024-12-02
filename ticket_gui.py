import os
import shutil
import time

import win32con as wcon
from win32api import GetLogicalDriveStrings
from win32file import GetDriveType

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

import gl_renderer as render
import webscraper as web

def get_drives_list(drive_types=(wcon.DRIVE_REMOVABLE,))    :
    drives_str = GetLogicalDriveStrings()
    drives = (item for item in drives_str.split("\x00") if item)
    return [item[:2] for item in drives if not drive_types or GetDriveType(item) in drive_types]

def eject_drive(path):
    os.system(f'powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""{path}""").InvokeVerb("""Eject""")')

class GUITicket(QFrame):
    def __init__(self, backend, gui, ticket, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.gui = gui
        self.ticket = ticket

        self.layout = QGridLayout(parent=self)
        
        self.id_label      = QLabel(parent=self, text=f"ID: #{ticket.ID}")
        self.time_label    = QLabel(parent=self, text=f"Time: {ticket.timestamp}")
        self.patron_label  = QLabel(parent=self, text=f"Patron: {ticket.patron}")
        self.color_label   = QLabel(parent=self, text=f"Color: {ticket.color}")
        self.printer_label = QLabel(parent=self, text=f"Printer: {ticket.printer}")
        self.model_label   = QLabel(parent=self, text=f"Model: {ticket.model_name}")
        self.layout.addWidget(self.id_label,      0, 1)
        self.layout.addWidget(self.time_label,    1, 1)
        self.layout.addWidget(self.patron_label,  2, 1)
        self.layout.addWidget(self.color_label,   0, 2)
        self.layout.addWidget(self.printer_label, 1, 2)
        self.layout.addWidget(self.model_label,   2, 2)

        self.setLineWidth(1)
        self.setFrameShape(QFrame.Shape.Box)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.mousePressEvent = self.select

        self.isSelected = False 

    @Slot()
    def start(self):
        model_path = self.ticket.get_model_path()
        model_dir, model_ext = os.path.splitext(model_path)
        while not os.path.isfile(model_path): 
            time.sleep(0.1)
        self.gui.update_status("Model downloaded")
        removable_drives = get_drives_list()
        if(len(removable_drives) > 0): 
            print(model_path)
            self.backend.que_email(self.ticket, "PENDING", "Thank you for using the ASU Library Makerspace 3D print submission form. We have reviewed your file and have placed it on the appropriate 3D printer. If there are any issues, we will email you as soon as possible with details on how to repair your file. Expect to receive one more email regarding your print.")
            shutil.copy(src=model_path, dst=removable_drives[0]+'/'+str(self.ticket.ID)+model_ext)
            eject_drive(removable_drives[0])
            self.gui.update_status("Drive ejected")
            self.ticket.status = 'Printing'
            self.gui.ticket_filter.update_filter()
            self.gui.select_ticket(self)
            # self.update_ticket(self.ticket)
        else:
            self.gui.update_status("Drive not inserted, email not sent")

    @Slot()
    def finish(self):
        self.backend.que_email(self.ticket, "CLOSED", "Thank you for using the ASU Library Makerspace 3D print submission form. The project you submitted is complete. Prints can be picked up during our normal hours which can be found at https://lib.asu.edu/hours However, if you would like to use our equipment for any additional touch-ups, please make an appointment to use the space: https://asu.libcal.com/reserve/makerspace")
        self.ticket.status = 'Done'
        self.gui.ticket_filter.update_filter()
        self.gui.select_ticket(None)
    
    @Slot()
    def error(self):
        self.backend.que_email(self.ticket, "CLOSED", "There was an error with your submission. Please schedule a 3D printing consultation for in-space or online help. Reservations can be made at https://asu.libcal.com/reserve/makerspace")
        self.ticket.status = 'Done'
        self.gui.ticket_filter.update_filter()
        self.gui.select_ticket(None)

    def send_closed(self, text):
        self.backend.que_email("CLOSED", text)

    def send_pending(self, text):
        self.backend.que_email("PENDING", text)

    def deselect(self):
        self.setLineWidth(1)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.isSelected = False

    def select(self, event):
        if self.isSelected:
            pass
        else:
            self.gui.select_ticket(self)
            self.setLineWidth(4)
            self.setFrameShadow(QFrame.Shadow.Raised)
        self.isSelected = True
    
class TicketFilter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tickets = []
        self.show_valid = 1
        self.show_type = 1

        self.h_layout = QHBoxLayout(self)
        self.show_type_dropdown = QComboBox(self)
        self.h_layout.addWidget(self.show_type_dropdown)
        self.show_type_dropdown.addItem("Show All")
        self.show_type_dropdown.addItem("Show New")
        self.show_type_dropdown.addItem("Show Printing")
        self.show_type_dropdown.setCurrentIndex(1)
        self.show_type_dropdown.currentIndexChanged.connect(self.update_filter)

        self.show_valid_dropdown = QComboBox(self)
        self.h_layout.addWidget(self.show_valid_dropdown)
        self.show_valid_dropdown.addItem("Show All")
        self.show_valid_dropdown.addItem("Show Valid")
        self.show_valid_dropdown.addItem("Show Invalid")
        self.show_valid_dropdown.setCurrentIndex(1)
        self.show_valid_dropdown.currentIndexChanged.connect(self.update_filter)

        self.printer_dropdown = QComboBox(self)
        self.h_layout.addWidget(self.printer_dropdown)
        self.printer_dropdown.addItem("All")
        self.printer_dropdown.addItem("Makerbot Replicator+")
        self.printer_dropdown.addItem("Makerbot 5th Gen")
        self.printer_dropdown.addItem("Ultimaker 3")
        self.printer_dropdown.addItem("Ultimaker S5")
        self.printer_dropdown.addItem("Raise 3D Pro 2+")
        self.printer_dropdown.addItem("LulzBot TAZ Workhorse")
        self.printer_dropdown.addItem("Creality Mill")
        self.printer_dropdown.setCurrentIndex(0)
        self.printer_dropdown.currentIndexChanged.connect(self.update_filter)

    def add_ticket(self, ticket):
        self.tickets.append(ticket)
        if not self.ticket_fits_filter(ticket.ticket):
            ticket.hide()

    def ticket_fits_filter(self, ticket):
        self.show_type = self.show_type_dropdown.currentIndex()
        self.show_valid = self.show_valid_dropdown.currentIndex()
        
        printer = self.printer_dropdown.currentText()
        if printer != "All" and ticket.printer.lower() != printer.lower():
            return False
        
        if self.show_type == 0:
            pass
        elif self.show_type == 1:
            if ticket.status != 'New':
                return False
        elif self.show_type == 2:
            if ticket.status != 'Printing':
                return False

        if self.show_valid == 1:
            if not ticket.valid:
                return False
        elif self.show_valid == 2:
            if ticket.valid:
                return False

        return True

    @Slot()
    def update_filter(self):
        for ticket in self.tickets:
            if self.ticket_fits_filter(ticket.ticket):
                ticket.show()
            else:
                ticket.hide()

    def get_ticket(self, ID):
        for ticket in self.tickets:
            if ticket.ticket.ID == ID:
                return ticket
        return None
         
class GUITicketInfo(QFrame):
    def __init__(self, update_status, parent=None):
        super().__init__(parent)

        self.update_status = update_status
        self.gui_ticket = None
        self.ticket = None
        self.layout = QGridLayout(self)
        self.button = QPushButton(text="")
        # self.button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.button, 0, 0)
        self.error_button = QPushButton(text="Send error email")
        # self.error_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.error_button.clicked.connect(self.send_error)
        self.layout.addWidget(self.error_button, 1, 0)
        self.label  = QLabel(text="Label")
        self.layout.addWidget(self.label, 0, 1, 2, 1, Qt.AlignmentFlag.AlignTop)
        self.valid_label = QLabel(text="VALID")
        self.layout.addWidget(self.valid_label, 0, 2, 2, 1, Qt.AlignmentFlag.AlignTop)
        self.printer_label = QLabel(text="Printer")
        self.layout.addWidget(self.printer_label, 0, 3, 2, 1, Qt.AlignmentFlag.AlignTop)
        self.replies = QLabel(text="")
        self.replies.setWordWrap(True)
        self.layout.addWidget(self.replies, 2, 0, 1, -1)
        self.send_closed_button = QPushButton(text="Send closed")
        # self.send_closed_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.send_closed_button.clicked.connect(self.send_closed)
        self.layout.addWidget(self.send_closed_button, 3, 0)
        self.send_pending_button = QPushButton(text="Send pending")
        # self.send_pending_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.send_pending_button.clicked.connect(self.send_pending)
        self.layout.addWidget(self.send_pending_button, 4, 0)
        self.email_text = QTextEdit()
        self.layout.addWidget(self.email_text, 3, 1, 2, -1)


        self.preview = render.GcodePreview(self.update_status)
        self.layout.addWidget(self.preview, 6, 0, 1, -1)

    def load_ticket(self, ticket):
        # self.button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        if self.ticket:
            self.button.clicked.disconnect()
        self.gui_ticket = ticket
        if ticket:
            self.ticket = ticket.ticket
            if self.ticket.status == "Printing":
                self.button.setText("Finish")
                self.button.clicked.connect(ticket.finish)
                self.error_button.show()
            elif self.ticket.status == "New":
                self.button.setText("Start")
                self.button.clicked.connect(ticket.start)
                self.error_button.hide()

            if self.ticket.valid:
                self.valid_label.setText(f"VALID\n({self.ticket.weight}g)")
            else:
                self.valid_label.setText(f"INVALID\n({self.ticket.weight}g)")
            self.printer_label.setText(f"Printer: {self.ticket.printer}")

            if ticket.ticket.for_class:
                self.label.setText(f"{ticket.ticket.ID}\n{ticket.ticket.patron}\n({ticket.ticket.professor}, {ticket.ticket.course})")
            else:
                self.label.setText(f"{ticket.ticket.ID}\n{ticket.ticket.patron}")
            if len(ticket.ticket.replies) > 0:
                replies = "" 
                for reply in ticket.ticket.replies:
                    replies += "\"" + reply.strip() + "\"\n\n"
                self.replies.setText(f"Replies:\n {replies}")
                self.replies.show()
            else:
                self.replies.hide()

            self.preview.load_ticket(ticket.ticket)
            valid_text = ""
            if self.ticket.valid:
                valid_text = "VALID"
            else:
                valid_text = "INVALID"

            if self.ticket.model_data:
                if self.ticket.model_data.printer != self.ticket.printer:
                    self.printer_label.setText(f"Actual: {self.ticket.model_data.printer}")
                    valid_text += " - Printers don't match!"
                else:
                    self.printer_label.setText(f"Printer: {self.ticket.model_data.printer}")
            
            valid_text += f"\n({self.ticket.weight}g)"
            self.valid_label.setText(valid_text)
        else:
            self.ticket = None

    @Slot()
    def send_closed(self):
        self.ticket.send_closed(self.email_text.toPlainText())
    
    @Slot()
    def send_pending(self):
        self.ticket.send_pending(self.email_text.toPlainText())

    @Slot()
    def send_error(self):
        self.gui_ticket.error()


class InfoPanel(QFrame):
    def __init__(self, parent, update_status, ticket_filter):
        super().__init__(parent)
        self.update_status = update_status

        self.scroll = QScrollArea(parent)
        self.scroll.setWidget(self)
        self.scroll.setWidgetResizable(True)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel("3D Printing Tickets")
        font = QFont("Impact", weight=QFont.Weight.Bold, pointSize=25)
        title.setFont(font)
        self.layout.addWidget(title)
        self.layout.addWidget(ticket_filter)
        self.ticket_info = GUITicketInfo(self.update_status, self)
        self.layout.addWidget(self.ticket_info)
        self.ticket_info.hide()

    def add_to_layout(self, layout):
        layout.addWidget(self.scroll)

    def display_ticket(self, ticket):
        if ticket:
            self.ticket_info.load_ticket(ticket)
            self.ticket_info.show()
        else:
            self.ticket_info.load_ticket(None)
            self.ticket_info.hide()

    # def update_status(self, status):
    #     self.status_label.setText(status)

class TicketsTab(QWidget):
    def __init__(self, update_status):
        super().__init__()
        self.update_status = update_status

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tickets = QWidget()
        self.ticket_scroll = QScrollArea(self)
        self.ticket_scroll.setWidget(self.tickets)
        self.ticket_scroll.setWidgetResizable(True)
        self.ticket_layout = QVBoxLayout(self.tickets)
        
        self.ticket_filter = TicketFilter(None)
        self.info          = InfoPanel(None, self.update_status, self.ticket_filter)

        root_layout = QHBoxLayout(self)
        root_layout.addWidget(self.ticket_scroll)
        self.info.add_to_layout(root_layout)

        self.selected_ticket = None

        # self.tickets.show()

        # self.show()
        # self.setCentralWidget(preview)
        # preview.show()
        
        # self.button = QPushButton(parent=self, text="Click me!")
        # self.button.clicked.connect(self.test)
        # self.button.show()

        # self.start()

    def sizeHint(self):
        return QSize(600, 300)

    def select_ticket(self, ticket):
        if self.selected_ticket: 
            self.selected_ticket.deselect()
        self.selected_ticket = ticket
        self.info.display_ticket(ticket)

    def add_ticket(self, backend, ticket):
        t = GUITicket(backend, self, ticket)
        self.ticket_layout.addWidget(t, alignment=Qt.AlignmentFlag.AlignTop)
        self.ticket_filter.add_ticket(t)