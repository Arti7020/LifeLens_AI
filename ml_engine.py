import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df):

    if df.empty:

        return pd.DataFrame()


    data = df.copy()


    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        errors="coerce"
    )


    data["hour"] = (
        data["timestamp"].dt.hour
    )


    data["productive_seconds"] = np.where(

        data["category"] == "Productive",

        data["duration_seconds"],

        0

    )


    data["distraction_seconds"] = np.where(

        data["category"] == "Distraction",

        data["duration_seconds"],

        0

    )


    data["neutral_seconds"] = np.where(

        data["category"] == "Neutral",

        data["duration_seconds"],

        0

    )


    data["idle_seconds_calculated"] = np.where(

        data["category"] == "Idle",

        data["duration_seconds"],

        data["idle_seconds"]

    )


    hourly = data.groupby(
        "hour"
    ).agg(

        total_duration=(
            "duration_seconds",
            "sum"
        ),

        productive_time=(
            "productive_seconds",
            "sum"
        ),

        distraction_time=(
            "distraction_seconds",
            "sum"
        ),

        neutral_time=(
            "neutral_seconds",
            "sum"
        ),

        idle_time=(
            "idle_seconds_calculated",
            "sum"
        ),

        sessions=(
            "id",
            "count"
        )

    ).reset_index()


    hourly["productivity_ratio"] = (

        hourly["productive_time"]

        /

        hourly["total_duration"]
        .replace(0, 1)

    )


    hourly["distraction_ratio"] = (

        hourly["distraction_time"]

        /

        hourly["total_duration"]
        .replace(0, 1)

    )


    return hourly


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_anomalies(df):

    features = prepare_features(df)


    if features.empty:

        return features


    if len(features) < 5:

        features["anomaly"] = 0

        features["anomaly_score"] = 0.0

        return features


    feature_columns = [

        "total_duration",
        "productive_time",
        "distraction_time",
        "neutral_time",
        "idle_time",
        "sessions",
        "productivity_ratio",
        "distraction_ratio"

    ]


    X = features[
        feature_columns
    ].fillna(0)


    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)


    model = IsolationForest(

        n_estimators=150,

        contamination=0.15,

        random_state=42

    )


    predictions = model.fit_predict(
        X_scaled
    )


    scores = model.decision_function(
        X_scaled
    )


    features["anomaly"] = np.where(

        predictions == -1,

        1,

        0

    )


    minimum = scores.min()

    maximum = scores.max()


    if maximum == minimum:

        normalized_scores = (

            np.ones(
                len(scores)
            ) * 50

        )

    else:

        normalized_scores = (

            (
                scores - minimum
            )

            /

            (
                maximum - minimum
            )

        ) * 100


    features["anomaly_score"] = (
        normalized_scores
    )


    return features


# ============================================================
# PRODUCTIVITY SCORE
# ============================================================

def productivity_score(df):

    if df.empty:

        return 0.0


    productive = df.loc[

        df["category"] == "Productive",

        "duration_seconds"

    ].sum()


    distraction = df.loc[

        df["category"] == "Distraction",

        "duration_seconds"

    ].sum()


    neutral = df.loc[

        df["category"] == "Neutral",

        "duration_seconds"

    ].sum()


    idle = df.loc[

        df["category"] == "Idle",

        "duration_seconds"

    ].sum()


    total = (

        productive
        + distraction
        + neutral
        + idle

    )


    if total <= 0:

        return 0.0


    score = (

        (
            productive * 1.0
        )

        +

        (
            neutral * 0.5
        )

    ) / total * 100


    score -= (
        idle / total
    ) * 20


    score = max(
        0,
        min(
            100,
            score
        )
    )


    return round(
        score,
        1
    )


# ============================================================
# AI EXPLANATION
# ============================================================

def generate_explanation(df):

    if df.empty:

        return [
            "No activity data is available yet."
        ]


    productive = df.loc[

        df["category"] == "Productive",

        "duration_seconds"

    ].sum()


    distraction = df.loc[

        df["category"] == "Distraction",

        "duration_seconds"

    ].sum()


    idle = df.loc[

        df["category"] == "Idle",

        "duration_seconds"

    ].sum()


    neutral = df.loc[

        df["category"] == "Neutral",

        "duration_seconds"

    ].sum()


    total = (

        productive
        + distraction
        + idle
        + neutral

    )


    if total <= 0:

        return [
            "Not enough data for analysis."
        ]


    productive_ratio = (
        productive / total
    )


    distraction_ratio = (
        distraction / total
    )


    idle_ratio = (
        idle / total
    )


    results = []


    if productive_ratio >= 0.60:

        results.append(
            "Your productive activity is strong."
        )

    elif productive_ratio >= 0.35:

        results.append(
            "Your productive activity is moderate."
        )

    else:

        results.append(
            "Your productive activity is currently low."
        )


    if distraction_ratio >= 0.30:

        results.append(
            "Distraction activity is a significant "
            "part of your tracked computer time."
        )

    elif distraction_ratio >= 0.15:

        results.append(
            "A noticeable amount of distraction "
            "activity was detected."
        )

    else:

        results.append(
            "Distraction activity is relatively low."
        )


    if idle_ratio >= 0.25:

        results.append(
            "A large amount of tracked time "
            "appears to be idle."
        )

    elif idle_ratio >= 0.10:

        results.append(
            "Some idle periods were detected."
        )

    else:

        results.append(
            "Your active usage is relatively consistent."
        )


    return results