import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 REPLACE WITH YOUR TheNewsAPI.com KEY
API_KEY = "eHdpLknQzjxQJSseM0eJjekQM55WsBFZhepT49rf"

ENDPOINT = "https://api.thenewsapi.com/v1/news/all"

# Number of days you want
DAYS_BACK = 3   # change to 7, 30, etc. if needed

TOPIC_QUERIES = {
    "banking": "banking OR banks OR banking sector",
    "digital": "digital banking OR online banking OR mobile banking",
    "transformation": "digital transformation banking",
    "fintech": "fintech OR financial technology OR startup finance",
    "neobanks": "neobank OR challenger bank OR digital-only bank",
    "payments": "digital payments OR UPI OR RTGS OR payment rails",
    "ai_in_banking": "AI banking OR artificial intelligence banking OR machine learning banking",
}


# ---------------- HELPERS ----------------

def parse_date(date_str):
    try:
        return date_parser.parse(date_str)
    except:
        return datetime.utcnow()


def fetch_thenewsapi(query, pages=3):
    """
    Fetches news results from TheNewsAPI.com
    - Supports pagination
    - Supports custom queries
    """
    articles = []

    for page in range(1, pages + 1):
        params = {
            "api_token": API_KEY,
            "search": query,
            "language": "en",
            "sort": "published_at",
            "published_after": (datetime.utcnow() - timedelta(days=DAYS_BACK)).isoformat(),
            "page": page,
            "limit": 50,  # max allowed per page
        }

        resp = requests.get(ENDPOINT, params=params)

        if resp.status_code != 200:
            st.error(f"TheNewsAPI error: {resp.status_code} → {resp.text[:200]}")
            break

        data = resp.json()
        page_articles = data.get("data", [])
        if not page_articles:
            break

        for a in page_articles:
            articles.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "summary": a.get("description"),
                "source": a.get("source"),
                "published_at": parse_date(a.get("published_at")),
                "image": a.get("image_url"),
            })

    articles.sort(key=lambda x: x["published_at"], reverse=True)
    return articles


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption(f"Live news from TheNewsAPI.com — last {DAYS_BACK} days.")

# Search bar
search_input = st.text_input("🔍 Search any keyword (e.g., UPI, RBI, fintech funding, JP Morgan):")

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

topic_choice = st.selectbox("Filter by Topic", list(topic_map.keys()))

# Timestamp & refresh
col1, col2 = st.columns([3,1])
with col1:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()


# ---------------- FETCH DATA ----------------
with st.spinner("Fetching the latest news…"):
    if search_input.strip():
        # Use custom search
        articles = fetch_thenewsapi(search_input.strip(), pages=3)
    else:
        # Use topic filter or "All topics"
        if topic_map[topic_choice] is None:
            combined_query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
            articles = fetch_thenewsapi(combined_query, pages=4)
        else:
            topic_key = topic_map[topic_choice]
            query = TOPIC_QUERIES[topic_key]
            articles = fetch_thenewsapi(query, pages=3)


# ---------------- DISPLAY ----------------

if not articles:
    st.warning("No news found. Try a different keyword or topic.")
else:
    for a in articles:
        with st.container():
            cols = st.columns([1, 3])

            # Image
            with cols[0]:
                if a["image"]:
                    st.image(a["image"], use_column_width=True)

            # Text
            with cols[1]:
                st.markdown(f"### [{a['title']}]({a['url']})")
                st.caption(
                    f"{a['source']} • {a['published_at'].strftime('%Y-%m-%d %H:%M')}"
                )
                st.write(a["summary"] or "")

        st.markdown("---")
