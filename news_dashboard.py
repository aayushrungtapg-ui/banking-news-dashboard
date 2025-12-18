import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import math

# ---------------- CONFIG ----------------
API_KEY = "aa09c77c5ad841ebaaf1ec387e74f4ab"  
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

DAYS_BACK = 3
MAX_API_PAGES = 5
API_PAGE_SIZE = 50
UI_PAGE_SIZE = 50
MAX_UI_PAGES = 5

TOPIC_QUERIES = {
    "Banking": 'banking OR "banking sector" OR "retail banking"',
    "Digital Banking": '"digital banking" OR "online banking" OR "mobile banking"',
    "Digital Transformation": '"digital transformation" AND banking',
    "Fintech": 'fintech OR "financial technology" AND banking',
    "Neobanks": 'neobank OR "neo bank" OR "digital-only bank" OR "challenger bank"',
    "Payments": '"digital payments" OR "payment rails" OR RTGS OR UPI OR "real-time payments"',
    "AI in Banking": '"AI in banking" OR "artificial intelligence" AND banking OR "machine learning" AND banking',
}

# ---------------- CSS (IMPROVED UI) ----------------
CUSTOM_CSS = """
<style>

body, .stApp { background-color: #f5f6fa; }

/* Remove margin */
.main .block-container { padding-top: 1.2rem; }

/* Spacing between columns */
.css-1fcdlhc, .css-ocqkz7, [data-testid="column"] {
    padding-right: 12px !important;
    padding-left: 12px !important;
}

/* News cards - More spacing & larger size */
.news-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 0;
    overflow: hidden;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-bottom: 28px;
}

/* Larger images */
.news-card img {
    width: 100%;
    height: 200px; 
    object-fit: cover;
    border-bottom: 1px solid #eee;
}

/* Inside spacing */
.news-card-content {
    padding: 1rem 1.1rem 1.2rem 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
}

/* Title styling */
.news-card-title {
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.35rem;
    margin: 0;
}
.news-card-title a {
    color: #111827;
    text-decoration: none;
}
.news-card-title a:hover {
    text-decoration: underline;
}

/* Source + time styling */
.news-card-meta {
    font-size: 0.78rem;
    color: #6b7280;
}

/* Snippet text */
.news-card-snippet {
    font-size: 0.85rem;
    color: #4b5563;
}

/* Search bar rounded */
.search-bar input {
    border-radius: 999px !important;
}

/* Section heading */
.section-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
}
</style>
"""

st.set_page_config(page_title="Banking News", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def normalize_published(timestamp: str):
    try:
        return date_parser.parse(timestamp)
    except:
        return datetime.utcnow()

def fetch_news(query, days_back=DAYS_BACK, max_pages=MAX_API_PAGES, page_size=API_PAGE_SIZE):
    all_articles = []
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)

    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    page = 1

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
        resp = requests.get(NEWSAPI_ENDPOINT, params=params)

        if resp.status_code != 200:
            st.error(f"NewsAPI error {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json()
        if data.get("status") != "ok":
            break

        articles = data.get("articles", [])
        if not articles:
            break

        for a in articles:
            published = normalize_published(a.get("publishedAt"))
            snippet = a.get("description") or a.get("content") or ""
            if len(snippet) > 230:
                snippet = snippet[:230] + "..."

            all_articles.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "image": a.get("urlToImage"),
                "summary": snippet,
                "source": (a.get("source") or {}).get("name", "Unknown"),
                "published_at": published,
            })

        if len(articles) < page_size:
            break

        page += 1

    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles

# ---------------- UI LAYOUT ----------------
left, right = st.columns([1, 4])

# LEFT PANEL
with left:
    st.markdown("### 📡 Feeds")
    feed_list = ["Newsfeed (All)"] + list(TOPIC_QUERIES.keys())
    feed_choice = st.radio("Select Feed", feed_list)

    st.markdown("---")
    st.caption("Use search on the right to override feed.")

# RIGHT PANEL
with right:
    st.markdown('<div class="section-label">Newsfeed</div>', unsafe_allow_html=True)

    search_query = st.text_input(
        "Search",
        placeholder="Search in articles...",
        label_visibility="collapsed"
    )

    if search_query.strip():
        query = search_query.strip()
    else:
        if feed_choice == "Newsfeed (All)":
            query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
        else:
            query = TOPIC_QUERIES[feed_choice]

    # FETCH NEWS
    with st.spinner("Fetching latest news..."):
        articles = fetch_news(query)

    # PAGINATION STATE
    if "page_num" not in st.session_state:
        st.session_state.page_num = 1

    TOTAL = len(articles)
    total_pages = min(math.ceil(TOTAL / UI_PAGE_SIZE), MAX_UI_PAGES)

    start = (st.session_state.page_num - 1) * UI_PAGE_SIZE
    end = start + UI_PAGE_SIZE
    page_articles = articles[start:end]

    # CARD GRID (3 per row, with spacing)
    st.markdown(f"### Showing page {st.session_state.page_num} of {total_pages}")

    if not page_articles:
        st.warning("No articles found.")
    else:
        rows = math.ceil(len(page_articles) / 3)
        idx = 0
        for r in range(rows):
            cols = st.columns(3)
            for col in cols:
                if idx >= len(page_articles):
                    break
                a = page_articles[idx]
                idx += 1

                card_html = f"""
                <div class="news-card">
                    {'<img src="'+a['image']+'" />' if a['image'] else ''}
                    <div class="news-card-content">
                        <p class="news-card-title"><a href="{a['url']}" target="_blank">{a['title']}</a></p>
                        <p class="news-card-meta">{a['source']} • {a['published_at'].strftime('%b %d, %H:%M')}</p>
                        <p class="news-card-snippet">{a['summary']}</p>
                    </div>
                </div>
                """
                col.markdown(card_html, unsafe_allow_html=True)

    # PAGINATION BUTTONS
    prev_col, mid_col, next_col = st.columns([1,2,1])
    with prev_col:
        if st.button("⬅ Prev", disabled=(st.session_state.page_num == 1)):
            st.session_state.page_num -= 1
            st.experimental_rerun()

    with mid_col:
        st.write("")  # spacing

    with next_col:
        if st.button("Next ➡", disabled=(st.session_state.page_num == total_pages)):
            st.session_state.page_num += 1
            st.experimental_rerun()
