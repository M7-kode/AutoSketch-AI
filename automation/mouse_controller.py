import pyautogui

pyautogui.FAILSAFE = True


class MouseController:
    def __init__(self, move_duration=0.2):
        self.move_duration = move_duration

    def move_to(self, x, y, duration=None):
        pyautogui.moveTo(x, y, duration=duration if duration is not None else self.move_duration)

    def press(self):
        pyautogui.mouseDown()

    def release(self):
        pyautogui.mouseUp()

    def click(self):
        pyautogui.click()
