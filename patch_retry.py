from pathlib import Path
import re

p = Path("gamebot.py")
s = p.read_text(encoding="utf-8")

pattern = r'(?s)        if outcome == "revive":.*?(?=        if outcome == "positive":)'

replacement = '''        if outcome == "revive":
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

'''

new_s, count = re.subn(pattern, replacement, s)

if count != 1:
    raise SystemExit(
        f"Expected one matching GIVE UP block, found {count}. "
        "No changes were made."
    )

p.write_text(new_s, encoding="utf-8")
print("Patch applied: faster confirmation and verified retries.")
