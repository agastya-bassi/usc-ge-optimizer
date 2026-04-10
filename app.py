import streamlit as st
import pandas as pd

df = pd.read_csv("ge_double_count.csv")

st.title("USC GE Double-Count Finder")
st.markdown("Find courses that satisfy **two GE requirements** at once.")

# Filters
col1, col2 = st.columns(2)
with col1:
    cat1_filter = st.multiselect(
        "Filter by Category 1",
        options=sorted(df["category_1"].unique()),
        default=[]
    )
with col2:
    cat2_filter = st.multiselect(
        "Filter by Category 2",
        options=sorted(df["category_2"].unique()),
        default=[]
    )

search = st.text_input("Search by course code or name")

# Apply filters
filtered = df.copy()
if cat1_filter:
    filtered = filtered[filtered["category_1"].isin(cat1_filter)]
if cat2_filter:
    filtered = filtered[filtered["category_2"].isin(cat2_filter)]
if search:
    filtered = filtered[
        filtered["course_code"].str.contains(search, case=False) |
        filtered["course_name"].str.contains(search, case=False)
    ]

st.markdown(f"**{len(filtered)} courses found**")
st.dataframe(filtered, use_container_width=True)

# Stats
st.markdown("---")
st.subheader("Most Common Category Pairs")
pairs = df.groupby(["category_1", "category_2"]).size().reset_index(name="count")
pairs["pair"] = pairs["category_1"] + " + " + pairs["category_2"]
st.bar_chart(pairs.set_index("pair")["count"])