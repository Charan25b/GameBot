from pathlib import Path
import re

p = Path("gamebot.py")
s = p.read_text(encoding="utf-8-sig")

# Keep ADB command timeout at 20 seconds; screen waits use TIMEOUT below.
s = s.replace(
    "capture_output=True, TIMEOUT = 300",
    "capture_output=True, timeout=20"
)

# Preserve the original short waits for GIVE UP retries.
s = s.replace('"result screen", TIMEOUT = 300', '"result screen", timeout=5')
s = s.replace('"result after GIVE UP", TIMEOUT = 300', '"result after GIVE UP", timeout=8')

# Set the general screen-wait timeout to five minutes.
if not re.search(r"^TIMEOUT\s*=\s*\d+\s*$", s, re.M):
    raise SystemExit("TIMEOUT setting not found; file was not changed.")

s = re.sub(r"^TIMEOUT\s*=\s*\d+\s*$", "TIMEOUT = 300", s, count=1, flags=re.M)

# Replace the fixed 20-round loop with an unlimited loop.
old_loop = "    for round_number in range(1, MAX_ROUNDS + 1):"
if old_loop not in s:
    raise SystemExit("Expected 20-round loop not found; file was not changed.")

s = s.replace(
    old_loop,
    "    round_number = 0\n    while True:\n        round_number += 1",
    1
)

# Remove the fixed limit from progress output.
s = s.replace(
    'print(f"\\nCompleted rounds: {round_number}/{MAX_ROUNDS}")',
    'print(f"\\nCompleted rounds: {round_number}")',
    1
)

# Validate the complete edited source before writing it.
compile(s, str(p), "exec")
p.write_text(s, encoding="utf-8")
print("SUCCESS: Unlimited loop and 300-second screen timeout applied.")
print("All other game logic preserved.")
