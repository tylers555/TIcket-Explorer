from seleniumrequests import Chrome
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import requests
from bs4 import BeautifulSoup
import pickle

import datetime
import time
import threading
from collections import deque

import re
import os
import sys
import importlib.util

from pprint import pprint
from zipfile import ZipFile
import thumby
import subprocess

import gcode

timeout = 5
WEIGHT_LIMIT = 250

def sort_ticket(ticket):
    return ticket.timestamp

def import_module(name):
    if name in sys.modules:
        pass
    elif (spec := importlib.util.find_spec(name)) is not None:
        # If you choose to perform the actual import ...
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        pass
    else:
        assert False

class Ticket:
    def __init__(self, ID, status, patron, timestamp):
        self.valid = True
        self.ID = ID
        self.status = status
        self.patron = patron
        self.timestamp = timestamp

        self.printer = 'DUMMY'
        self.weight = 0
        self.color = 'DUMMY'
        self.model_name = 'DUMMY'

        self.for_class = False
        self.course = None
        self.professor = None
        
        self.needs_filament = False

        self.replies = []

        self.thumbnail = []
        self.gl_model = None

        self.model_data = None
        self.iteration_num = 0

        self.lock = threading.Lock()

    def get_model_path(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        model_dir, model_ext = os.path.splitext(self.model_name)
        model_path =  script_path + '/files/' + str(self.ID) + model_ext
        return model_path

    def download_model(self, session, modal_text):
        with self.lock:
            model_path = self.get_model_path()
            if os.path.isfile(model_path):
                return
            self.model_name = self.model_name.replace(" ",  "%20")
            self.model_name = self.model_name.replace("<",  "%3C")
            self.model_name = self.model_name.replace(">",  "%2E")
            self.model_name = self.model_name.replace("#",  "%23")
            self.model_name = self.model_name.replace("%",  "%25")
            self.model_name = self.model_name.replace("+",  "%2B")
            self.model_name = self.model_name.replace("{",  "%7B")
            self.model_name = self.model_name.replace("}",  "%7D")
            self.model_name = self.model_name.replace("|",  "%7C")
            self.model_name = self.model_name.replace("\\", "%5C")
            self.model_name = self.model_name.replace("^",  "%5E")
            self.model_name = self.model_name.replace("~",  "%7E")
            self.model_name = self.model_name.replace("[",  "%5B")
            self.model_name = self.model_name.replace("]",  "%5D")
            self.model_name = self.model_name.replace("`",  "%60")
            self.model_name = self.model_name.replace(";",  "%3B")
            self.model_name = self.model_name.replace("/",  "%2F")
            self.model_name = self.model_name.replace("?",  "%3F")
            self.model_name = self.model_name.replace(":",  "%3A")
            self.model_name = self.model_name.replace("@",  "%40")
            self.model_name = self.model_name.replace("=",  "%3D")
            self.model_name = self.model_name.replace("&",  "%26")
            self.model_name = self.model_name.replace("$",  "%24")
            self.model_name = self.model_name.replace("(",  "%28")
            self.model_name = self.model_name.replace(")",  "%29")
            # print(self.model_name)
            # print(modal_text)
            x = re.search(f'[0-9][0-9][0-9][0-9][0-9]\\\\/{self.model_name}', modal_text)
            extra = x.group().replace("\\", "")
            headers = {
                "scheme": "https",
                "accept" :"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding":"gzip, deflate, br",
                "accept-language":"en-US,en;q=0.9",
                "referer":"https://askalibrarian.asu.edu/",
                "sec-ch-ua":"\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
                "sec-ch-ua-mobile":"?0",
                "sec-ch-ua-platform":"\"Windows\"",
                "sec-fetch-dest":"document",
                "sec-fetch-mode":"navigate",
                "sec-fetch-site":"same-site",
                "sec-fetch-user":"?1",
                "upgrade-insecure-requests":"1",
            }
            r = session.get(f"https://lib.asu.edu/system/files/webform/3d_print_request/{extra}", headers=headers, allow_redirects=True, stream=True)
            # print("\nAttempted Download:")
            # print(r.headers.get('content-type'))
            with open(model_path, 'wb') as file:
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        file.write(chunk)
                        file.flush()
                file.close()

    def get_thumbnail(self):
        self.lock.acquire()
        model_path = self.get_model_path()
        if not os.path.isfile(model_path):
            return None
        model_dir, model_ext = os.path.splitext(model_path)
        if model_ext == '.makerbot':
            if not os.path.isdir(model_dir):
                with ZipFile(model_path, 'r') as zip:
                    zip.extractall(model_dir)
            with open(model_dir + '/thumbnail_110x80.png', 'rb') as file:
                 self.thumbnail = file.read()
        # elif model_ext == '.gcode':
            # import_module("gcode2image")
            # subprocess.run([''])
            # thumby.extract_png_from_gcode_normal(model_dir+'_thumbnail.png', model_path)
            # with open(model_dir + '_thumbnail.png', 'rb') as file:
            #      self.thumbnail = file.read()
        #     self.thumbnail = bytearray()
        else:
            self.thumbnail = bytearray()
        
        self.lock.release()

    def get_model(self):
        assert not self.gl_model   
        model_path = self.get_model_path()
        model_dir, model_ext = os.path.splitext(model_path)
        if model_ext == '.makerbot':
            if not os.path.isdir(model_dir):
                with ZipFile(model_path, 'r') as zip:
                    zip.extractall(model_dir)
        model, self.model_data = gcode.parse_model_file(model_path)
        if self.model_data:
            self.weight = max(self.weight, self.model_data.weight)
            if self.model_data.printer and self.printer != self.model_data.printer:
                print("Printers don't match!")
                self.valid = False
            elif "OWN:" not in self.color and self.weight > WEIGHT_LIMIT:
                self.needs_filament = True
                self.valid = False
        return model

    def parse_modal(self, session, driver, question):
        try:
            response = session.request('GET', f'https://askalibrarian.asu.edu/admin/ticket/{self.ID}/preview')
            soup = BeautifulSoup(response.json()['content'], 'html.parser')

            replies = soup.find_all("div", {"class": "s-la-preview-reply-body"})
            if 'New' not in self.status:
                if not replies:
                    self.status = 'New'
                else:
                    self.status = 'New'
                    for reply in replies:
                        if 'We will review the file and you will be notified if there are any issues printing' in reply.text:
                            self.status = 'Printing'
                            break
                        elif 'placed it on the appropriate 3D printer' in reply.text:
                            self.status = 'Printing'
                            break
                        elif 'added it to our queue' in reply.text:
                            self.status = 'Printing'
                            break
            self.replies = [reply.text for reply in replies]

            body = soup.find("div", {'class': None}).text

            self.printer = body.split('Which 3D printer was your model sliced for?')[1].split('Estimated print weight (grams)')[0].strip()
            weight = body.split('Estimated print weight (grams)')[1].split('Filament color')[0]
            try:
                weight = "".join(c for c in weight if c.isdigit() or c == '.' or c == ',')
                self.weight = float(weight)
            except:
                self.weight = 500
            self.color = body.split('Filament color')[1].split('Upload your project')[0].strip()
            if "I will provide my own filament" in self.color:
                color1 = self.color.split('What color will you be using?')[0].strip()
                color2 = self.color.split('What color will you be using?')[1].strip()
                if len(color2) > 20:
                    color2 = color2[0:20]+'...'
                self.color = 'OWN: ' + color2
            elif "Color does not matter" in self.color:
                self.color = 'CDM'
            self.model_name = body.split('Upload your project')[1].split('Questioner Information:')[0].strip()
            self.download_model(session, response.text)
            # self.get_thumbnail()

            for_class = body.split('Is this print for a course or class project?')[1].split('Which 3D printer was your model sliced for?')[0].strip()
            if 'Yes' in for_class:
                self.for_class = True

            if self.for_class:
                self.course    = body.split('Course prefix and number')[1].split('Instructor name')[0].strip()
                self.professor = body.split('Instructor name')[1].split('Which 3D printer was your model sliced for?')[0].strip()

            # self.check_filament(modal_window)
            if not replies:
                if "OWN:" in self.color:
                    self.needs_filament = False
                elif self.weight > WEIGHT_LIMIT:
                    self.needs_filament = True
                else:
                    self.needs_filament = False
            elif any(('own filament' in reply.text.lower()) or ('provide filament' in reply.text.lower()) for reply in replies): 
                self.needs_filament = True
            
            if self.needs_filament:
                self.valid = False
        except:
            print(f"ERROR PARSING: {self.ID}")

    def to_string(self):
        return self.ID + ',' + self.status + ',' + self.patron + ',' + self.timestamp.strftime('%b %d %Y, %I:%M%p') + ',' + self.printer + ',' + str(self.weight) + ',' + self.color + ',' + self.model_name + ',' + str(self.for_class) + ',' + str(self.needs_filament)

def make_ticket(session, driver, elem):
    ID = elem['data-qid']
    status = elem.find(attrs={'class': 's-la-qu-col-status'}).text
    if 'New' in status:
        status = 'New'
    question = elem.find(attrs={'class': 's-la-queues-col-question'})
    type = question.find(attrs={'class': 's-la-queues-question'})
    patron = question.find(attrs={'class': 's-la-queues-name'}).text.split(' (')[0]
    created = elem.find(attrs={'class': 's-la-queues-col-created'})
    timestamp = datetime.datetime.strptime(created.text, '%b %d %Y, %I:%M%p')
    if not ("3D print request" == type.text):
        return None
    ticket = Ticket(ID, status, patron, timestamp)
    ticket.parse_modal(session, driver, question)
    
    return ticket

class BackendActionEmail:
    def __init__(self, ticket, status, message):
        self.ticket = ticket
        self.status = status
        self.message = message
        # print(f"Action requested! {status}")

    def execute(self, backend):
        # print(f"Action executed begun! {self.status}")
        if self.status == 'PENDING':
            # print("Submitted pending")
            backend.send_pending_email(self.ticket, self.message)
        elif self.status == 'CLOSED':
            # print("Submitted closed")
            backend.send_closed_email(self.ticket, self.message)
        else:  
            assert False
        # print("Action execution done!")

class WebBackend:
    SUCCESS       = 0
    INVALID_LOGIN = 1

    def __init__(self, update_status):
        self.update_status = update_status
        self.lock = threading.Lock()

        self.start_driver()

        self.logged_in = False
        self.is_done   = False
        self.tickets = []

        self.username = ""
        self.password = ""

        self.actions = deque()

    def start_driver(self):
        self.update_status("Initializing")
        options = Options()
        # options.add_argument("--headless")
        # options.add_argument('user-data-dir="C:\\Users\\epicr\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 2"')
        self.driver = Chrome(options=options)
        self.driver.get("https://askalibrarian.asu.edu/admin/home")
        self.load_cookies()
        self.session = requests.Session()

    def store_cookies(self):
        try:
            self.driver.execute_script("window.open('');") 
            self.driver.switch_to.window(self.driver.window_handles[1]) 
            self.driver.get("https://weblogin.asu.edu/404")
            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0]) 
            print("Successfully saved cookies!")
        except:
            print("Failed to save cookies")

    def load_cookies(self):
        try:
            print("Attempting to load cookies")
            cookies = pickle.load(open("cookies.pkl", "rb"))
            self.driver.execute_script("window.open('');") 
            self.driver.switch_to.window(self.driver.window_handles[1]) 
            self.driver.get("https://weblogin.asu.edu/404")
            for cookie in cookies:
                # print(cookie)
                self.driver.add_cookie(cookie)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0]) 
            print("Cookies loaded!")
        except:
            if "error page" in self.driver.title:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0]) 
            print("Failed to load cookies!")
            pass
    
    def sync_cookies(self):
        selenium_user_agent = self.driver.execute_script("return navigator.userAgent;")
        self.session.headers.update({"user-agent": selenium_user_agent})
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    def set_login(self, username, password):
        self.username = username
        self.password = password

    def attempt_asu_login(self):
        assert self.lock.locked()

        self.update_status('Logging into ASU')
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.NAME, 'username')))

        input_username = self.driver.find_element(By.NAME, "username")
        input_username.clear()
        input_username.send_keys(self.username)

        input_password = self.driver.find_element(By.NAME, "password")
        input_password.clear()
        input_password.send_keys(self.password)

        submit_button = self.driver.find_element(By.NAME, "submit")
        submit_button.click()
        
        self.duo_login()

        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'title')))
        if self.driver.title == 'Login':
            return self.INVALID_LOGIN

        self.update_status("Duo push received")
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'title')))
        if "Information" in self.driver.title:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.NAME, '_eventId_proceed'))).click()
    
        print("Here!")

        # self.sync_cookies()
        # self.session.request("GET", "https://lib.asu.edu/caslogin")

        self.driver.execute_script("window.open('');") 
        self.driver.switch_to.window(self.driver.window_handles[1]) 
        self.driver.get("https://lib.asu.edu/caslogin") 
        sign_in = WebDriverWait(self. driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "title")))
        self.sync_cookies()
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.logged_in = True
        return self.SUCCESS
    
    def duo_login(self):
        print("A")
        while "Duo" in self.driver.title:
            print(self.driver.title)
            time.sleep(0.2)

        print("B")
        self.update_status("Duo push sent")


    def send_pending_email(self, ticket, text):
        assert self.lock.locked()
        self.update_status("Sending pending email")
        self.driver.execute_script(f"window.open('/admin/ticket?qid={ticket.ID}');")
        # time.sleep(5)
        for win in self.driver.window_handles:
            self.driver.switch_to.window(win)
            if "3D print request" == self.driver.title:
                break
        iframe = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
        
        self.driver.switch_to.frame(iframe)
        text_box = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, 'cke_editable')))
        text_box.click()
        text_box.send_keys(text)

        self.driver.switch_to.default_content()
        elem = self.driver.find_element(By.CLASS_NAME, 'dropup')
        elem.find_element(By.CLASS_NAME, 'dropdown-toggle').click()
        WebDriverWait(elem, timeout).until(EC.presence_of_element_located((By.XPATH, '//a[@data-status="2"]'))).click()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0]) 
        self.update_status("Pending email sent")

    def send_closed_email(self, ticket, text):
        assert self.lock.locked()
        self.update_status("Sending closed email")
        self.driver.execute_script(f"window.open('/admin/ticket?qid={ticket.ID}');")
        # time.sleep(5)
        for win in self.driver.window_handles:
            self.driver.switch_to.window(win)
            if "3D print request" == self.driver.title:
                break
        iframe = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
        self.driver.switch_to.frame(iframe)
        text_box = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, 'cke_editable')))
        text_box.click()
        text_box.send_keys(text)

        self.driver.switch_to.default_content()
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.ID, 'main_submit'))).click()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0]) 
        self.update_status("Closed email sent")

    def maybe_restart_driver(self):
        try:
            self.driver.title
        except:
            self.logged_in = False
            self.start_driver()

    def refresh_tickets(self):
        try:
            with self.lock:
                if not self.logged_in:
                    self.attempt_asu_login()

                self.driver.refresh()
                while not "Dashboard" in self.driver.title:
                    time.sleep(.1)
                WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, 's-la-queues-col-question')))
                
                self.sync_cookies()

                soup = BeautifulSoup(self.driver.find_element(By.TAG_NAME, "tbody").get_attribute('innerHTML'), "html.parser")

                self.ticket_elements = soup.find_all("tr")
            
            for elem in self.ticket_elements:
                with self.lock:
                    new_ticket = make_ticket(self.session, self.driver, elem)
                    if not new_ticket:
                        continue
                    existing_ticket = None
                    for ticket in self.tickets:
                        if ticket.ID == new_ticket.ID:
                            existing_ticket = ticket
                    if existing_ticket:
                        # TODO: Handle this case where a ticket already exists
                        pass
                    else:
                        self.tickets.append(new_ticket)

        except:
            if self.is_done:
                return
            self.maybe_restart_driver()
            pass

        try:
            threading.Timer(30.0, self.refresh_tickets).start()
        except:
            pass

    def execute_next_action(self):
        try:
            with self.lock:
                if not self.logged_in:
                    self.attempt_asu_login()
                try:
                    action = self.actions.popleft()
                    action.execute(self)
                except:
                    pass

        except:
            if self.is_done:
                return
            self.maybe_restart_driver()
            pass

        try:
            threading.Timer(2.0, self.execute_next_action).start()
        except:
            pass

    def quit(self):
        self.store_cookies()
        self.is_done = True
        self.driver.quit()

    def start(self):
        threading.Thread(target=self.refresh_tickets).start()
        threading.Thread(target=self.execute_next_action).start()
    
    def que_email(self, ticket, status, message):
        action = BackendActionEmail(ticket, status, message)
        self.actions.append(action)

    def get_tickets(self):
        return self.lock, self.tickets
