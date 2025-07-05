import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import cvzone
from pynput.keyboard import Controller
import time

# Initialize camera
cam = cv2.VideoCapture(0)
cam.set(3, 1280)
cam.set(4, 720)

# Hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)
keyboard = Controller()

# Colors
KEY_COLOR = (102, 204, 204)
HOVER_COLOR = (41, 128, 185)
CLICK_COLOR = (52, 152, 219)
TEXT_COLOR = (255, 255, 255)
TEXT_BG_COLOR = (44, 62, 80)
BORDER_COLOR = (189, 195, 199)

# Cooldown settings
isClicked = False
clickStartTime = 0
cooldown = 0.5

# Final typed text
finalText = ""

# Keyboard layout
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["SPACE", "BACKSPACE", "CLEAR"]]

# Button class
class Button():
    def __init__(self, pos, text, size=None):
        self.pos = pos
        self.text = text
        self.size = size if size else [85, 85]

# Create all keys
buttonList = []
for i, row in enumerate(keys):
    for j, key in enumerate(row):
        if key == "SPACE":
            pos = [390, 100 * i + 50]
            size = [300, 85]
        elif key == "BACKSPACE":
            pos = [700, 100 * i + 50]
            size = [200, 85]
        elif key == "CLEAR":
            pos = [910, 100 * i + 50]
            size = [200, 85]
        else:
            pos = [100 * j + 50, 100 * i + 50]
            size = [85, 85]
        buttonList.append(Button(pos, key, size))

# Main loop
while True:
    success, img = cam.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    # Overlay background for keyboard
    kb_overlay = img.copy()
    cv2.rectangle(kb_overlay, (30, 30), (1250, 450), TEXT_BG_COLOR, cv2.FILLED)
    img = cv2.addWeighted(kb_overlay, 0.35, img, 0.65, 0)

    # Draw keys
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, (x, y), (x + w, y + h), KEY_COLOR, cv2.FILLED)
        cv2.rectangle(img, (x, y), (x + w, y + h), BORDER_COLOR, 2)
        cvzone.cornerRect(img, (x, y, w, h), 20, rt=0, colorC=BORDER_COLOR)
        font_scale = 2 if len(button.text) > 1 else 4
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, font_scale, TEXT_COLOR, 2)

    # Finger detection and interaction
    if hands:
        lmList = hands[0]['lmList']
        x1, y1 = lmList[8][0], lmList[8][1]   # index finger
        x2, y2 = lmList[12][0], lmList[12][1] # middle finger
        l, _, _ = detector.findDistance((x1, y1), (x2, y2))

        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            if x < x1 < x + w and y < y1 < y + h:
                # Hover
                cv2.rectangle(img, (x, y), (x + w, y + h), HOVER_COLOR, cv2.FILLED)
                cv2.putText(img, button.text, (x + 20, y + 65),
                            cv2.FONT_HERSHEY_PLAIN, font_scale, TEXT_COLOR, 2)

                currTime = time.time()
                if l < 40 and not isClicked and (currTime - clickStartTime > cooldown):
                    # Click
                    cv2.rectangle(img, (x, y), (x + w, y + h), CLICK_COLOR, cv2.FILLED)
                    cv2.putText(img, button.text, (x + 20, y + 65),
                                cv2.FONT_HERSHEY_PLAIN, font_scale, TEXT_COLOR, 2)

                    if button.text == "SPACE":
                        finalText += " "
                        keyboard.press(" ")
                        keyboard.release(" ")
                    elif button.text == "BACKSPACE":
                        finalText = finalText[:-1]
                        keyboard.press('\b')
                        keyboard.release('\b')
                    elif button.text == "CLEAR":
                        finalText = ""
                    else:
                        finalText += button.text
                        keyboard.press(button.text.lower())
                        keyboard.release(button.text.lower())

                    isClicked = True
                    clickStartTime = currTime
                elif l > 40:
                    isClicked = False

    # Draw typed text area
    txt_overlay = img.copy()
    cv2.rectangle(txt_overlay, (50, 500), (1230, 620), TEXT_BG_COLOR, cv2.FILLED)
    img = cv2.addWeighted(txt_overlay, 0.5, img, 0.5, 0)
    cv2.rectangle(img, (50, 500), (1230, 620), BORDER_COLOR, 2)

    displayText = finalText[-50:]
    cv2.putText(img, displayText, (60, 580), cv2.FONT_HERSHEY_PLAIN, 5, TEXT_COLOR, 5)

    # Header and instructions
    cv2.putText(img, "Virtual Keyboard", (50, 25),
                cv2.FONT_HERSHEY_COMPLEX, 0.7, TEXT_COLOR, 1)
    cv2.putText(img, "Pinch to type", (1050, 25),
                cv2.FONT_HERSHEY_PLAIN, 1.2, TEXT_COLOR, 1)

    # Show FPS
    fps = int(1 / (time.time() - clickStartTime + 0.01))
    fps_overlay = img.copy()
    cv2.rectangle(fps_overlay, (1140, 680), (1230, 710), TEXT_BG_COLOR, cv2.FILLED)
    img = cv2.addWeighted(fps_overlay, 0.5, img, 0.5, 0)
    cv2.putText(img, f"FPS: {fps}", (1150, 700), cv2.FONT_HERSHEY_PLAIN, 1, TEXT_COLOR, 1)

    # Show frame
    cv2.imshow("Air Press Virtual Keyboard", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
