from pathlib import Path
import subprocess
import time
import sys
import cv2
import numpy as np

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
TAPS = {
    "play": (540, 1300),
    "give_up": (540, 1575),
    "no_thanks": (540, 1765),
    "home": (540, 1615),
}
THRESHOLDS = {
    "play": 0.90,
    "revive": 0.72,
    "positive": 0.85,
    "negative": 0.85,
}
POLL = 0.7
TIMEOUT = 900


def adb(*args):
    return subprocess.run(
        [ADB, *args], check=True, capture_output=True, timeout=20
    ).stdout


def screenshot():
    raw = adb("exec-out", "screencap", "-p")
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Screenshot capture failed")
    return img


def crop(img, region):
    h, w = img.shape[:2]
    l, t, r, b = region
    return img[int(t*h):int(b*h), int(l*w):int(r*w)]


def normalize(img):
    img = cv2.resize(img, (160, 80))
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def load_refs():
    refs = {}
    for state, filename in FILES.items():
        img = cv2.imread(str(ROOT / filename))
        if img is None:
            raise FileNotFoundError(f"Cannot read {filename}")
        refs[state] = normalize(crop(img, REGIONS[state]))
    return refs


def detect(img, refs):
    scores = {}
    for state, ref in refs.items():
        current = normalize(crop(img, REGIONS[state]))
        value = cv2.matchTemplate(
            current, ref, cv2.TM_CCOEFF_NORMED
        )[0, 0]
        scores[state] = float(value) if np.isfinite(value) else 0.0

    best = max(scores, key=scores.get)
    if scores[best] < THRESHOLDS[best]:
        return None, scores
    return best, scores


def tap(name):
    x, y = TAPS[name]
    print(f"TAP {name} ({x}, {y})", flush=True)
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(2)


def wait_for(refs, accepted, description, timeout=TIMEOUT):
    print(f"Waiting for {description}...", flush=True)
    started = time.monotonic()
    last_log = 0
    consecutive = 0

    while time.monotonic() - started < timeout:
        img = screenshot()
        state, scores = detect(img, refs)

        if state in accepted:
            consecutive += 1
            if consecutive >= 2:
                print(f"Detected {state}", flush=True)
                return state
        else:
            consecutive = 0

        if time.monotonic() - last_log >= 5:
            summary = " ".join(
                f"{k}={v:.2f}" for k, v in scores.items()
            )
            print(f"  Current: {state}; {summary}", flush=True)
            last_log = time.monotonic()

        time.sleep(POLL)

    raise TimeoutError(f"Timed out waiting for {description}")


def main():
    print("ToyJoy GameBot. Stop with Ctrl+C.")
    adb("get-state")
    refs = load_refs()

    initial, scores = detect(screenshot(), refs)
    print("Initial screen:", initial)
    print("Scores:", {k: round(v, 3) for k, v in scores.items()})

    if initial != "play":
        raise RuntimeError("Open ToyJoy home screen with PLAY visible first")

    runs = 0
    while True:
        wait_for(refs, {"play"}, "home screen")
        tap("play")

        # A round can end with REVIVE, or go directly to a result.
        outcome = wait_for(
            refs, {"revive", "positive", "negative"},
            "REVIVE or result screen"
        )

        if outcome == "revive":
            tap("give_up")
            outcome = wait_for(
                refs, {"positive", "negative"}, "result after GIVE UP"
            )

        if outcome == "positive":
            # The saved positive reference includes the NO THANKS panel.
            # Wait until the delayed button is visible before tapping.
            tap("no_thanks")
        elif outcome == "negative":
            tap("home")

        wait_for(refs, {"play"}, "home after result")
        runs += 1
        print(f"Completed rounds: {runs}", flush=True)
        print("-" * 35, flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as exc:
        print(f"\nBOT STOPPED: {exc}", file=sys.stderr)
        sys.exit(1)
