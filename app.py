import time
from datetime import datetime, date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    init_db,
    get_activity,
    delete_all_activity
)

from ml_engine import (
    productivity_score,
    detect_anomalies,
    generate_explanation
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LifeLens AI",
    page_icon="🧠",
    layout="wide"
)

init_db()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 45px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 19px;
        color: gray;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🧠 LifeLens AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Personalized Digital Behavior & Productivity Analyzer
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD ALL DATA
# ============================================================

all_data = get_activity()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Control Panel")

    st.info(
        """
        LifeLens AI monitors application-level
        computer activity.

        It does NOT record:

        • Passwords
        • Keyboard content
        • Screenshots
        • Personal files
        """
    )

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if st.button(
        "🔄 Refresh Dashboard",
        use_container_width=True
    ):

        st.rerun()

    st.divider()

    # ========================================================
    # DATE FILTER
    # ========================================================

    st.subheader("📅 Time Period")

    period = st.selectbox(
        "Select period",
        [
            "Today",
            "Last 7 Days",
            "This Month",
            "Custom Date"
        ]
    )

    # --------------------------------------------------------
    # CUSTOM DATE
    # --------------------------------------------------------

    if period == "Custom Date":

        custom_start = st.date_input(
            "Start Date",
            value=date.today()
        )

        custom_end = st.date_input(
            "End Date",
            value=date.today()
        )

    st.divider()

    # ========================================================
    # FOCUS MODE
    # ========================================================

    st.subheader("🎯 Focus Mode")

    focus_minutes = st.number_input(
        "Focus duration (minutes)",
        min_value=1,
        max_value=180,
        value=25
    )

    if st.button(
        "▶ Start Focus",
        use_container_width=True
    ):

        st.session_state["focus_start"] = time.time()

        st.session_state["focus_duration"] = (
            focus_minutes * 60
        )

        st.success(
            "Focus session started!"
        )

    if st.button(
        "⏹ Stop Focus",
        use_container_width=True
    ):

        st.session_state.pop(
            "focus_start",
            None
        )

        st.session_state.pop(
            "focus_duration",
            None
        )

        st.info(
            "Focus session stopped."
        )

    st.divider()

    # ========================================================
    # DELETE DATA
    # ========================================================

    st.subheader("🗑️ Data")

    if st.button(
        "Delete All Activity",
        use_container_width=True
    ):

        delete_all_activity()

        st.success(
            "All activity has been deleted."
        )

        time.sleep(0.5)

        st.rerun()


# ============================================================
# FOCUS TIMER
# ============================================================

if "focus_start" in st.session_state:

    remaining = (
        st.session_state["focus_duration"]
        -
        (
            time.time()
            -
            st.session_state["focus_start"]
        )
    )

    if remaining > 0:

        minutes = int(
            remaining // 60
        )

        seconds = int(
            remaining % 60
        )

        st.warning(
            f"🎯 FOCUS MODE ACTIVE — "
            f"{minutes:02d}:{seconds:02d}"
        )

    else:

        st.success(
            "🎉 Focus session completed!"
        )

        st.session_state.pop(
            "focus_start",
            None
        )

        st.session_state.pop(
            "focus_duration",
            None
        )


# ============================================================
# CHECK DATA
# ============================================================

if all_data.empty:

    st.info(
        "👋 No activity has been collected yet."
    )

    st.markdown(
        """
        ### How to start

        1. Start the LifeLens tracker.
        2. Use your computer normally.
        3. Switch between applications.
        4. Come back to this dashboard.
        5. Click **Refresh Dashboard**.

        Your activity will automatically be stored
        in the local LifeLens database.
        """
    )

    st.stop()


# ============================================================
# CONVERT TIMESTAMP
# ============================================================

all_data["timestamp"] = pd.to_datetime(
    all_data["timestamp"],
    errors="coerce"
)

all_data = all_data.dropna(
    subset=["timestamp"]
)


# ============================================================
# SELECT DATE RANGE
# ============================================================

today = date.today()

if period == "Today":

    start_date = today

    end_date = today


elif period == "Last 7 Days":

    start_date = today - timedelta(days=6)

    end_date = today


elif period == "This Month":

    start_date = today.replace(day=1)

    end_date = today


else:

    start_date = custom_start

    end_date = custom_end


# ============================================================
# VALIDATE CUSTOM DATE
# ============================================================

if start_date > end_date:

    st.error(
        "Start Date cannot be after End Date."
    )

    st.stop()


# ============================================================
# FILTER DATA
# ============================================================

filtered_data = all_data[
    (
        all_data["timestamp"].dt.date
        >= start_date
    )
    &
    (
        all_data["timestamp"].dt.date
        <= end_date
    )
].copy()


# ============================================================
# NO DATA FOR SELECTED PERIOD
# ============================================================

if filtered_data.empty:

    st.warning(
        f"No activity data found from "
        f"{start_date.strftime('%d %b %Y')} "
        f"to "
        f"{end_date.strftime('%d %b %Y')}."
    )

    st.info(
        "Keep the tracker running and use your "
        "computer. Then refresh the dashboard."
    )

    st.stop()


# ============================================================
# FORMAT TIME
# ============================================================

def format_time(seconds):

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    if hours > 0:

        return (
            f"{hours}h {minutes}m"
        )

    return (
        f"{minutes}m"
    )


# ============================================================
# CALCULATE STATISTICS
# ============================================================

total_time = (
    filtered_data["duration_seconds"]
    .sum()
)

productive_time = filtered_data.loc[
    filtered_data["category"] == "Productive",
    "duration_seconds"
].sum()

distraction_time = filtered_data.loc[
    filtered_data["category"] == "Distraction",
    "duration_seconds"
].sum()

neutral_time = filtered_data.loc[
    filtered_data["category"] == "Neutral",
    "duration_seconds"
].sum()

idle_time = filtered_data.loc[
    filtered_data["category"] == "Idle",
    "duration_seconds"
].sum()


# ============================================================
# PRODUCTIVITY SCORE
# ============================================================

score = productivity_score(
    filtered_data
)


# ============================================================
# PERIOD HEADER
# ============================================================

st.subheader(
    f"📊 {period} Overview"
)

st.caption(
    f"{start_date.strftime('%d %b %Y')} "
    f"→ "
    f"{end_date.strftime('%d %b %Y')}"
)


# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)


col1.metric(
    "Productivity Score",
    f"{score}%"
)


col2.metric(
    "Total Tracked",
    format_time(total_time)
)


col3.metric(
    "Productive",
    format_time(productive_time)
)


col4.metric(
    "Distraction",
    format_time(distraction_time)
)


col5.metric(
    "Idle",
    format_time(idle_time)
)


# ============================================================
# SCORE MESSAGE
# ============================================================

if score >= 80:

    st.success(
        "🔥 Excellent productivity pattern!"
    )

elif score >= 60:

    st.info(
        "👍 Good productivity. "
        "There is room for improvement."
    )

elif score >= 40:

    st.warning(
        "⚠️ Moderate productivity. "
        "Try using Focus Mode."
    )

else:

    st.error(
        "🚨 Productive activity is currently low."
    )


# ============================================================
# DAILY PRODUCTIVITY
# ============================================================

st.subheader(
    "📈 Daily Productivity"
)


daily = filtered_data.copy()


daily["date"] = (
    daily["timestamp"].dt.date
)


daily_total = (
    daily
    .groupby("date")[
        "duration_seconds"
    ]
    .sum()
    .reset_index()
)


daily_productive = (
    daily[
        daily["category"] == "Productive"
    ]
    .groupby("date")[
        "duration_seconds"
    ]
    .sum()
    .reset_index()
)


daily_productive.rename(
    columns={
        "duration_seconds":
        "productive_seconds"
    },
    inplace=True
)


daily_chart = daily_total.merge(
    daily_productive,
    on="date",
    how="left"
)


daily_chart[
    "productive_seconds"
] = daily_chart[
    "productive_seconds"
].fillna(0)


daily_chart[
    "productivity_percentage"
] = (

    daily_chart[
        "productive_seconds"
    ]

    /

    daily_chart[
        "duration_seconds"
    ].replace(0, 1)

) * 100


daily_chart["productivity_percentage"] = (
    daily_chart[
        "productivity_percentage"
    ].round(1)
)


fig = px.line(

    daily_chart,

    x="date",

    y="productivity_percentage",

    markers=True,

    title="Productivity Percentage by Day"

)


fig.update_yaxes(
    range=[0, 100],
    title="Productivity %"
)

fig.update_xaxes(
    title="Date"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# DAILY TIME BREAKDOWN
# ============================================================

st.subheader(
    "📊 Daily Activity Breakdown"
)


daily_category = (

    filtered_data

    .assign(
        date=filtered_data[
            "timestamp"
        ].dt.date
    )

    .groupby(
        [
            "date",
            "category"
        ]
    )[
        "duration_seconds"
    ]

    .sum()

    .reset_index()

)


daily_category["minutes"] = (

    daily_category[
        "duration_seconds"
    ]

    /

    60

)


fig = px.bar(

    daily_category,

    x="date",

    y="minutes",

    color="category",

    barmode="stack",

    title="Daily Productive, Neutral, Distraction & Idle Time"

)


fig.update_xaxes(
    title="Date"
)

fig.update_yaxes(
    title="Minutes"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# ACTIVITY ANALYSIS
# ============================================================

st.subheader(
    "📈 Activity Analysis"
)


col1, col2 = st.columns(2)


# ============================================================
# PIE CHART
# ============================================================

with col1:

    category_data = (

        filtered_data

        .groupby(
            "category"
        )[
            "duration_seconds"
        ]

        .sum()

        .reset_index()

    )


    category_data["minutes"] = (

        category_data[
            "duration_seconds"
        ]

        /

        60

    )


    fig = px.pie(

        category_data,

        names="category",

        values="minutes",

        title="Where Your Time Goes"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# TOP APPLICATIONS
# ============================================================

with col2:

    applications = (

        filtered_data

        .groupby(
            "app_name"
        )[
            "duration_seconds"
        ]

        .sum()

        .reset_index()

        .sort_values(
            "duration_seconds",
            ascending=False
        )

        .head(10)

    )


    applications["minutes"] = (

        applications[
            "duration_seconds"
        ]

        /

        60

    )


    fig = px.bar(

        applications,

        x="minutes",

        y="app_name",

        orientation="h",

        title="Top Applications"

    )


    fig.update_xaxes(
        title="Minutes"
    )

    fig.update_yaxes(
        title="Application"
    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# HOURLY ACTIVITY
# ============================================================

st.subheader(
    "🕐 Activity by Hour"
)


hourly = filtered_data.copy()


hourly["hour"] = (
    hourly["timestamp"].dt.hour
)


hourly_data = (

    hourly

    .groupby(
        [
            "hour",
            "category"
        ]
    )[
        "duration_seconds"
    ]

    .sum()

    .reset_index()

)


hourly_data["minutes"] = (

    hourly_data[
        "duration_seconds"
    ]

    /

    60

)


fig = px.bar(

    hourly_data,

    x="hour",

    y="minutes",

    color="category",

    barmode="stack",

    title="Activity Distribution by Hour"

)


fig.update_xaxes(
    title="Hour of Day"
)

fig.update_yaxes(
    title="Minutes"
)


st.plotly_chart(

    fig,

    use_container_width=True

)


# ============================================================
# MACHINE LEARNING ANALYSIS
# ============================================================

st.subheader(
    "🤖 Machine Learning Analysis"
)


ml_data = detect_anomalies(
    filtered_data
)


if ml_data.empty:

    st.info(
        "Not enough data for ML analysis."
    )

elif len(ml_data) < 5:

    st.warning(

        f"ML is still learning your behavior. "
        f"Only {len(ml_data)} hourly records "
        f"are available."

    )

else:

    anomaly_count = int(
        ml_data["anomaly"].sum()
    )


    if anomaly_count > 0:

        st.warning(

            f"⚠️ {anomaly_count} unusual "
            "behavior period(s) detected."

        )

    else:

        st.success(
            "✅ No strong behavioral anomalies detected."
        )


# ============================================================
# ML TABLE
# ============================================================

if not ml_data.empty:

    ml_table = ml_data.copy()


    ml_table["hour"] = (

        ml_table[
            "hour"
        ].astype(str)

        +

        ":00"

    )


    for column in [

        "total_duration",
        "productive_time",
        "distraction_time",
        "idle_time"

    ]:

        if column in ml_table.columns:

            ml_table[column] = (

                ml_table[
                    column
                ]

                /

                60

            ).round(1)


    available_columns = [

        "hour",
        "total_duration",
        "productive_time",
        "distraction_time",
        "idle_time",
        "sessions",
        "anomaly"

    ]


    available_columns = [

        column

        for column in available_columns

        if column in ml_table.columns

    ]


    ml_table = ml_table[
        available_columns
    ]


    rename_columns = {

        "hour": "Hour",

        "total_duration":
        "Total Min",

        "productive_time":
        "Productive Min",

        "distraction_time":
        "Distraction Min",

        "idle_time":
        "Idle Min",

        "sessions":
        "Sessions",

        "anomaly":
        "Anomaly"

    }


    ml_table.rename(
        columns=rename_columns,
        inplace=True
    )


    st.dataframe(

        ml_table,

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# AI EXPLANATION
# ============================================================

st.subheader(
    "🧠 LifeLens AI Explanation"
)


explanations = generate_explanation(
    filtered_data
)


for explanation in explanations:

    st.write(
        "• " + explanation
    )


# ============================================================
# PERSONALIZED RECOMMENDATION
# ============================================================

st.subheader(
    "💡 Personalized Recommendation"
)


if score >= 80:

    recommendation = (

        "Your productivity is excellent. "
        "Continue your current working pattern "
        "and take regular short breaks."

    )

elif score >= 60:

    recommendation = (

        "Your productivity is good. "
        "Try a 25-minute focused session "
        "to improve consistency."

    )

elif score >= 40:

    recommendation = (

        "Your activity is mixed. "
        "Try Focus Mode for 25 minutes "
        "and reduce distracting applications."

    )

else:

    recommendation = (

        "Your productive activity is low. "
        "Try a 15–25 minute Focus Mode session "
        "with one task at a time."

    )


st.info(
    "🤖 " + recommendation
)


# ============================================================
# RECENT ACTIVITY
# ============================================================

st.subheader(
    "📝 Activity Records"
)


records = filtered_data.copy()


records["Minutes"] = (

    records[
        "duration_seconds"
    ]

    /

    60

).round(1)


records["Time"] = (

    records[
        "timestamp"
    ]

    .dt.strftime(
        "%d %b %Y %H:%M"
    )

)


records = records[

    [
        "Time",
        "app_name",
        "window_title",
        "category",
        "Minutes"
    ]

].sort_values(
    "Time",
    ascending=False
)


records.columns = [

    "Time",
    "Application",
    "Window",
    "Category",
    "Minutes"

]


st.dataframe(

    records.head(100),

    use_container_width=True,

    hide_index=True

)


# ============================================================
# DATA SUMMARY
# ============================================================

st.subheader(
    "📋 Selected Period Summary"
)


summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.write(
        f"**Start Date:** "
        f"{start_date.strftime('%d %B %Y')}"
    )

    st.write(
        f"**End Date:** "
        f"{end_date.strftime('%d %B %Y')}"
    )

    st.write(
        f"**Total Records:** "
        f"{len(filtered_data)}"
    )


with summary_col2:

    st.write(
        f"**Total Tracked:** "
        f"{format_time(total_time)}"
    )

    st.write(
        f"**Productivity Score:** "
        f"{score}%"
    )

    st.write(
        f"**Applications Used:** "
        f"{filtered_data['app_name'].nunique()}"
    )


# ============================================================
# PRIVACY INFORMATION
# ============================================================

with st.expander(
    "🔒 Privacy Information"
):

    st.write(
        """
        LifeLens AI is a local student project.

        ✓ Records application names
        ✓ Records window titles
        ✓ Records activity duration
        ✓ Detects idle periods
        ✓ Stores data locally
        ✓ Uses Machine Learning anomaly detection

        ✗ Does NOT record passwords
        ✗ Does NOT record keyboard content
        ✗ Does NOT take screenshots
        ✗ Does NOT send your activity to a server
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "LifeLens AI • Personalized Digital Behavior "
    "Analytics using Machine Learning"
)