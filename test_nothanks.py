import subprocess

ADB = r"C:\Users\chara\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("Ensure the AWESOME screen shows NO THANKS.")
input("Press Enter to tap NO THANKS, or Ctrl+C to cancel...")

subprocess.run(
    [ADB, "shell", "input", "tap", "540", "1765"],
    check=True,
    timeout=15
)

print("Tap sent. Check whether ToyJoy returns to the home screen.")
