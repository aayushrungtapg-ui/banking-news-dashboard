import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 REPLACE THIS WITH YOUR REAL NEWSAPI KEY
API_KEY = "aa09c77c5ad841ebaaf1ec387e74f4ab"  # e.g. "eHdpLknQzjxQJSseM0eJjekQM55WsBFZhepT49rf"

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

# How many days of news you want (you asked for 3–4 days)
DAYS_BACK = 3  # change to 4 if you want 4 days

# Topic-specific query templates
TOPIC_QUERIES = {
    "banking": 'banking OR "banking sector" OR "retail banking"',
    "digital": '"digital banking" OR "online banking" OR "mobile banking"',
    "transformation": '"digital transformation" AND banking',
    "fintech": 'fintech OR "financial technology" AND banking',
    "neobanks": 'neobank OR "neo bank" OR "digital-only bank" OR "challenger bank"',
    "payments": '"digital payments" OR "payment rails" OR RTGS OR UPI OR "real-time payments"',
    "ai_in_banking": '"AI in banking" OR "artificial intelligence" AND banking OR "machine learning" AND banking',
}


# ---------------- HELPERS ----------------

def normalize_published(published_str: str | None) -> datetime:
    """Convert NewsAPI date string to datetime object."""
    if not published_str:
        return datetime.utcnow()
    try:
        dt = date_parser.parse(published_str)
        return dt
    except Exception:
        return datetime.utcnow()


def fetch_news(query: str, days_back: int = DAYS_BACK, max_pages: int = 3) -> list[dict]:
    """
    Fetch articles from NewsAPI 'everything' endpoint.

    - query: text query
    - days_back: how many days back to include
    - max_pages: how many pages (100 results/page) to fetch

    NewsAPI free tier: 100 results per page, limited daily quota.
    """
    all_articles: list[dict] = []

    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)

    # NewsAPI accepts ISO8601. Date only is also fine: YYYY-MM-DD
    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    page = 1
    page_size = 100  # max allowed

    while page <= max_pages:
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "from": from_str,
            "to": to_str,
            "pageSize": page_size,
            "page": page,
            "apiKey": API_KEY,
        }

        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=20)

        if resp.status_code == 401:
            st.error("NewsAPI returned 401 (unauthorized). Check your API key.")
            break

        if resp.status_code != 200:
            st.error(
                f"NewsAPI error (status {resp.status_code}) on page {page}: "
                f"{resp.text[:200]}"
            )
            break

        data = resp.json()

        if data.get("status") != "ok":
            st.error(f"NewsAPI returned error JSON: {data}")
            break

        articles = data.get("articles", [])
        if not articles:
            break

        for article in articles:
            title = article.get("title") or "No Title"
            url = article.get("url")
            if not url:
                continue

            description = article.get("description") or ""
            content = article.get("content") or ""
            text = description if description else content

            # Short snippet (around 2 lines)
            max_chars = 260
            if text and len(text) > max_chars:
                snippet = text[:max_chars].rsplit(" ", 1)[0] + "..."
            else:
                snippet = text

            source_name = (article.get("source") or {}).get("name") or "Unknown"
            published_raw = article.get("publishedAt")
            published_at = normalize_published(published_raw)

            all_articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": snippet,
                    "source": source_name,
                    "published_at": published_at,
                    "image": article.get("urlToImage"),
                }
            )

        # If fewer than page_size results returned, no more pages
        if len(articles) < page_size:
            break

        page += 1

    # Sort newest first
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News (NewsAPI)", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption(
    f"Live news from NewsAPI.org — last {DAYS_BACK} day(s), "
    "sorted by recency with topic filters and search."
)

# Search bar (overrides topics if used)
search_query = st.text_input(
    "🔍 Search any keyword (e.g., RBI, UPI, JP Morgan, fraud, blockchain):"
)

# Topic filter dropdown
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

# Timestamp + manual refresh
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------- FETCH DATA ----------------

with st.spinner("Fetching latest news from NewsAPI…"):
    if search_query.strip():
        # User manually searched → ignore topic filter
        query = search_query.strip()
        articles = fetch_news(query)
    else:
        # No free-text search → use topics
        if topic_map[topic_choice] is None:
            # All topics: single combined OR query (saves API calls)
            combined_query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
            articles = fetch_news(combined_query)
        else:
            topic_key = topic_map[topic_choice]
            query = TOPIC_QUERIES[topic_key]
            articles = fetch_news(query)

# ---------------- DISPLAY ----------------

if not articles:
    st.warning(
        "No news found. This could be because:\n"
        "• The query is too narrow\n"
        "• Your daily NewsAPI quota is exhausted\n"
        "• Or there were no matching articles in the last days.\n\n"
        "Try another keyword, 'All topics', or increase DAYS_BACK in the code."
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
