from pathlib import Path
import re

p = Path("gamebot.py")
s = p.read_text(encoding="utf-8")

# Correct timeout keyword arguments if the earlier edit changed them.
s = s.replace(
    "capture_output=True, TIMEOUT = 300",
    "capture_output=True, timeout=20"
)
s = s.replace('"result screen", TIMEOUT = 300', '"result screen", timeout=5')
s = s.replace('"result after GIVE UP", TIMEOUT = 300', '"result after GIVE UP", timeout=8')

# Change fixed-round configuration to periodic summaries.
if "MAX_ROUNDS = 20" not in s:
    raise SystemExit("MAX_ROUNDS = 20 not found. No changes saved.")

s = s.replace("MAX_ROUNDS = 20", "SUMMARY_EVERY = 10", 1)

# Update the startup message.
s = re.sub(
    r'print\("ToyJoy GameBot.*?"\)',
    'print("ToyJoy GameBot - UNLIMITED MODE")',
    s,
    count=1
)

# Replace the fixed-round loop with an unlimited loop.
old_loop = "    for round_number in range(1, MAX_ROUNDS + 1):"
if old_loop not in s:
    raise SystemExit("Expected fixed-round loop not found. No changes saved.")

s = s.replace(
    old_loop,
    "    round_number = 0\n    while True:\n        round_number += 1",
    1
)

# Remove / replace the completed-round label.
s = re.sub(
    r'print\(f"\\nCompleted rounds: \{round_number\}/\{MAX_ROUNDS\}"\)',
    'print(f"\\nCompleted rounds: {round_number}")',
    s,
    count=1
)

# Add a summary every 10 completed rounds.
separator = '        print("-" * 35, flush=True)'
if separator not in s:
    raise SystemExit("Progress separator not found. No changes saved.")

summary = '''        print("-" * 35, flush=True)

        if round_number % SUMMARY_EVERY == 0:
            total = sum(durations)
            avg_all = total / len(durations)
            print("\\\\n========== PROGRESS SUMMARY ==========")
            print(f"Rounds completed:  {round_number}")
            print(f"Elapsed game time: {total/3600:.2f} hours")
            print(f"Average per round: {avg_all:.2f} seconds")
            print(f"Estimated rate:    {3600/avg_all:.1f} rounds/hour")
            print(f"Positive results:  {positive_count}")
            print(f"Negative results:  {negative_count}")
            print("======================================", flush=True)'''

s = s.replace(separator, summary, 1)

# Remove the now-obsolete end-of-20-round summary.
s = re.sub(
    r'\n    total = sum\(durations\)\n    print\("\\\\n20-ROUND TEST FINISHED".*?'
    r'print\(f"Negative results:.*?\)',
    '',
    s,
    count=1,
    flags=re.DOTALL
)

# Ensure the five-minute general wait remains configured.
if not re.search(r'^TIMEOUT\s*=\s*300\s*$', s, flags=re.MULTILINE):
    raise SystemExit("TIMEOUT = 300 was not found. No changes saved.")

p.write_text(s, encoding="utf-8")
print("Unlimited mode patch applied.")
