import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 REPLACE THESE WITH YOUR REAL VALUES:
API_KEY = "YOUR_BING_API_KEY_HERE"
ENDPOINT = "https://api.bing.microsoft.com/v7.0/news/search"

# How many days of news you want:
DAYS_BACK = 3  # <-- change to 7 or 30 if needed

FROM_DATE = (datetime.utcnow() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")

TOPIC_QUERIES = {
    "banking": "banking OR banks OR financial sector",
    "digital": "digital banking OR online banking OR mobile banking",
    "transformation": "digital transformation banking",
    "fintech": "fintech OR financial technology",
    "neobanks": "neobank OR challenger bank",
    "payments": "digital payments OR payment systems",
    "ai_in_banking": "AI banking OR artificial intelligence banking",
}


# ---------------- HELPERS ----------------

def fetch_bing_news(query):
    """Fetch news articles from Bing News Search."""
    headers = {
        "Ocp-Apim-Subscription-Key": API_KEY
    }

    params = {
        "q": query,
        "count": 50,
        "sortBy": "Date",
        "freshness": f"{DAYS_BACK}day",
        "textFormat": "Raw",
        "safeSearch": "Off",
    }

    resp = requests.get(ENDPOINT, headers=headers, params=params)
    
    if resp.status_code != 200:
        st.error(f"Bing News error: {resp.status_code} → {resp.text[:200]}")
        return []

    data = resp.json()
    articles = data.get("value", [])

    parsed = []
    for a in articles:
        parsed.append({
            "title": a.get("name"),
            "url": a.get("url"),
            "summary": a.get("description"),
            "source": (a.get("provider") or [{}])[0].get("name", "Unknown"),
            "published_at": date_parser.parse(a["datePublished"]) if "datePublished" in a else datetime.utcnow(),
            "image": a.get("image", {}).get("thumbnail", {}).get("contentUrl"),
        })

    parsed.sort(key=lambda x: x["published_at"], reverse=True)
    return parsed


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption(f"Live news from Bing News Search — last {DAYS_BACK} days.")

# Search bar
search_query = st.text_input("🔍 Search any keyword (e.g., RBI, UPI, Fintech funding):")

# Topic filter
topic_map = {
    "All topics": None,
    "Banking": "banking",
    "Digital Banking": "digital",
    "Digital Transformation": "transformation",
    "Fintech": "fintech",
    "Neobanks": "neobanks",
    "Payments": "payments",
    "AI in Banking": "ai_in_banking",
}

topic_choice = st.selectbox("Filter by topic", list(topic_map.keys()))

# Refresh & timestamp
col1, col2 = st.columns([3,1])
with col1:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()


# ---------------- FETCH DATA ----------------
with st.spinner("Fetching latest news…"):
    articles = []

    if search_query.strip():
        articles = fetch_bing_news(search_query)
    else:
        if topic_map[topic_choice] is None:
            for key in TOPIC_QUERIES:
                articles.extend(fetch_bing_news(TOPIC_QUERIES[key]))
        else:
            topic_key = topic_map[topic_choice]
            articles = fetch_bing_news(TOPIC_QUERIES[topic_key])

    articles.sort(key=lambda x: x["published_at"], reverse=True)


# ---------------- SHOW ARTICLES ----------------

if not articles:
    st.warning("No news found. Try a different topic or search keyword.")
else:
    for a in articles:
        with st.container():
            cols = st.columns([1, 3])

            with cols[0]:
                if a["image"]:
                    st.image(a["image"], use_column_width=True)

            with cols[1]:
                st.markdown(f"### [{a['title']}]({a['url']})")
                st.caption(f"{a['source']} • {a['published_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(a["summary"] or "")

        st.markdown("---")
