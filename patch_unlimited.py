from pathlib import Path

p = Path("gamebot.py")
s = p.read_text(encoding="utf-8")

changes = [
    (
        "MAX_ROUNDS = 20",
        "SUMMARY_EVERY = 10"
    ),
    (
        'print("ToyJoy GameBot â€” 20-round timing test")',
        'print("ToyJoy GameBot - UNLIMITED MODE")'
    ),
    (
        "    for round_number in range(1, MAX_ROUNDS + 1):",
        "    round_number = 0\n    while True:\n        round_number += 1"
    ),
    (
        'print(f"Completed rounds: {round_number}/{MAX_ROUNDS}")',
        'print(f"Completed rounds: {round_number}")'
    ),
]

for old, new in changes:
    if old not in s:
        raise SystemExit(
            f"Could not find expected code to replace:\n{old}\n"
            "No further changes were made. Your backup is preserved."
        )
    s = s.replace(old, new, 1)

old_tail = '''    total = sum(durations)
    print("\\n20-ROUND TEST FINISHED")
    print(f"Total timed:       {total/60:.2f} minutes")
    print(f"Average per round: {total/len(durations):.2f} seconds")
    print(f"Rounds/hour:       {3600/(total/len(durations)):.1f}")
    print(f"Positive results:  {positive_count}")
    print(f"Negative results:  {negative_count}")
'''

new_tail = '''        if round_number % SUMMARY_EVERY == 0:
            total = sum(durations)
            avg_all = total / len(durations)
            print("\\\\n========== PROGRESS SUMMARY ==========")
            print(f"Rounds completed:  {round_number}")
            print(f"Elapsed time:      {total/3600:.2f} hours")
            print(f"Average per round: {avg_all:.2f} seconds")
            print(f"Estimated rate:    {3600/avg_all:.1f} rounds/hour")
            print(f"Positive results:  {positive_count}")
            print(f"Negative results:  {negative_count}")
            print("======================================", flush=True)
'''

if old_tail not in s:
    raise SystemExit(
        "Could not find the final 20-round summary block. "
        "No changes were saved. Your backup is preserved."
    )

s = s.replace(old_tail, new_tail, 1)
p.write_text(s, encoding="utf-8")
print("SUCCESS: Unlimited mode enabled.")
print("Existing retry logic, tap coordinates and result handling preserved.")
