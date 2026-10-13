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

FILES = {
    "play": "play.png",
    "revive": "revive.png",
    "positive": "positive.png",
    "negative": "negative.png",
}


def adb(*args):
    return subprocess.run(
        [ADB, *args], capture_output=True, check=True, timeout=15
    ).stdout


def crop(image, box):
    h, w = image.shape[:2]
    l, t, r, b = box
    return image[int(t*h):int(b*h), int(l*w):int(r*w)]


def normalize(image):
    return cv2.resize(
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (160, 80)
    )


def main():
    raw = adb("exec-out", "screencap", "-p")
    live = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)

    if live is None:
        raise RuntimeError("Could not capture phone screen")

    print("Phone screen resolution:", live.shape[1], "x", live.shape[0])
    print("Reference matching scores (higher is better):")

    for state, filename in FILES.items():
        path = ROOT / filename
        if not path.exists():
            print(f"{state}: MISSING {filename}")
            continue

        reference = cv2.imread(str(path))
        if reference is None:
            print(f"{state}: could not read {filename}")
            continue

        a = normalize(crop(live, REGIONS[state]))
        b = normalize(crop(reference, REGIONS[state]))

        score = cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)[0, 0]
        print(f"{state}: {float(score):.3f}")

    cv2.imwrite(str(ROOT / "live_test.png"), live)
    print("Saved live screenshot to live_test.png")
    print("This test sends no taps.")


if __name__ == "__main__":
    main()
