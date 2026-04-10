import streamlit as st
import pandas as pd
import requests
import concurrent.futures

st.set_page_config(page_title="USC GE Double-Count Finder", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0f0f0f; }
    .block-container { padding-top: 2rem; }
    h1 { color: #FF6B6B; font-size: 2.5rem; }
    .stDataFrame { border-radius: 10px; }
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
    }
    div[data-testid="metric-container"] label {
        color: #aaa;
    }
    div[data-testid="metric-container"] div {
        color: white;
        font-size: 2rem;
        font-weight: bold;
    }
    .stSpinner { color: #FF6B6B; }
    .stCaption { color: #666; font-size: 0.75rem; }
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 USC GE Double-Count Finder")
st.markdown("##### Find courses that satisfy two GE requirements at once — with live seat availability from WebReg.")

def fetch_one(course_code):
    prefix = course_code.split()[0]
    number = course_code.split()[1][:3]
    url = f"https://classes.usc.edu/api/Search/Basic?termCode=20263&searchTerm={prefix}+{number}"
    try:
        response = requests.get(url, timeout=4)  # down from 8
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

@st.cache_data(ttl=30)
@st.cache_data(ttl=420)
def load_data():
    ge_df = pd.read_csv("ge_double_count.csv")
    enrollment_df = pd.read_csv("https://raw.githubusercontent.com/agastya-bassi/usc-ge-optimizer/main/enrollment_data.csv")
    merged = ge_df.merge(enrollment_df, on="course_code", how="left")
    merged["status"] = merged["open_seats"].apply(lambda x: "✅ Open" if x > 0 else "🔴 Full")
    return merged

ge_df = pd.read_csv("ge_double_count.csv")
course_codes = tuple(ge_df["course_code"].unique())

with st.spinner("Fetching live enrollment from WebReg..."):
    df = load_data(course_codes)

# Sidebar
st.sidebar.header("Filters")
cat1_filter = st.sidebar.multiselect("Category 1", sorted(df["category_1"].unique()))
cat2_filter = st.sidebar.multiselect("Category 2", sorted(df["category_2"].unique()))
show_open_only = st.sidebar.checkbox("Show open courses only", value=False)
search = st.sidebar.text_input("Search course code or name")

# Apply filters
filtered = df.copy()
if cat1_filter:
    filtered = filtered[filtered["category_1"].isin(cat1_filter)]
if cat2_filter:
    filtered = filtered[filtered["category_2"].isin(cat2_filter)]
if show_open_only:
    filtered = filtered[filtered["open_seats"] > 0]
if search:
    filtered = filtered[
        filtered["course_code"].str.contains(search, case=False) |
        filtered["course_name"].str.contains(search, case=False)
    ]

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Courses Shown", len(filtered))
col2.metric("Open", len(filtered[filtered["open_seats"] > 0]))
col3.metric("Full", len(filtered[filtered["open_seats"] == 0]))

# Table
st.dataframe(
    filtered[["course_code", "course_name", "category_1", "category_2", "open_seats", "total_seats", "status"]].rename(columns={
        "course_code": "Course",
        "course_name": "Name",
        "category_1": "GE Cat 1",
        "category_2": "GE Cat 2",
        "open_seats": "Open Seats",
        "total_seats": "Total Seats",
        "status": "Status"
    }),
    use_container_width=True
)

st.caption("Live enrollment data from USC Schedule of Classes API. Refreshes every 30 seconds.")