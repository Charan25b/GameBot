from pathlib import Path

p = Path("gamebot.py")
s = p.read_text(encoding="utf-8")

old = '''        if outcome == "revive":
            tap("give_up")
            outcome = wait_for(
                refs, {"positive", "negative"},
                "result after GIVE UP"
            )
'''

new = '''        if outcome == "revive":
            print("REVIVE screen found. Waiting for GIVE UP to stay visible...")

            # Require several consecutive detections and a minimum
            # visible period before tapping, to avoid transition frames.
            visible_since = None
            consecutive = 0
            tapped = False
            deadline = time.monotonic() + 30

            while time.monotonic() < deadline:
                frame = screenshot()
                state, scores = detect(frame, refs)

                if state == "revive":
                    if visible_since is None:
                        visible_since = time.monotonic()
                    consecutive += 1

                    visible_for = time.monotonic() - visible_since
                    if consecutive >= 4 and visible_for >= 2.5:
                        tap("give_up")
                        tapped = True
                        break
                else:
                    visible_since = None
                    consecutive = 0

                time.sleep(POLL)

            if not tapped:
                raise TimeoutError(
                    "GIVE UP was not stably detected; stopping safely"
                )

            # Verify that the result screen actually appears.
            outcome = wait_for(
                refs, {"positive", "negative"},
                "result after GIVE UP", timeout=30
            )
'''

if old not in s:
    raise SystemExit(
        "Could not find the expected code block. No changes were made."
    )

p.write_text(s.replace(old, new), encoding="utf-8")
print("Updated GIVE UP detection safely.")
