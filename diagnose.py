import subprocess
import cv2
import numpy as np
from pathlib import Path

ADB = r"C:\Users\chara\AppData\Local\Android\Sdk\platform-tools\adb.exe"
ROOT = Path(__file__).resolve().parent

REGIONS = {
    "play":     (0.10, 0.50, 0.90, 0.62),
    "revive":   (0.20, 0.63, 0.80, 0.72),
    "positive": (0.20, 0.72, 0.80, 0.80),
    "negative": (0.25, 0.64, 0.75, 0.73),
}

def adb(*args):
    return subprocess.run(
        [ADB, *args], capture_output=True, check=True, timeout=20
    ).stdout

def crop(image, box):
    h, w = image.shape[:2]
    l, t, r, b = box
    return image[int(t*h):int(b*h), int(l*w):int(r*w)]

def normalize(image):
    image = cv2.resize(image, (160, 80))
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

live = cv2.imread(str(ROOT / "live_current.png"))
if live is None:
    raw = adb("exec-out", "screencap", "-p")
    live = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite(str(ROOT / "live_current.png"), live)

print("Live screen:", live.shape[1], "x", live.shape[0])

for state in ("play", "revive", "positive", "negative"):
    ref = cv2.imread(str(ROOT / f"{state}.png"))
    if ref is None:
        print(state, ": missing reference")
        continue

    a = normalize(crop(live, REGIONS[state]))
    b = normalize(crop(ref, REGIONS[state]))
    score = cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)[0, 0]
    print(f"{state}: {float(score):.3f}")

print("Diagnostic complete. No taps sent.")
