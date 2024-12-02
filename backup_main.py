import threading
from pathlib import Path

import time
import sys
import shutil

import win32con as wcon
from win32api import GetLogicalDriveStrings
from win32file import GetDriveType
import os

from webscraper import *
import main

GREEN = '#32a852'
RED   = '#eb4034'
BLUE  = '#4287f5'

def get_drives_list(drive_types=(wcon.DRIVE_REMOVABLE,))    :
    drives_str = GetLogicalDriveStrings()
    drives = (item for item in drives_str.split("\x00") if item)
    return [item[:2] for item in drives if not drive_types or GetDriveType(item) in drive_types]

def eject_drive(path):
    os.system(f'powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""{path}""").InvokeVerb("""Eject""")')

class TicketManager:
    def __init__(self):
        self.tickets = []
        self.gui = None
        self.backend = None
        self.selected_ticket = None

        self.show_only_valid = 1
        self.show_type       = 0

        # self.username = "tisanto1"
        # self.password = "!EpicTyler050505!1"

        try:
            login_file = open("login.txt", 'r')
            lines = login_file.readlines()
            if len(lines) > 0:
                self.username = lines[0].strip()
                self.password = lines[1].strip()
            else:
                self.username = ""  
                self.password = ""
            login_file.close()
        except:
            self.username = ""
            self.password = ""

    def threaded_parse_tickets(self):
        if self.backend == None:
            self.backend = WebBackend(self.gui.update_status)
            if self.username and self.password:
                status = self.backend.attempt_asu_login(self.username, self.password)
                if status == WebBackend.INVALID_LOGIN:
                    self.password = ""
            while not self.username or not self.password:
                self.username, self.password = self.gui.get_login_info(self.username)
                status = self.backend.attempt_asu_login(self.username, self.password)
                if status == WebBackend.INVALID_LOGIN:
                    self.password = ""
                else:
                    login_file = open("login.txt", 'w')
                    login_file.write(f"{self.username}\n{self.password}")

        if self.tickets:
            self.backend.parse_tickets(self.update_ticket)
            self.gui.update_tickets()
        else:    
            self.backend.parse_tickets(self.add_ticket)
        
        # self.tickets = [
        #     Ticket(1, "New", "John Jacob", 6),
        #     Ticket(2, "New", "John Jacob", 5),
        #     Ticket(3, "New", "John Jacob", 4),
        #     Ticket(4, "New", "John Jacob", 3),
        #     Ticket(5, "New", "John Jacob", 2),
        #     Ticket(6, "New", "John Jacob", 1),
        # ]
        # self.gui.update_status('Testing')
        # self.gui.update_tickets()

        self.gui.refresh_tickets()
        threading.Timer(30.0, self.threaded_parse_tickets).start()

    def add_ticket(self, ticket):
        self.tickets.append(ticket)
        if self.ticket_fits_filter(ticket):
            self.gui.add_ticket(ticket)
            self.gui.refresh_tickets()

    def update_ticket(self, new_ticket):
        found = False
        self.gui.update_ticket(new_ticket)
        for ticket in self.tickets:
            if new_ticket.ID == ticket.ID:
                found = True
                ticket = new_ticket
        if not found:
            self.add_ticket(new_ticket)
    
    def threaded_start_print(self, ticket):
        model_path = ticket.get_model_path()
        while not os.path.isfile(model_path): 
            time.sleep(0.1)
        self.gui.update_status("Model downloaded")
        removable_drives = get_drives_list()
        if(len(removable_drives) > 0): 
            # self.backend.send_started_email(ticket)
            shutil.copy(src=model_path, dst=removable_drives[0]+'/'+ticket.model_name)
            eject_drive(removable_drives[0])
            self.gui.update_status("Drive ejected")
            ticket.Status = 'Printing'
            self.update_ticket(ticket)
        else:
            self.gui.update_status("Drive not inserted, email not sent")

    def start_print(self, ticket):
        self.threaded_start_print()
        # threading.Thread(target=self.threaded_start_print, args=(ticket,)).start()

    def threaded_end_print(self, ticket):
        self.backend.send_ended_email(ticket)

    def end_print(self, ticket):
        self.threaded_end_print()
        # threading.Thread(target=self.threaded_end_print, args=(ticket,)).start()

    def update_only_valid(self):
        self.show_only_valid += 1
        self.show_only_valid %= 3
        
        if self.show_only_valid == 0:
            return (BLUE, 'All')
        elif self.show_only_valid == 1:
            return (GREEN, 'Printable')
        elif self.show_only_valid == 2:
            return (RED, 'Invalid')

    def update_show_type(self):
        self.show_type += 1
        self.show_type %= 3

        if self.show_type == 0:
            return (BLUE, 'All')
        elif self.show_type == 1:
            return (GREEN, 'New')
        elif self.show_type == 2:
            return (RED, 'Printing')
    
    def ticket_fits_filter(self, ticket):
        if self.show_type == 0:
            pass
        elif self.show_type == 1:
            if ticket.status != 'New':
                return False
        elif self.show_type == 2:
            if ticket.status != 'Printing':
                return False
        
        if self.show_only_valid == 1:
            if ticket.needs_filament:
                return False
        elif self.show_only_valid == 2:
            if not ticket.needs_filament:
                return False

        return True
        
    def get_tickets(self):
        self.tickets = sorted(self.tickets, key=lambda x: x.timestamp)
        result = [ticket for ticket in self.tickets if self.ticket_fits_filter(ticket)]
        
        return result

    def start(self):
        pass
        # self.gui = GUI(self)
        # self.gui.start()
        # threading.Thread(target=self.threaded_parse_tickets).start()
        # gui.start()

ticketer = TicketManager()
ticketer.start()