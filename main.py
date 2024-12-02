from PySide6.QtCore import QByteArray
from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import *
from PySide6.QtGui import *     
from PySide6.QtCore import *

from ticket_gui import *    
from filament_gui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = None
            
        self.resize(800, 400)
        self.setWindowTitle('3D Printing Tickets')

        self.tabs = QTabWidget(self)
        self.tickets_tab = TicketsTab(self.update_status)
        self.tabs.addTab(self.tickets_tab, "Tickets")
        self.filament_tab = FilamentTab()
        self.tabs.addTab(self.filament_tab, "Filaments")
        
        self.setCentralWidget(self.tabs)

        self.start_backend()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)

    def add_ticket(self, ticket):
        self.tickets_tab.add_ticket(self.backend, ticket)
        self.filament_tab.add_ticket(ticket)

    def update_ticket(self, ticket):
        current_ticket = self.tickets_tab.ticket_filter.get_ticket(ticket.ID)
        if not current_ticket:
            self.add_ticket(ticket)
        else:
            # TODO(Tyler): Make this actually update the ticket info if it exists   
            pass

    def update_status(self, text):
        status_bar = self.statusBar().showMessage(text, 500)

    def start_backend(self):
        username = ""   
        password = ""
        with open("login.txt", 'r') as login_file:
            lines = login_file.readlines()
            if len(lines) > 0:
                username = lines[0].strip() 
                password = lines[1].strip()
        self.backend = web.WebBackend(self.update_status)
        self.backend.set_login(username, password)
        self.backend.start()
        # self.backend.attempt_asu_login(username, password)

    def showEvent(self, event: QShowEvent) -> None:
        settings = QSettings("ASU MakerSpace", "3D Printing Tickets")
        self.restoreGeometry(settings.value("geometry"))
        self.restoreState(settings.value("windowState"))  
        return super().showEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.backend.quit()
        settings = QSettings("ASU MakerSpace", "3D Printing Tickets")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        return super().closeEvent(event)

    @Slot()
    def refresh(self):
        if not self.backend.logged_in:
            # TODO: Login page or something
            return
            
        lock, tickets = self.backend.get_tickets()
        if lock.acquire(True, 0.5):
            for ticket in tickets:
                self.update_ticket(ticket)
            lock.release()



def start():   
    # Create the Qt Applications
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication()

    window = MainWindow()
    window.show()
    app.exec()


start()
# window.setPosition(100, 100)
# window.resize(500, 500)

# fmt = QOpenGLVersionProfile()
# fmt.setVersion(3, 3)
# fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)



# QSurfaceFormat.setDefaultFormat(fmt)
