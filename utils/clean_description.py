import re

def clean_job_description(raw_text: str) -> str:
    # print("Cleaning job description...")

    # 1. Replace newlines with space
    text = raw_text.replace("\n", " ")

    # 2. Remove unwanted phrases (LinkedIn junk)
    junk_phrases = [
        r"\b\d+d\b",                 # 2d, 3d, etc.
        r"\b\d+ days? ago\b",        # 2 days ago, 1 day ago
        r"\b\d+h\b",                 # 5h
        r"\b\d+m\b",                 # 10m
        r"\bFollow\b",
        r"•", r"●", r"🔹",            # Bullet characters
        r"\|.*?\|",                  # Text between pipes like |LinkedIn|
        r"\bVisible to anyone.*?\b",
        r"\b\d+(st|nd|rd|th)\+?\b",  # 3rd+, 1st+, etc.
        r"@",                        # @ symbols (mentions)
        r"\+",                       # literal plus sign
        r"\s+"                       # collapse extra spaces
    ]


    for pattern in junk_phrases:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # 3. Remove multiple spaces again
    text = re.sub(r"\s{2,}", " ", text)

    # 4. Strip trailing/leading space
    return text.strip()

