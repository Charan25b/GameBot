import subprocess
import time

ADB = r"C:\Users\chara\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def adb(*args):
    return subprocess.run(
        [ADB, *args],
        check=True,
        timeout=15,
        capture_output=True
    ).stdout

# Phone resolution: 1080 x 2340
# Approximate center of the PLAY button.
X, Y = 540, 1300

print("Check your phone: ToyJoy home screen should be visible.")
input("Press Enter to send ONE tap to PLAY, or Ctrl+C to cancel...")

adb("get-state")
print("Sending one tap...")
adb("shell", "input", "tap", str(X), str(Y))

time.sleep(2)
adb("exec-out", "screencap", "-p")
print("Tap command sent. Check whether the game started.")
