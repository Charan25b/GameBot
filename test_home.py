import subprocess

ADB = r"C:\Users\chara\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("Make sure the negative-score result screen and HOME button are visible.")
input("Press Enter to tap HOME, or Ctrl+C to cancel...")

subprocess.run(
    [ADB, "shell", "input", "tap", "540", "1615"],
    check=True,
    timeout=15
)

print("Tap sent. Check whether ToyJoy returned to the home screen.")
