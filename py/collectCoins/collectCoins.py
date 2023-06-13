import cv2
import numpy as np
import pyautogui
import time
import keyboard
import os
import win32gui
import ctypes
import sys
import json

# Enable color mode in console
os.system('color')


def rgb(r, g, b): return f"\u001b[38;2;{r};{g};{b}m"


# ANSI color codes
yellow = rgb(255, 255, 0)
pink = rgb(255, 50, 255)
cyan = rgb(0, 255, 255)
green = rgb(50, 255, 50)
red = rgb(255, 50, 50)
gray = rgb(128, 128, 128)
gold = rgb(255, 215, 0)
blue = rgb(0, 101, 196)
reset = "\u001b[0m"

# Images to scan
silver_coin_img = cv2.imread("silver_coin.png")
gold_coin_img = cv2.imread("gold_coin.png")
diamond_img = cv2.imread("diamond.png")

# Stats
silver_coins_collected = 0
gold_coins_collected = 0
diamonds_collected = 0
time_spent = 0
collection_start_time = 0

# detection region, confidence threshold, cursor type
top = 0
left = 0
bot = 0
right = 0

width = 0
height = 0

confidence_threshold = 1.0

correct_cursor = 0

# keybinds
with open('keybinds.json', 'r') as f:
    keybinds = json.load(f)

for key in keybinds:
    if keybinds[key]['key'].lower() == "ctrl+c":
        print(f"action '{key}' is keybinded to '{keybinds[key]['key']}' which is a default hotkey for interrupting the python shell.\n"
              f"It is crucial to change this key (NOT THE ACTION) to something else in the 'keybinds.json' file.")
    elif keybinds[key]['key'].lower() == "ctrl+i":
        print(f"action '{key}' is keybinded to '{keybinds[key]['key']}' which is a default hotkey for clearing the python shell screen.\n"
              f"It is crucial to change this key (NOT THE ACTION) to something else in the 'keybinds.json' file.")
    elif keybinds[key]['key'].lower() == "ctrl+d":
        print(f"action '{key}' is keybinded to '{keybinds[key]['key']}' which is a default hotkey for exiting the python shell.\n"
              f"It is crucial to change this key (NOT THE ACTION) to something else in the 'keybinds.json' file.")

first_corner_key = keybinds['first_corner']['key']
second_corner_key = keybinds['second_corner']['key']
get_cursor_key = keybinds['get_cursor']['key']
pause_script_key = keybinds['pause_script']['key']
resume_script_key = keybinds['resume_script']['key']
exit_script_key = keybinds['exit_script']['key']


def set_confidence_threshold():
    global confidence_threshold
    confidence_threshold = float(
        input("Enter confidence threshold between 1-0.1 (higher = precise, 0.9 recommended): "))
    while confidence_threshold < 0.1 or confidence_threshold > 1.0:
        confidence_threshold = float(input("Confidence threshold is invalid. Please enter a float between 1 and 0.1: "))


def set_region(first_selected=False, second_selected=False, cursor_selected=False):
    global top, left, bot, right, width, height, correct_cursor

    while True:
        if keyboard.is_pressed(exit_script_key):
            raise KeyboardInterrupt
        elif keyboard.is_pressed(first_corner_key) and not first_selected:
            cords = pyautogui.position()
            print(f"First corner selected: {cords}")
            top = cords[1]
            left = cords[0]
            first_selected = True
        elif keyboard.is_pressed(second_corner_key) and not second_selected:
            cords = pyautogui.position()
            print(f"Second corner selected: {cords}")
            bot = cords[1]
            right = cords[0]
            second_selected = True
        elif keyboard.is_pressed(get_cursor_key) and not cursor_selected:
            correct_cursor = win32gui.GetCursorInfo()[1]
            print(f"Cursor info found: win32gui.GetCursorInfo = {win32gui.GetCursorInfo()}")
            cursor_selected = True
        elif first_selected and second_selected and cursor_selected:
            width = right - left
            height = bot - top
            try:
                game_img = cv2.cvtColor(np.array(pyautogui.screenshot(region=(left-20, top-20, width+40, height+40))), cv2.COLOR_RGB2BGR)
                game_img_outlined = cv2.rectangle(game_img, (20, 20), (width+20, height+20), (255, 0, 255), 5)
                cv2.imshow("Region", game_img_outlined)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            except Exception as e:
                print(e)
            print(f"\nSelected region: top left corner = (X={left}, Y={top}), width & height = (W={width}, H={height})\n"
                  f"Press {yellow}{pause_script_key}{reset} if region is inaccurate, otherwise press {green}{resume_script_key}{reset} to continue\n\n")
            break


def start_collecting():
    global collection_start_time, silver_coins_collected, gold_coins_collected, diamonds_collected, correct_cursor

    collection_start_time = time.time()
    while True:
        if keyboard.is_pressed(pause_script_key):
            print(f"Script was paused. Press {green}{resume_script_key}{reset} to continue,"
                  f"otherwise press {red}{exit_script_key}{reset} to exit the script")
            while True:
                if keyboard.is_pressed(resume_script_key):
                    print(f"Script will resume in 2 seconds")
                    time.sleep(2)
                    break
                elif keyboard.is_pressed(exit_script_key):
                    raise KeyboardInterrupt
        elif keyboard.is_pressed(exit_script_key):
            raise KeyboardInterrupt
        else:
            # Screenshot of the detection region
            game_img = cv2.cvtColor(np.array(pyautogui.screenshot(region=(left, top, width, height))), cv2.COLOR_RGB2BGR)

            # load and compare coins/diamond images in the detection region
            silver_result = cv2.matchTemplate(game_img, silver_coin_img, cv2.TM_CCOEFF_NORMED)
            gold_result = cv2.matchTemplate(game_img, gold_coin_img, cv2.TM_CCOEFF_NORMED)
            diamond_result = cv2.matchTemplate(game_img, diamond_img, cv2.TM_CCOEFF_NORMED)

            # get information about the matches
            silver_min_val, silver_max_val, silver_min_loc, silver_max_loc = cv2.minMaxLoc(silver_result)
            gold_min_val, gold_max_val, gold_min_loc, gold_max_loc = cv2.minMaxLoc(gold_result)
            diamond_min_val, diamond_max_val, diamond_min_loc, diamond_max_loc = cv2.minMaxLoc(diamond_result)

            # Check if the most confident match of each silver, gold, and diamond matches is above the confidence threshold, in which case go to it
            # then check if the cursor changes to the correct cursor type, if so click it and store collected amount in stats variables
            if silver_max_val > confidence_threshold:
                pyautogui.moveTo(left + silver_max_loc[0], top + silver_max_loc[1])
                if win32gui.GetCursorInfo()[1] == correct_cursor:
                    pyautogui.click()
                    print(
                        f"{gray}Silver coin detected{reset} with {round(silver_max_val, 3)} {cyan}confidence{reset}  at {cyan}Location{reset}: {silver_max_loc}\n")
                    silver_coins_collected += 1
            if gold_max_val > confidence_threshold:
                pyautogui.moveTo(left + gold_max_loc[0], top + gold_max_loc[1])
                if win32gui.GetCursorInfo()[1] == correct_cursor:
                    pyautogui.click()
                    print(
                        f"{gold}Gold coin detected{reset} with {round(gold_max_val, 3)} {cyan}confidence{reset}  at {cyan}Location{reset}: {gold_max_loc}\n")
                    gold_coins_collected += 1
            if diamond_max_val > confidence_threshold:
                pyautogui.moveTo(left + diamond_max_loc[0], top + diamond_max_loc[1])
                if win32gui.GetCursorInfo()[1] == correct_cursor:
                    pyautogui.click()
                    print(
                        f"{blue}Diamond detected{reset} with {round(diamond_max_val, 3)} {cyan}confidence{reset}  at {cyan}Location{reset}: {diamond_max_loc}\n")
                    diamonds_collected += 1


# Function that handles restarting/exiting if the user stops the script/exe
def restart():
    global collection_start_time, silver_coins_collected, gold_coins_collected, diamonds_collected, time_spent, correct_cursor

    time_spent = time.time() - collection_start_time
    end_prompt = input(f"\nScript stopped.\n\nHere is your stats\n"
                       f"Silver coins collected: {gray}{silver_coins_collected}{reset}\n"
                       f"Gold coins collected: {gold}{gold_coins_collected}{reset}\n"
                       f"Diamonds collected: {blue}{diamonds_collected}{reset}\n\n"
                       f"Total value: {silver_coins_collected * 10 + gold_coins_collected * 50 + diamonds_collected * 1000}\n"
                       f"Time spent: {green}{round(time_spent, 2)}{reset} seconds ({green}{round(time_spent / 60, 2)}{reset} minutes)\n\n"
                       f"Type and enter '{yellow}1{reset}' to restart the whole script and select new parameters\n"
                       f"Type and enter '{yellow}2{reset}' to restart with the same parameters\n"
                       f"Otherwise, any other key to close: ")

    silver_coins_collected = 0
    gold_coins_collected = 0
    diamonds_collected = 0
    time_spent = 0
    collection_start_time = 0
    if end_prompt == "1":
        print(f"{yellow}NOTE{reset}: stats will be {red}reset{reset}.\n"
              f"New states will be displayed next time script is exited during collection.\n"
              f"Press {green}{resume_script_key}{reset} once ready to restart script and choose {yellow}new parameters{reset}\n\n")
        while True:
            if keyboard.is_pressed(resume_script_key):
                try:
                    main()
                except KeyboardInterrupt:
                    restart()
    elif end_prompt == "2":
        print(f"{yellow}NOTE{reset}: stats will be {red}reset{reset}.\n"
              f"New states will be displayed next time script is stopped (double-press {yellow}{pause_script_key}{reset}) during collection.\n"
              f"Press {green}{resume_script_key}{reset} once ready to restart script with the {yellow}same parameters{reset}\n\n")
        while True:
            if keyboard.is_pressed(resume_script_key):
                try:
                    start_collecting()
                except KeyboardInterrupt:
                    restart()
    else:
        quit()


# Main function that produces some information and groups other functions together
def main():
    try:
        print(f"To pause the script: press {yellow}{pause_script_key}{reset} ({yellow}NOTE{reset}: you might have to spam the key during for now)\n"
              f"To resume the script: press {green}{resume_script_key}{reset}\n"
              f"To exit the script: press {red}{exit_script_key}{reset} ({yellow}NOTE{reset}: you might have to spam the key during for now) \n\n"
              f"Hover your mouse over the top left then press {yellow}{first_corner_key}{reset} to select the first corner of the region\n"
              f"Hover your mouse over bottom right then press {yellow}{second_corner_key}{reset} to select the second corner of the region\n"
              f"Hover your mouse over a coin then press {yellow}{get_cursor_key}{reset} to identify cursor change\n\n")

        set_region()

        while True:
            if keyboard.is_pressed(exit_script_key):
                raise KeyboardInterrupt
            elif keyboard.is_pressed(pause_script_key):
                print("Reselect the region\n")
                set_region(cursor_selected=True)
            elif keyboard.is_pressed(resume_script_key):
                break

        set_confidence_threshold()
        print(f"{cyan}Confidence threshold{reset} = {cyan}{confidence_threshold}{reset}\n\n"
              f"Press {green}{resume_script_key}{reset} to start collecting!")
        while True:
            if keyboard.is_pressed(resume_script_key):
                break
        start_collecting()
    except KeyboardInterrupt:
        restart()

# Function for checking if the script/exe is in admin mode, in which case run as normal.
# Otherwise, bring UAC prompt again after inputting anything.
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        main()
        return False

if is_admin():
    main()
else:
    print(
        f"{red}IMPORTANT{reset}: script/exe should be ran in elevated (admin) mode to enable clicking. Otherwise, clicking will not work.\n"
        f"You can also run script/exe through elevated (admin) command prompt.\n")
    input("Script/exe will ask again for admin permission once you enter anything.")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
