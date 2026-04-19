from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="TrendGuide", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "benchmark_for_web.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

def circular_hour_distance(a, b):
    diff = abs(int(a) - int(b))
    return min(diff, 24 - diff)

def hour_score(planned_hour, common_hour):
    d = circular_hour_distance(planned_hour, common_hour)
    if d == 0:
        return 50
    if d == 1:
        return 45
    if d == 2:
        return 38
    if d == 3:
        return 30
    if d == 4:
        return 20
    if d == 5:
        return 10
    return 0

def tag_score(tag_count, tag_min, tag_max, tag_median):
    tag_count = int(tag_count)
    tag_min = int(tag_min)
    tag_max = int(tag_max)
    tag_median = int(tag_median)

    if tag_min <= tag_count <= tag_max:
        if abs(tag_count - tag_median) <= 1:
            return 50
        return 42

    if tag_count < tag_min:
        gap = tag_min - tag_count
    else:
        gap = tag_count - tag_max

    if gap == 1:
        return 30
    if gap == 2:
        return 20
    if gap == 3:
        return 10
    return 0

def get_score_label(score):
    if score >= 85:
        return "Strong match"
    if score >= 65:
        return "Good match"
    if score >= 45:
        return "Moderate match"
    return "Weak match"

def get_advice(row, planned_hour, tag_count):
    advice = []

    common_hour = int(row["common_publish_hour"])
    tag_min = int(row["recommended_tag_min"])
    tag_max = int(row["recommended_tag_max"])
    tag_median = int(row["recommended_tag_median"])
    hour_diff = circular_hour_distance(planned_hour, common_hour)

    if hour_diff == 0:
        advice.append(f"Your planned posting time matches the most common trending hour in this market.")
    elif hour_diff <= 2:
        advice.append(f"Your posting time is close to the benchmark. Try staying within {row['hour_window_text']}.")
    else:
        advice.append(f"Your posting time is far from the benchmark. Consider posting around {row['hour_window_text']}.")

    if tag_min <= tag_count <= tag_max:
        if abs(tag_count - tag_median) <= 1:
            advice.append(f"Your tag count is very close to the benchmark median of {tag_median}.")
        else:
            advice.append(f"Your tag count is within the typical range for trending videos in this category.")
    elif tag_count < tag_min:
        advice.append(f"Your tag count is below the typical range. Consider increasing it toward {tag_median}.")
    else:
        advice.append(f"Your tag count is above the typical range. Consider reducing it toward {tag_median}.")

    if int(row["video_count"]) < 10:
        advice.append("Limited benchmark data in this category. Suggestions may be less reliable.")

    return advice

if not DATA_PATH.exists():
    st.error(f"Data file not found: {DATA_PATH}")
    st.stop()

df = load_data()

st.title("TrendGuide")
st.write("A simple benchmark tool for small YouTube creators.")

countries = sorted(df["country"].dropna().unique().tolist())
selected_country = st.selectbox("Select country", countries)

filtered_country = df[df["country"] == selected_country].copy()
categories = filtered_country.sort_values("category_name")["category_name"].unique().tolist()
selected_category = st.selectbox("Select category", categories)

selected_row = filtered_country[filtered_country["category_name"] == selected_category].iloc[0]

col1, col2 = st.columns(2)
with col1:
    planned_hour = st.slider("Planned publish hour", 0, 23, int(selected_row["common_publish_hour"]))
with col2:
    tag_count = st.number_input("Tag count", min_value=0, max_value=50, value=int(selected_row["recommended_tag_median"]), step=1)

score = hour_score(planned_hour, selected_row["common_publish_hour"]) + tag_score(
    tag_count,
    selected_row["recommended_tag_min"],
    selected_row["recommended_tag_max"],
    selected_row["recommended_tag_median"]
)

score_label = get_score_label(score)
advice_list = get_advice(selected_row, planned_hour, tag_count)

st.subheader("Benchmark Summary")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Recommended posting window", selected_row["hour_window_text"])
m2.metric("Recommended tag range", selected_row["tag_range_text"])
m3.metric("Avg engagement rate", f"{selected_row['avg_engagement_rate_pct']:.2f}%")
m4.metric("Benchmark sample size", int(selected_row["video_count"]))

m5, m6, m7, m8 = st.columns(4)
m5.metric("Avg like rate", f"{selected_row['avg_like_rate_pct']:.2f}%")
m6.metric("Avg comment rate", f"{selected_row['avg_comment_rate_pct']:.2f}%")
m7.metric("Common publish hour", f"{int(selected_row['common_publish_hour']):02d}:00")
m8.metric("Median tag count", int(selected_row["recommended_tag_median"]))

st.subheader("Your Match Score")

s1, s2 = st.columns([1, 2])
with s1:
    st.metric("Score", f"{score}/100")
    st.write(score_label)
with s2:
    st.progress(score / 100)

if int(selected_row["video_count"]) < 10:
    st.warning("Limited benchmark data in this category. Suggestions may be less reliable.")

st.subheader("Suggestions")
for item in advice_list:
    st.write(f"- {item}")

with st.expander("Show raw benchmark data"):
    display_row = selected_row.to_frame().T
    st.dataframe(display_row, width="stretch")