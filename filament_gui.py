from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

class PatronFilament(QFrame):
    def __init__(self, name):
        super().__init__()
        self.tickets = []
        self.grams_used = 0
        self.name = name
        
        self.layout = QGridLayout(self)
        self.name_label   = QLabel(f"Patron: {self.name}")
        self.layout.addWidget(self.name_label, 0, 0)
        self.weight_label = QLabel(f"Weight: {self.grams_used}")
        self.layout.addWidget(self.weight_label, 0, 1)


    def add_ticket(self, ticket):
        for t in self.tickets:
            if t.ID == ticket.ID:
                return
        if "OWN:" not in ticket.color:
            self.grams_used += ticket.weight
            self.weight_label.setText(f"Weight: {self.grams_used}")
        

class FilamentTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        title = QLabel("Patron Filament")
        font = QFont("Impact", weight=QFont.Weight.Bold, pointSize=25)
        title.setFont(font)
        self.layout.addWidget(title, 0, 1, 1, -1, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.patrons_widget = QWidget()
        self.patron_scroll = QScrollArea(self)
        self.patron_scroll.setWidget(self.patrons_widget)
        self.patron_scroll.setWidgetResizable(True)
        self.patron_layout = QVBoxLayout(self.patrons_widget)
        self.layout.addWidget(self.patron_scroll, 0, 0, -1, 1)

        self.patrons = []

    def find_patron(self, ticket):
        for patron in self.patrons:
            # print(f"'{ticket.patron}' and '{patron.name}'")
            if ticket.patron.strip().lower() == patron.name.strip().lower():
                # print("here")
                return patron
            
        result = PatronFilament(ticket.patron)
        self.patron_layout.addWidget(result)
        self.patrons.append(result)

        return result

    def add_ticket(self, ticket):
        patron = self.find_patron(ticket)
        patron.add_ticket(ticket)