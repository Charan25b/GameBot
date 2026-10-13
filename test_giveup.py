import subprocess

ADB = r"C:\Users\chara\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("Make sure REVIVE and GIVE UP are visible on your phone.")
input("Press Enter to tap GIVE UP, or Ctrl+C to cancel...")

subprocess.run(
    [ADB, "shell", "input", "tap", "540", "1575"],
    check=True,
    timeout=15
)

print("GIVE UP tap sent. Wait for the animation to finish.")
