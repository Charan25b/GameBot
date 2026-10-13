
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
    # Focus on the relatively stable GIVE UP text.
    "revive":   (0.33, 0.65, 0.66, 0.70),
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
    "revive": 0.35,
    "positive": 0.85,
    "negative": 0.85,
}

POLL = 0.7
TIMEOUT = 900
MAX_ROUNDS = 20


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
    time.sleep(1.5)


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
    print("ToyJoy GameBot â€” 20-round timing test")
    print("Stop with Ctrl+C.")
    adb("get-state")
    refs = load_refs()

    # Diagnostic: inspect the current screen before tapping anything.
    img = screenshot()
    initial, scores = detect(img, refs)
    print("Initial screen:", initial)
    print("Scores:", {k: round(v, 3) for k, v in scores.items()})

    if initial != "play":
        raise RuntimeError(
            "Open the ToyJoy HOME screen with PLAY visible first. "
            "Do not start from the REVIVE screen."
        )

    durations = []
    positive_count = 0
    negative_count = 0

    for round_number in range(1, MAX_ROUNDS + 1):
        # Measure from tapping PLAY until HOME is detected again.
        round_started = time.monotonic()
        tap("play")

        outcome = wait_for(
            refs, {"revive", "positive", "negative"},
            "REVIVE or result screen"
        )

        if outcome == "revive":
            print("REVIVE detected. Using verified GIVE UP retries...")

            resolved = False

            for attempt in range(1, 4):
                # Never tap GIVE UP unless REVIVE is currently detected.
                state, scores = detect(screenshot(), refs)

                if state in {"positive", "negative"}:
                    outcome = state
                    resolved = True
                    print(f"Result already visible: {outcome}")
                    break

                if state != "revive":
                    print(
                        f"Attempt {attempt}: screen unclear; "
                        "checking for result without tapping."
                    )
                    try:
                        outcome = wait_for(
                            refs, {"positive", "negative"},
                            "result screen", timeout=5
                        )
                        resolved = True
                        break
                    except TimeoutError:
                        continue

                print(f"GIVE UP attempt {attempt}/3")
                tap("give_up")

                try:
                    outcome = wait_for(
                        refs, {"positive", "negative"},
                        "result after GIVE UP", timeout=8
                    )
                    resolved = True
                    break
                except TimeoutError:
                    state, scores = detect(screenshot(), refs)
                    print(
                        f"No result yet; current detection={state}, "
                        f"scores={ {k: round(v, 2) for k, v in scores.items()} }"
                    )

                    if state in {"positive", "negative"}:
                        outcome = state
                        resolved = True
                        break

                    if state == "revive":
                        print("REVIVE still visible; will retry.")
                    else:
                        print("Unclear screen; next attempt will recheck first.")

            if not resolved:
                raise TimeoutError(
                    "No result after 3 GIVE UP attempts. "
                    "Stopping safely for diagnosis."
                )

        if outcome == "positive":
            positive_count += 1
            tap("no_thanks")
        elif outcome == "negative":
            negative_count += 1
            tap("home")

        wait_for(refs, {"play"}, "home after result")

        elapsed = time.monotonic() - round_started
        durations.append(elapsed)

        avg = sum(durations) / len(durations)
        rounds_per_hour = 3600 / avg

        print(f"\nCompleted rounds: {round_number}/{MAX_ROUNDS}")
        print(f"This round:       {elapsed:.1f} seconds")
        print(f"Average round:    {avg:.1f} seconds")
        print(f"Shortest round:   {min(durations):.1f} seconds")
        print(f"Longest round:    {max(durations):.1f} seconds")
        print(f"Estimated rate:   {rounds_per_hour:.1f} rounds/hour")
        print(f"Positive results: {positive_count}")
        print(f"Negative results: {negative_count}")
        print("-" * 35, flush=True)

    total = sum(durations)
    print("\n20-ROUND TEST FINISHED")
    print(f"Total timed:       {total/60:.2f} minutes")
    print(f"Average per round: {total/len(durations):.2f} seconds")
    print(f"Rounds/hour:       {3600/(total/len(durations)):.1f}")
    print(f"Positive results:  {positive_count}")
    print(f"Negative results:  {negative_count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as exc:
        print(f"\nBOT STOPPED: {exc}", file=sys.stderr)
        sys.exit(1)


