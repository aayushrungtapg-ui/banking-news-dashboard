import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 IMPORTANT: paste your GNEWS API key here
API_KEY = "4991b94d92e7165a2b2fb0d663fb2a7b"

GNEWS_ENDPOINT = "https://gnews.io/api/v4/search"

# Last 6 months range
TO_DATE = datetime.utcnow()
FROM_DATE = TO_DATE - timedelta(days=180)

TOPIC_QUERIES = {
    "banking": "banking OR banks OR finance sector",
    "digital": "digital banking OR online banking OR mobile banking",
    "transformation": "digital transformation banking",
    "fintech": "fintech OR financial technology OR startup banking",
    "neobanks": "neobank OR challenger bank OR digital-only bank",
    "payments": "payments OR digital payments OR UPI OR RTGS",
    "ai_in_banking": "AI banking OR artificial intelligence banking OR machine learning banking",
}


# ---------------- HELPERS ----------------

def parse_date(date_str):
    try:
        return date_parser.parse(date_str)
    except:
        return datetime.utcnow()


def fetch_gnews(query):
    """Fetches fresh news results from GNews API within last 6 months."""
    params = {
        "q": query,
        "from": FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": TO_DATE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sortby": "publishedAt",
        "lang": "en",
        "max": 100,  
        "apikey": API_KEY,
    }

    resp = requests.get(GNEWS_ENDPOINT, params=params)

    if resp.status_code != 200:
        st.error(f"GNews error: {resp.status_code}, response: {resp.text[:200]}")
        return []

    data = resp.json()
    articles = data.get("articles", [])

    parsed = []
    for a in articles:
        parsed.append({
            "title": a.get("title"),
            "url": a.get("url"),
            "summary": a.get("description"),
            "source": a.get("source", {}).get("name", "Unknown"),
            "published_at": parse_date(a.get("publishedAt")),
            "image": a.get("image"),
        })

    # Sort by newest first
    parsed.sort(key=lambda x: x["published_at"], reverse=True)
    return parsed


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption("Live, real-time news from the last 6 months — sourced from GNews.")

# --- Search Bar ---
search_query = st.text_input("🔍 Search for any keyword (e.g., RBI, UPI, Blockchain, JP Morgan):")

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

topic_choice = st.selectbox("Filter by Topic", list(topic_map.keys()))

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

if st.button("🔄 Refresh"):
    st.rerun()

# ---------------- DATA FETCH ----------------

with st.spinner("Fetching latest news…"):
    articles = []

    if search_query.strip():
        articles = fetch_gnews(search_query.strip())
    else:
        if topic_map[topic_choice] is None:
            # Fetch all topics combined
            for key in TOPIC_QUERIES:
                articles.extend(fetch_gnews(TOPIC_QUERIES[key]))
        else:
            topic_key = topic_map[topic_choice]
            articles = fetch_gnews(TOPIC_QUERIES[topic_key])

    articles.sort(key=lambda x: x["published_at"], reverse=True)


# ---------------- DISPLAY ----------------

if not articles:
    st.warning("No news found. Try changing topic or search term.")
else:
    for a in articles:
        with st.container():
            cols = st.columns([1, 3])

            with cols[0]:
                if a["image"]:
                    st.image(a["image"], use_column_width=True)
                else:
                    st.empty()

            with cols[1]:
                st.markdown(f"### [{a['title']}]({a['url']})")
                st.caption(
                    f"{a['source']} • {a['published_at'].strftime('%Y-%m-%d %H:%M')}"
                )
                st.write(a["summary"] or "")
        st.markdown("---")
