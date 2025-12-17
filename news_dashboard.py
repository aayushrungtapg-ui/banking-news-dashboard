import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 REPLACE THIS WITH YOUR REAL NEWSDATA.IO API KEY
API_KEY = "pub_79ae5e4589834c119ff26d5c5506cb62"

ENDPOINT = "https://newsdata.io/api/1/news"

# How many days of news to show (you can set to 3 or 4 as you asked)
DAYS_BACK = 3

TOPIC_QUERIES = {
    "banking": "banking OR banks OR retail banking OR corporate banking",
    "digital": '"digital banking" OR "online banking" OR "mobile banking"',
    "transformation": '"digital transformation" AND banking',
    "fintech": "fintech OR financial technology OR neobank",
    "neobanks": "neobank OR challenger bank OR digital-only bank",
    "payments": '"digital payments" OR UPI OR RTGS OR payments',
    "ai_in_banking": '"AI in banking" OR "artificial intelligence" AND banking',
}


# ---------------- HELPERS ----------------

def parse_date(date_str):
    if not date_str:
        return datetime.utcnow()
    try:
        return date_parser.parse(date_str)
    except Exception:
        return datetime.utcnow()


def fetch_newsdata(query: str, days_back: int = DAYS_BACK, max_pages: int = 3):
    """
    Fetch articles from NewsData.io.

    - query: search string
    - days_back: how many days back to include
    - max_pages: how many pages to pull (NewsData paginates)
    """
    all_articles = []

    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)

    # NewsData expects YYYY-MM-DD format
    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    page = 1
    next_page = None

    while page <= max_pages:
        params = {
            "apikey": API_KEY,
            "q": query,
            "language": "en",
            "from_date": from_str,
            "to_date": to_str,
            "page": next_page,  # NewsData uses "page" cursor for pagination
        }

        resp = requests.get(ENDPOINT, params=params, timeout=20)

        if resp.status_code != 200:
            st.error(
                f"NewsData.io error (HTTP {resp.status_code}): "
                f"{resp.text[:200]}"
            )
            break

        data = resp.json()

        # If NewsData signals an error in JSON
        if data.get("status") != "success":
            st.error(f"NewsData.io returned error: {data}")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            title = item.get("title")
            url = item.get("link")
            if not title or not url:
                continue

            # Some fields may be missing
            description = item.get("description") or item.get("content") or ""
            source_name = (item.get("source") or {}).get("name") or item.get("source_id") or "Unknown"
            image_url = item.get("image_url") or item.get("image")  # depending on response
            pub_date = parse_date(item.get("pubDate"))

            # Short snippet
            snippet = description.strip()
            max_chars = 260
            if snippet and len(snippet) > max_chars:
                snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "..."

            all_articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": snippet,
                    "source": source_name,
                    "published_at": pub_date,
                    "image": image_url,
                }
            )

        # Handle pagination: NewsData uses "nextPage" cursor
        next_page = data.get("nextPage")
        if not next_page:
            break

        page += 1

    # Sort by recency (newest first)
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News (NewsData.io)", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption(
    f"Live news from the last {DAYS_BACK} days via NewsData.io "
    "(sorted by recency, with topics & search)."
)

# Search input
search_query = st.text_input(
    "🔍 Search any keyword (e.g., RBI, UPI, JP Morgan, fraud, blockchain):"
)

# Topic dropdown
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

# Refresh + timestamp
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------- FETCH DATA ----------------

with st.spinner("Fetching latest news from NewsData.io…"):
    if search_query.strip():
        # User keyword search overrides topic filter
        query = search_query.strip()
        articles = fetch_newsdata(query)
    else:
        if topic_map[topic_choice] is None:
            # All topics combined — single big OR query to save quota
            combined_query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
            articles = fetch_newsdata(combined_query)
        else:
            topic_key = topic_map[topic_choice]
            query = TOPIC_QUERIES[topic_key]
            articles = fetch_newsdata(query)

# ---------------- DISPLAY ----------------

if not articles:
    st.warning(
        "No news found for this combination. Try changing topic, search keyword, or "
        "increasing DAYS_BACK in the code."
    )
else:
    for a in articles:
        with st.container():
            cols = st.columns([1, 3])

            # Image column
            with cols[0]:
                if a["image"]:
                    try:
                        st.image(a["image"], use_column_width=True)
                    except Exception:
                        st.empty()
                else:
                    st.empty()

            # Text column
            with cols[1]:
                st.markdown(f"### [{a['title']}]({a['url']})")
                st.caption(
                    f"{a['source']} • {a['published_at'].strftime('%Y-%m-%d %H:%M')}"
                )
                if a["summary"]:
                    st.write(a["summary"])

        st.markdown("---")
