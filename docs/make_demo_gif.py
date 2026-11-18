"""Record docs/demo.gif from the running app (dev-only tool: pip install playwright pillow && playwright install chromium).
Run: uvicorn coach.server:app --port 8777  then  python docs/make_demo_gif.py http://127.0.0.1:8777"""
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8777"
OUT = Path(__file__).parent / "demo.gif"
frames = []


def shot(page, caption):
    img = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    bar = Image.new("RGB", (img.width, 56), (31, 35, 40))
    draw = ImageDraw.Draw(bar)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    draw.text((24, 14), caption, fill=(255, 255, 255), font=font)
    frame = Image.new("RGB", (img.width, img.height + 56))
    frame.paste(bar, (0, 0)); frame.paste(img, (0, 56))
    frames.append(frame.resize((frame.width * 3 // 4, frame.height * 3 // 4)))


def scroll_to(page, selector):
    page.evaluate("s => document.querySelector(s).scrollIntoView({block: 'start'})", selector)
    page.wait_for_timeout(600)


with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1280, "height": 800}, color_scheme="light")
    page.goto(URL); page.wait_for_selector("#grade option[value='6']", state="attached")
    shot(page, "1. Open the coach: no login, no tracking")
    page.select_option("#grade", "6"); shot(page, "2. Pick a grade (1-10)...")
    page.select_option("#topic", "dividing-fractions"); page.wait_for_selector("#part-1")
    page.wait_for_timeout(800); shot(page, "3. ...and a topic: what the lesson covers + the 40-minute plan")
    scroll_to(page, "#notes section:nth-of-type(2)"); shot(page, "4. Short theory: the idea, why it works, one example")
    scroll_to(page, "#part-1"); page.wait_for_timeout(800); shot(page, "5. Each part: 2 ways to explain it + an example")
    page.evaluate("document.querySelector('#part-1 .jxgbox')?.scrollIntoView({block: 'center'})"); page.wait_for_timeout(800)
    shot(page, "6. A drawing of the example (fixed template, checked values)")
    inputs = page.locator("#part-1 .controls input")
    if inputs.count() == 4:
        for i, v in enumerate(["5", "4", "1", "2"]):
            inputs.nth(i).fill(v)
        page.locator("#part-1 .controls button").first.click(); page.wait_for_timeout(600)
        shot(page, "7. Teachers change the numbers to fit their class")
    page.evaluate("[...document.querySelectorAll('#part-1 h3')].find(h => h.textContent.startsWith('Common'))?.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(500); shot(page, "8. Common mistakes + 3 questions students may ask")
    page.locator("#part-1 details summary").first.click()
    page.evaluate("document.querySelector('#part-1 details').scrollIntoView({block: 'center'})"); page.wait_for_timeout(500)
    shot(page, "9. A check question for the class (answer hidden, nothing scored)")
    page.evaluate("[...document.querySelectorAll('#notes h2')].find(h => h.textContent.startsWith('Last 10'))?.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(500); shot(page, "10. Last 10 minutes: extra examples + resources (Khan, Wolfram, GeoGebra, YouTube)")
    page.fill("#question", "Why do we flip the second fraction?"); page.click("#askbtn")
    page.wait_for_selector("#answer .answer", timeout=60000); page.wait_for_timeout(500)
    shot(page, "11. Optional side panel: ask one question (repeats come from the cache)")
    page.click("aside details:nth-of-type(2) summary"); page.fill("#feedback", "Printable worksheets would help my class.")
    page.click("#fbbtn"); page.wait_for_timeout(600); shot(page, "12. Tell us what you need (anonymous feedback)")
    page.click("#tab-mine"); page.wait_for_selector("#mine textarea")
    page.locator("#mine textarea").first.fill("Start with pizza slices: how many 1/4 slices fit in 2 pizzas?")
    page.click("#mine button.primary"); page.wait_for_timeout(500)
    shot(page, "13. My notes tab: the teacher's own notes, verified saves, on this device only")
    box = page.locator("#mine canvas").bounding_box()
    page.evaluate("document.querySelector('#mine canvas').scrollIntoView({block: 'center'})"); page.wait_for_timeout(300)
    box = page.locator("#mine canvas").bounding_box()
    page.mouse.move(box["x"] + 60, box["y"] + 200); page.mouse.down()
    for i in range(40):
        page.mouse.move(box["x"] + 60 + i * 12, box["y"] + 200 - (i % 10) * 15)
    page.mouse.up(); page.wait_for_timeout(400); shot(page, "14. Sketch pad for their own drawings")
    page.click("#tab-notes"); page.select_option("#grade", "8"); page.select_option("#topic", "pythagorean-theorem")
    page.wait_for_selector("#part-1"); page.evaluate("document.querySelector('.jxgbox')?.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(1000); shot(page, "15. Every grade 1-10: e.g. grade 8, a draggable right triangle")
    page.select_option("#grade", "9"); page.select_option("#topic", "quadratic-equations")
    page.wait_for_selector("#part-1"); page.evaluate("document.querySelector('.jxgbox')?.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(1000); shot(page, "16. ...or grade 9, a function graph the teacher can retype")

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=2200, loop=0, optimize=True)
print(OUT, len(frames), "frames", OUT.stat().st_size // 1024, "KB")
