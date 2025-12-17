import streamlit as st
import requests
from datetime import datetime, timezone
from dateutil import parser as date_parser

# ---------- CONFIG ----------

# 🔴 IMPORTANT: paste your NewsAPI key here BEFORE deploying
API_KEY = "aa09c77c5ad841ebaaf1ec387e74f4ab"

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

TOPIC_QUERIES = {
    "banking": "banking sector",
    "digital": "digital banking OR online banking",
    "transformation": "banking digital transformation",
    "fintech": "fintech AND banking",
    "neobanks": "neobank OR neobanks OR digital-only bank",
    "payments": "digital payments AND banking",
    "ai_in_banking": "artificial intelligence AND banking",
}


def normalize_published(published_str: str | None) -> datetime:
    if not published_str:
        return datetime.now(timezone.utc)
    try:
        dt = date_parser.parse(published_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def fetch_topic(topic_key: str) -> list[dict]:
    """Fetch articles for a single topic from NewsAPI."""
    if not API_KEY or API_KEY == "PASTE_YOUR_NEWSAPI_KEY_HERE":
        st.error("Please set your NewsAPI API_KEY at the top of the file before deploying.")
        return []

    query = TOPIC_QUERIES[topic_key]

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 40,
        "apiKey": API_KEY,
    }

    resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=20)

    if resp.status_code != 200:
        st.error(
            f"NewsAPI request failed for topic '{topic_key}'. "
            f"Status code: {resp.status_code}, Response: {resp.text[:200]}"
        )
        return []

    data = resp.json()
    if data.get("status") != "ok":
        st.error(f"NewsAPI error for topic '{topic_key}': {data}")
        return []

    articles: list[dict] = []
    for article in data.get("articles", []):
        title = article.get("title") or "No Title"
        url = article.get("url")
        if not url:
            continue

        description = article.get("description") or ""
        content = article.get("content") or ""
        text = description if description else content

        max_chars = 260
        if text and len(text) > max_chars:
            snippet = text[:max_chars].rsplit(" ", 1)[0] + "..."
        else:
            snippet = text

        source_name = (article.get("source") or {}).get("name") or "NewsAPI"

        published_raw = article.get("publishedAt")
        published_at = normalize_published(published_raw)

        articles.append(
            {
                "title": title,
                "url": url,
                "summary": snippet,
                "source": source_name,
                "published_at": published_at,
                "topic": topic_key,
                "image": article.get("urlToImage"),
            }
        )

    articles.sort(key=lambda x: x["published_at"], reverse=True)
    return articles


# ---------- STREAMLIT UI ----------

st.set_page_config(page_title="Banking & Fintech News", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption("Live results pulled from NewsAPI, filtered for banking & digital themes.")

topic_map = {
    "All topics": None,
    "Banking": "banking",
    "Digital banking": "digital",
    "Digital transformation": "transformation",
    "Fintech": "fintech",
    "Neobanks": "neobanks",
    "Payments": "payments",
    "AI in banking": "ai_in_banking",
}

topic_choice = st.selectbox("Filter by topic", list(topic_map.keys()))

col_left, col_right = st.columns([3, 1])
with col_left:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_right:
    if st.button("🔄 Refresh now"):
        st.rerun()

with st.spinner("Fetching latest news..."):
    if topic_map[topic_choice] is None:
        all_articles: list[dict] = []
        for key in TOPIC_QUERIES.keys():
            all_articles.extend(fetch_topic(key))
        all_articles.sort(key=lambda x: x["published_at"], reverse=True)
        articles = all_articles
    else:
        topic_key = topic_map[topic_choice]
        articles = fetch_topic(topic_key)

if not articles:
    st.info(
        "No articles found for this topic.\n\n"
        "• Check that your NewsAPI key is set correctly\n"
        "• Check that you haven't exceeded the free quota"
    )
else:
    for a in articles:
        with st.container():
            cols = st.columns([1, 3])

            with cols[0]:
                if a.get("image"):
                    st.image(a["image"], use_column_width=True)
                else:
                    st.empty()

            with cols[1]:
                st.markdown(f"#### [{a['title']}]({a['url']})")
                meta = (
                    f"Source: {a['source']} · "
                    f"Published: {a['published_at'].strftime('%Y-%m-%d %H:%M')} · "
                    f"Topic: {a['topic']}"
                )
                st.caption(meta)
                if a.get("summary"):
                    st.write(a["summary"])

        st.markdown("---")
