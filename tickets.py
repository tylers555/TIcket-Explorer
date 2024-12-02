import webscraper as web

import win32con as wcon
from win32api import GetLogicalDriveStrings
from win32file import GetDriveType
import os

def get_drives_list(drive_types=(wcon.DRIVE_REMOVABLE,))    :
    drives_str = GetLogicalDriveStrings()
    drives = (item for item in drives_str.split("\x00") if item)
    return [item[:2] for item in drives if not drive_types or GetDriveType(item) in drive_types]

def eject_drive(path):
    os.system(f'powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""{path}""").InvokeVerb("""Eject""")')

GREEN = '#32a852'
RED   = '#eb4034'
BLUE  = '#4287f5'
