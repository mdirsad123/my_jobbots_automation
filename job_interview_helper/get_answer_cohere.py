"""
python -m python_code_practice.get_answer_cohere
"""
import os
import cohere
import mss
import mss.tools
import pytesseract
from PIL import Image

co = cohere.Client("aRyUD9I9nNy0YtoNF20VTkW1b7R5ajn4mC2qvVxW")

def take_screenshot() -> str:
    filename = "screen1.png"
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        mss.tools.to_png(img.rgb, img.size, output=filename)
    return os.path.abspath(filename)


def extract_text_from_image(image_path: str) -> str:
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()


def get_answer_from_cohere(problem_text: str) -> str:
    response = co.chat(
        model="command-nightly",
        message=(
            "Solve the following programming interview problem in Python.\n"
            "Return ONLY the final Python code.\n\n"
            f"{problem_text}"
        ),
        temperature=0.3,
        max_tokens=500
    )
    return response.text.strip()


def get_answer_cohere() -> str:
    screenshot_path = take_screenshot()
    problem_text = extract_text_from_image(screenshot_path)

    if not problem_text:
        return "ERROR: No text detected in screenshot."

    return get_answer_from_cohere(problem_text)

if __name__ == "__main__":
    print(get_answer_cohere())
