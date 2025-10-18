import threading
import time
import random
from pynput import mouse, keyboard

clicking = False
click_thread = None

# Создаем контроллеры
mouse_controller = mouse.Controller()
keyboard_listener = keyboard.Listener
Key = keyboard.Key
KeyCode = keyboard.KeyCode

def clicker():
    global clicking
    while clicking:
        mouse_controller.click(mouse.Button.left)
        time.sleep(random.uniform(0.05, 0.1))  # Задержка между кликами как у человека

def toggle_clicking():
    global clicking, click_thread
    clicking = not clicking
    if clicking:
        print("Кликер включён")
        click_thread = threading.Thread(target=clicker)
        click_thread.start()
    else:
        print("Кликер выключен")

def on_press(key):
    if isinstance(key, KeyCode) and key.char and key.char.lower() == 'z':
        toggle_clicking()

with keyboard_listener(on_press=on_press) as listener:
    listener.join()
