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


import concurrent.futures

def get_all_enrollments(df: pd.DataFrame) -> pd.DataFrame:
    def fetch_one(course_code):
        prefix = course_code.split()[0]
        number = course_code.split()[1][:3]
        url = f"https://classes.usc.edu/api/Search/Basic?termCode=20263&searchTerm={prefix}+{number}"
        try:
            response = requests.get(url, timeout=8)
            data = response.json()
            total = 0
            registered = 0
            open_seats = 0
            for course in data.get("courses", []):
                for section in course.get("sections", []):
                    if section.get("rnrMode") == "Lecture":
                        t = section.get("totalSeats") or 0
                        r = section.get("registeredSeats") or 0
                        total += t
                        registered += r
                        open_seats += max(0, t - r)
            return {"course_code": course_code, "total_seats": total, "registered_seats": registered, "open_seats": open_seats}
        except:
            return {"course_code": course_code, "total_seats": 0, "registered_seats": 0, "open_seats": 0}

    course_codes = df["course_code"].unique().tolist()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_one, course_codes))

    return pd.DataFrame(results)

if __name__ == "__main__":
    ge_df = pd.read_csv("ge_double_count.csv")
    print("Fetching live enrollment for all double-count courses...")
    enrollment_df = get_all_enrollments(ge_df)
    enrollment_df.to_csv("enrollment_data.csv", index=False)
    print(f"Done. Saved {len(enrollment_df)} courses.")