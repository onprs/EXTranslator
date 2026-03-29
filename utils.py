import os
import subprocess
import msvcrt

def clear_panel():
    subprocess.run('cls' if os.name=='nt' else 'clear',shell=True)

def press_to_continue():
    if os.name=='nt':
        subprocess.run('pause',shell=True)

def catch_keyboard(keys):
    while True:
        choice=msvcrt.getch().decode(encoding='utf-8',errors='ignore').strip()
        if choice in keys:
            print(choice)
            return choice
