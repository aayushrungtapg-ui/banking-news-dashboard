import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# ---------------- CONFIG ----------------

# 🔴 REPLACE WITH YOUR NEWSDATA.IO API KEY
API_KEY = "pub_79ae5e4589834c119ff26d5c5506cb62"

ARCHIVE_ENDPOINT = "https://newsdata.io/api/1/archive"

# Number of days you want (3–4 as you said)
DAYS_BACK = 4

TOPIC_QUERIES = {
    "banking": "banking OR banks OR retail banking",
    "digital": '"digital banking" OR "online banking" OR "mobile banking"',
    "transformation": '"digital transformation" AND banking',
    "fintech": "fintech OR financial technology",
    "neobanks": "neobank OR challenger bank",
    "payments": '"digital payments" OR UPI OR RTGS',
    "ai_in_banking": '"AI in banking" OR "artificial intelligence" AND banking',
}


# ---------------- HELPERS ----------------

def parse_date(date_str):
    try:
        return date_parser.parse(date_str)
    except:
        return datetime.utcnow()


def fetch_newsdata_archive(query, days_back=DAYS_BACK, max_pages=5):
    """Fetches articles using the correct /archive endpoint."""
    all_articles = []

    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)

    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    next_page = None
    pages_fetched = 0

    while pages_fetched < max_pages:
        params = {
            "apikey": API_KEY,
            "q": query,
            "language": "en",
            "from_date": from_str,
            "to_date": to_str,
            "page": next_page,
        }

        resp = requests.get(ARCHIVE_ENDPOINT, params=params, timeout=20)

        if resp.status_code != 200:
            st.error(f"NewsData.io ERROR {resp.status_code}: {resp.text[:300]}")
            break

        data = resp.json()

        if data.get("status") != "success":
            st.error(f"NewsData.io Error: {data}")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            title = item.get("title")
            url = item.get("link")
            if not title or not url:
                continue

            summary = item.get("description") or item.get("content") or ""
            max_chars = 260
            if len(summary) > max_chars:
                summary = summary[:max_chars].rsplit(" ", 1)[0] + "..."

            source = (item.get("source") or {}).get("name") or "Unknown"
            pub_date = parse_date(item.get("pubDate"))
            image_url = item.get("image_url")

            all_articles.append({
                "title": title,
                "url": url,
                "summary": summary,
                "source": source,
                "published_at": pub_date,
                "image": image_url,
            })

        next_page = data.get("nextPage")
        if not next_page:
            break

        pages_fetched += 1

    # Sort by latest first
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles


# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Banking & Fintech News", layout="wide")

st.title("📰 Banking, Fintech & Digital Transformation News")
st.caption(f"Live news (past {DAYS_BACK} days) from NewsData.io archive endpoint.")

search_query = st.text_input("🔍 Search any keyword (RBI, UPI, fintech funding...):")

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

col1, col2 = st.columns([3,1])
with col1:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------- FETCH DATA ----------------

with st.spinner("Fetching fresh news from NewsData.io…"):
    if search_query.strip():
        query = search_query.strip()
        articles = fetch_newsdata_archive(query)
    else:
        if topic_map[topic_choice] is None:
            combined_query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
            articles = fetch_newsdata_archive(combined_query)
        else:
            topic_key = topic_map[topic_choice]
            query = TOPIC_QUERIES[topic_key]
            articles = fetch_newsdata_archive(query)


# ---------------- DISPLAY ----------------

if not articles:
    st.warning("No news found. Try another keyword or topic.")
else:
    for a in articles:
        with st.container():
            cols = st.columns([1,3])

            with cols[0]:
                if a["image"]:
                    st.image(a["image"], use_column_width=True)

            with cols[1]:
                st.markdown(f"### [{a['title']}]({a['url']})")
                st.caption(f"{a['source']} • {a['published_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(a["summary"])

        st.markdown("---")
