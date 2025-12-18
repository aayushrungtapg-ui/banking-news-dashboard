import streamlit as st
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import math

# ---------------- CONFIG ----------------

# 🔴 Put your NewsAPI key here
API_KEY = "aa09c77c5ad841ebaaf1ec387e74f4ab"  # e.g. "eHdpLknQzjxQJSseM0eJjekQM55WsBFZhepT49rf"
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

DAYS_BACK = 3              # how many days of news
MAX_API_PAGES = 5          # how many pages to fetch from NewsAPI
API_PAGE_SIZE = 50         # how many articles per page from NewsAPI

UI_PAGE_SIZE = 50          # how many cards you want per UI page
MAX_UI_PAGES = 5           # max pages you want user to be able to click through

TOPIC_QUERIES = {
    "Banking": 'banking OR "banking sector" OR "retail banking"',
    "Digital Banking": '"digital banking" OR "online banking" OR "mobile banking"',
    "Digital Transformation": '"digital transformation" AND banking',
    "Fintech": 'fintech OR "financial technology" AND banking',
    "Neobanks": 'neobank OR "neo bank" OR "digital-only bank" OR "challenger bank"',
    "Payments": '"digital payments" OR "payment rails" OR RTGS OR UPI OR "real-time payments"',
    "AI in Banking": '"AI in banking" OR "artificial intelligence" AND banking OR "machine learning" AND banking',
}

# ---------------- STYLING ----------------

CUSTOM_CSS = """
<style>
body, .stApp {
    background-color: #f5f6fa;
}
.block-container {
    padding-top: 1.5rem;
}

/* Left feeds panel header */
.feeds-header {
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* News cards */
.news-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 0;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    display: flex;
    flex-direction: column;
    height: 100%;
}
.news-card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
}
.news-card-content {
    padding: 0.8rem 0.9rem 0.9rem 0.9rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}
.news-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.25rem;
    margin: 0;
}
.news-card-title a {
    color: #111827;
    text-decoration: none;
}
.news-card-title a:hover {
    text-decoration: underline;
}
.news-card-meta {
    font-size: 0.7rem;
    color: #6b7280;
}
.news-card-snippet {
    font-size: 0.78rem;
    color: #4b5563;
}
.section-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9ca3af;
}

/* Search bar rounded */
.search-bar input {
    border-radius: 999px !important;
}
</style>
"""

st.set_page_config(page_title="Banking & Fintech News", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------- HELPERS ----------------

def normalize_published(published_str):
    if not published_str:
        return datetime.utcnow()
    try:
        return date_parser.parse(published_str)
    except Exception:
        return datetime.utcnow()


def fetch_news(query, days_back=DAYS_BACK, max_pages=MAX_API_PAGES, page_size=API_PAGE_SIZE):
    """Fetch up to max_pages*page_size articles from NewsAPI."""
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

        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=20)

        if resp.status_code == 401:
            st.error("NewsAPI returned 401 (Unauthorized). Check your API key.")
            break

        if resp.status_code != 200:
            st.error(
                f"NewsAPI error (status {resp.status_code}) on page {page}: "
                f"{resp.text[:200]}"
            )
            break

        data = resp.json()
        if data.get("status") != "ok":
            st.error(f"NewsAPI error JSON: {data}")
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

            max_chars = 220
            if text and len(text) > max_chars:
                snippet = text[:max_chars].rsplit(" ", 1)[0] + "..."
            else:
                snippet = text

            source_name = (article.get("source") or {}).get("name") or "Unknown"
            published_at = normalize_published(article.get("publishedAt"))
            image = article.get("urlToImage")

            all_articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": snippet,
                    "source": source_name,
                    "published_at": published_at,
                    "image": image,
                }
            )

        if len(articles) < page_size:
            break
        page += 1

    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles


def get_query_signature(feed_choice, search_query):
    return f"{feed_choice}|{search_query.strip()}"


# ---------------- LAYOUT ----------------

# Top row
top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown("### 📡 Feeds")
with top_right:
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

left_col, right_col = st.columns([1, 4])

# ---- Left: feeds ----
with left_col:
    st.markdown('<div class="feeds-header">Feeds</div>', unsafe_allow_html=True)
    feed_options = ["Newsfeed (All)"] + list(TOPIC_QUERIES.keys())
    feed_choice = st.radio(
        "Feeds",
        feed_options,
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("----")
    st.caption("Use the search bar on the right to override feeds.")

# ---- Right: search + cards + pagination ----
with right_col:
    st.markdown('<div class="section-label">Newsfeed</div>', unsafe_allow_html=True)
    search_query = st.text_input(
        "",
        placeholder="Search in articles (e.g., UPI, RBI, 'digital lending')",
        label_visibility="collapsed",
        key="search_bar",
    )

    # Figure out which query we are running
    if search_query.strip():
        query = search_query.strip()
        feed_title = f"Results for: **{query}**"
    else:
        if feed_choice == "Newsfeed (All)":
            query = " OR ".join(f"({q})" for q in TOPIC_QUERIES.values())
            feed_title = "All banking & fintech feeds"
        else:
            query = TOPIC_QUERIES[feed_choice]
            feed_title = feed_choice

    # Reset pagination if query changed
    current_signature = get_query_signature(feed_choice, search_query)
    if "last_signature" not in st.session_state:
        st.session_state.last_signature = current_signature
    if "page_num" not in st.session_state:
        st.session_state.page_num = 1

    if st.session_state.last_signature != current_signature:
        st.session_state.page_num = 1
        st.session_state.last_signature = current_signature

    # Fetch data
    with st.spinner("Fetching latest news…"):
        articles = fetch_news(query)

    st.markdown(f"#### {feed_title}")

    if not articles:
        st.warning(
            "No articles found. This can happen if the query is too narrow, or the "
            "NewsAPI free quota is exhausted. Try another keyword or feed."
        )
    else:
        # ---- Pagination logic ----
        total_articles = len(articles)
        total_pages = math.ceil(total_articles / UI_PAGE_SIZE)
        total_pages = min(total_pages, MAX_UI_PAGES)

        # Clamp current page
        if st.session_state.page_num < 1:
            st.session_state.page_num = 1
        if st.session_state.page_num > total_pages:
            st.session_state.page_num = total_pages

        page_num = st.session_state.page_num

        start_idx = (page_num - 1) * UI_PAGE_SIZE
        end_idx = start_idx + UI_PAGE_SIZE
        page_articles = articles[start_idx:end_idx]

        # ---- Render cards (grid) for this page ----
        cards_per_row = 3
        for i in range(0, len(page_articles), cards_per_row):
            row_articles = page_articles[i:i + cards_per_row]
            row_cols = st.columns(cards_per_row)
            for col, article in zip(row_cols, row_articles):
                with col:
                    image_url = article["image"]
                    title = article["title"]
                    url = article["url"]
                    summary = article["summary"]
                    source = article["source"]
                    published_at = article["published_at"].strftime("%Y-%m-%d %H:%M")

                    card_html_parts = ['<div class="news-card">']
                    if image_url:
                        card_html_parts.append(
                            f'<img src="{image_url}" alt="thumbnail" />'
                        )
                    card_html_parts.append('<div class="news-card-content">')
                    card_html_parts.append(
                        f'<p class="news-card-title"><a href="{url}" target="_blank">{title}</a></p>'
                    )
                    card_html_parts.append(
                        f'<p class="news-card-meta">{source} • {published_at}</p>'
                    )
                    if summary:
                        card_html_parts.append(
                            f'<p class="news-card-snippet">{summary}</p>'
                        )
                    card_html_parts.append("</div></div>")

                    card_html = "".join(card_html_parts)
                    st.markdown(card_html, unsafe_allow_html=True)

        # ---- Pagination controls ----
        st.write("")
        pag_left, pag_mid, pag_right = st.columns([1, 2, 1])
        with pag_left:
            if st.button("⬅ Previous", disabled=(page_num <= 1)):
                st.session_state.page_num = max(1, page_num - 1)
                st.experimental_rerun()
        with pag_mid:
            st.markdown(
                f"<p style='text-align:center;font-size:0.85rem;color:#6b7280;'>"
                f"Page {page_num} of {total_pages} • Showing {len(page_articles)} of {total_articles} articles"
                f"</p>",
                unsafe_allow_html=True,
            )
        with pag_right:
            if st.button("Next ➡", disabled=(page_num >= total_pages)):
                st.session_state.page_num = min(total_pages, page_num + 1)
                st.experimental_rerun()
