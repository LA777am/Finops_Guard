def df_to_json(df):
    if df is None or df.empty:
        return []
    return df.to_dict(orient="records")


def get_anomalies(service=None, provider=None):
    from backend.core.db import get_db
    db = get_db()
    df = db.fetch_anomalies(service=service, provider=provider, limit=50000)
    return df_to_json(df)


def get_forecasts(service=None):
    from backend.core.db import get_db
    db = get_db()
    df = db.fetch_forecasts(service=service, limit=50000)
    return df_to_json(df)


def get_metrics():
    from backend.core.db import get_db
    db = get_db()
    df = db.fetch_latest_metrics()
    return df_to_json(df)