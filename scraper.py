import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

url = "https://dornsife.usc.edu/ge/courses/double-count/"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

full_text = soup.get_text()
lines = [line.strip() for line in full_text.split("\n") if line.strip()]

courses = []
current_cat1 = None
current_cat2 = None

for line in lines:
    # Detect category header like "GE-A and GE-G"
    cat_match = re.match(r"(GE-[A-H])\s+and\s+(GE-[A-H])", line)
    if cat_match:
        current_cat1 = cat_match.group(1)
        current_cat2 = cat_match.group(2)
        continue

    # Detect course line
    course_match = re.match(r"([A-Z]{2,4}\s\d{3}[A-Za-z]*),\s(.+?)\s*\|", line)
    if course_match and current_cat1:
        code = course_match.group(1).strip()
        name = course_match.group(2).strip()
        courses.append({
            "course_code": code,
            "course_name": name,
            "category_1": current_cat1,
            "category_2": current_cat2
        })

df = pd.DataFrame(courses)
print(df.to_string())
print(f"\nTotal: {len(df)} double-count courses")
df.to_csv("ge_double_count.csv", index=False)
print("Saved to ge_double_count.csv")