import cv2
import gamebot

refs = gamebot.load_refs()
img = gamebot.screenshot()

for state, region in gamebot.REGIONS.items():
    live = gamebot.crop(img, region)
    reference = cv2.imread(str(gamebot.ROOT / gamebot.FILES[state]))
    reference_crop = gamebot.crop(reference, region)

    cv2.imwrite(f"live_{state}.png", live)
    cv2.imwrite(f"reference_{state}.png", reference_crop)

    score = cv2.matchTemplate(
        gamebot.normalize(live),
        refs[state],
        cv2.TM_CCOEFF_NORMED
    )[0, 0]

    print(f"{state}: {score:.3f}")

print("Diagnostic images saved in GameBot.")
