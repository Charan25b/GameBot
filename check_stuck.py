import gamebot

refs = gamebot.load_refs()
img = gamebot.screenshot()
state, scores = gamebot.detect(img, refs)

print("Detected state:", state)
for name, score in scores.items():
    print(f"{name}: {score:.3f}")