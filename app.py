import time

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    init_db,
    get_activity,
    get_today_activity,
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
# HEADER
# ============================================================

st.markdown(
    """
    <h1 style="
        font-size: 45px;
        margin-bottom: 0px;
    ">
        🧠 LifeLens AI
    </h1>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <p style="
        font-size: 19px;
        color: gray;
    ">
        Personalized Digital Behavior &
        Productivity Analyzer
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Control Panel"
    )


    st.info(
        """
        LifeLens AI monitors application-level
        activity.

        It does NOT record:
        • Passwords
        • Keyboard content
        • Screenshots
        """
    )


    if st.button(
        "🔄 Refresh Dashboard",
        use_container_width=True
    ):

        st.rerun()


    st.divider()


    # ========================================================
    # FOCUS MODE
    # ========================================================

    st.subheader(
        "🎯 Focus Mode"
    )


    focus_minutes = st.number_input(

        "Focus duration",

        min_value=1,

        max_value=180,

        value=25

    )


    if st.button(
        "▶ Start Focus",
        use_container_width=True
    ):

        st.session_state[
            "focus_start"
        ] = time.time()


        st.session_state[
            "focus_duration"
        ] = focus_minutes * 60


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

    st.subheader(
        "🗑️ Data"
    )


    if st.button(
        "Delete All Activity",
        use_container_width=True
    ):

        delete_all_activity()

        st.success(
            "All activity deleted."
        )

        time.sleep(0.5)

        st.rerun()


# ============================================================
# FOCUS TIMER
# ============================================================

if "focus_start" in st.session_state:

    remaining = (

        st.session_state[
            "focus_duration"
        ]

        -

        (
            time.time()
            -
            st.session_state[
                "focus_start"
            ]
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
# LOAD DATABASE
# ============================================================

all_data = get_activity()

today_data = get_today_activity()


# ============================================================
# NO DATA
# ============================================================

if all_data.empty:

    st.info(
        "👋 LifeLens has not collected "
        "activity data yet."
    )


    st.markdown(
        """
        ### What to do

        1. Keep the tracker running.
        2. Use your computer normally.
        3. Switch between applications.
        4. Come back after a few minutes.
        5. Click **Refresh Dashboard**.

        The ML system needs activity data before
        it can detect unusual behavior.
        """
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
            f"{hours}h "
            f"{minutes}m"
        )


    return (
        f"{minutes}m"
    )


# ============================================================
# CALCULATE TODAY'S DATA
# ============================================================

productive = today_data.loc[

    today_data["category"]
    == "Productive",

    "duration_seconds"

].sum()


distraction = today_data.loc[

    today_data["category"]
    == "Distraction",

    "duration_seconds"

].sum()


idle = today_data.loc[

    today_data["category"]
    == "Idle",

    "duration_seconds"

].sum()


score = productivity_score(
    today_data
)


# ============================================================
# OVERVIEW
# ============================================================

st.subheader(
    "📊 Today's Overview"
)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Productivity Score",
    f"{score}%"
)


col2.metric(
    "Productive Time",
    format_time(productive)
)


col3.metric(
    "Distraction",
    format_time(distraction)
)


col4.metric(
    "Idle",
    format_time(idle)
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
        "Try Focus Mode."
    )

else:

    st.error(
        "🚨 Your productive activity is currently low."
    )


# ============================================================
# CHARTS
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

        today_data

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
# APPLICATION CHART
# ============================================================

with col2:

    application_data = (

        today_data

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


    application_data["minutes"] = (

        application_data[
            "duration_seconds"
        ]

        /

        60

    )


    fig = px.bar(

        application_data,

        x="minutes",

        y="app_name",

        orientation="h",

        title="Top Applications"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# HOURLY ACTIVITY
# ============================================================

st.subheader(
    "🕐 Hourly Activity"
)


hourly = today_data.copy()


hourly["timestamp"] = pd.to_datetime(
    hourly["timestamp"]
)


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

    title="Activity by Hour"

)


st.plotly_chart(

    fig,

    use_container_width=True

)


# ============================================================
# MACHINE LEARNING
# ============================================================

st.subheader(
    "🤖 Machine Learning Analysis"
)


ml_data = detect_anomalies(
    all_data
)


if len(ml_data) < 5:

    st.warning(

        f"ML is still learning your behavior. "
        f"Currently {len(ml_data)} hourly records "
        f"are available. Collect more data."

    )

else:

    anomaly_count = int(
        ml_data["anomaly"].sum()
    )


    if anomaly_count > 0:

        st.error(

            f"⚠️ {anomaly_count} unusual "
            "behavior period(s) detected."

        )

    else:

        st.success(

            "✅ No strong behavioral anomalies detected."

        )


# ============================================================
# ML DATA TABLE
# ============================================================

if not ml_data.empty:

    table = ml_data.copy()


    table["hour"] = (

        table["hour"].astype(str)

        + ":00"

    )


    for column in [

        "total_duration",
        "productive_time",
        "distraction_time",
        "idle_time"

    ]:

        table[column] = (

            table[column] / 60

        ).round(1)


    table = table[

        [

            "hour",
            "total_duration",
            "productive_time",
            "distraction_time",
            "idle_time",
            "sessions",
            "anomaly"

        ]

    ]


    table.columns = [

        "Hour",
        "Total Min",
        "Productive Min",
        "Distraction Min",
        "Idle Min",
        "Sessions",
        "Anomaly"

    ]


    st.dataframe(

        table,

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
    today_data
)


for explanation in explanations:

    st.write(
        "• " + explanation
    )


# ============================================================
# RECOMMENDATION
# ============================================================

st.subheader(
    "💡 Personalized Recommendation"
)


if score >= 80:

    recommendation = (

        "Your productivity is excellent. "
        "Continue your current work pattern "
        "and take regular short breaks."

    )

elif score >= 60:

    recommendation = (

        "Try a 25-minute focused work session "
        "with minimal application switching."

    )

elif score >= 40:

    recommendation = (

        "Your activity is mixed. "
        "Try Focus Mode for 25 minutes "
        "and reduce distracting applications."

    )

else:

    recommendation = (

        "Start a 15–25 minute Focus Mode session "
        "and concentrate on one task."

    )


st.info(
    "🤖 " + recommendation
)


# ============================================================
# RECENT ACTIVITY
# ============================================================

st.subheader(
    "📝 Recent Activity"
)


recent = today_data.copy()


recent["Minutes"] = (

    recent[
        "duration_seconds"
    ]

    /

    60

).round(1)


recent = recent[

    [
        "timestamp",
        "app_name",
        "category",
        "Minutes"
    ]

].tail(15)


recent.columns = [

    "Time",
    "Application",
    "Category",
    "Minutes"

]


st.dataframe(

    recent,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# PRIVACY
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
        ✓ Uses local SQLite database
        ✓ Uses Machine Learning anomaly detection

        ✗ Does NOT record passwords
        ✗ Does NOT record keyboard content
        ✗ Does NOT take screenshots
        ✗ Does NOT send data to a server
        """
    )


st.divider()


st.caption(
    "LifeLens AI • Personalized Digital "
    "Behavior Analytics using Machine Learning"
)