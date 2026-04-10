import requests
import pandas as pd
import time


def get_enrollment(course_code: str, term_code: str = "20263") -> list:
    """
    Fetch live enrollment data for a course from USC's API.
    Returns list of sections with seat info.
    """
    prefix = course_code.split()[0]  # e.g. "AMST" from "AMST 101mgw"
    number = course_code.split()[1][:3]  # e.g. "101" from "101mgw"

    url = f"https://classes.usc.edu/api/Search/Basic?termCode={term_code}&searchTerm={prefix}+{number}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        sections = []
        for course in data.get("courses", []):
            for section in course.get("sections", []):
                sections.append({
                    "course_code": course_code,
                    "section_id": section.get("sisSectionId"),
                    "total_seats": section.get("totalSeats"),
                    "registered_seats": section.get("registeredSeats"),
                    "waitlisted_seats": section.get("waitlistedSeats") or 0,
                    "is_full": section.get("isFull"),
                    "open_seats": max(0, (section.get("totalSeats") or 0) - (section.get("registeredSeats") or 0)),
                    "mode": section.get("rnrMode"),
                    "days": str(section.get("schedule", [{}])[0].get("days", [])),
                    "start_time": section.get("schedule", [{}])[0].get("startTime", ""),
                })
        return sections
    except Exception as e:
        print(f"Error fetching {course_code}: {e}")
        return []


# Test on one course
sections = get_enrollment("AMST 101mgw")
for s in sections:
    print(s)


def get_all_enrollments(df: pd.DataFrame) -> pd.DataFrame:
    """Fetch enrollment for all double-count courses."""
    all_sections = []

    for i, course_code in enumerate(df["course_code"].unique()):
        print(f"Fetching {i + 1}/{len(df)}: {course_code}")
        sections = get_enrollment(course_code)
        all_sections.extend(sections)
        time.sleep(0.3)  # be polite to USC's servers

    if not all_sections:
        return pd.DataFrame()

    sections_df = pd.DataFrame(all_sections)

    # Summarize per course — only lecture sections
    summary = sections_df[sections_df["mode"] == "Lecture"].groupby("course_code").agg(
        total_seats=("total_seats", "sum"),
        registered_seats=("registered_seats", "sum"),
        open_seats=("open_seats", "sum"),
        sections_available=("section_id", "count"),
        any_open=("is_full", lambda x: not all(x))
    ).reset_index()

    return summary


# Run for all courses
ge_df = pd.read_csv("ge_double_count.csv")
print("Fetching live enrollment for all 120 double-count courses...")
enrollment_df = get_all_enrollments(ge_df)
enrollment_df.to_csv("enrollment_data.csv", index=False)
print("\nDone. Sample:")
print(enrollment_df.head(10).to_string())