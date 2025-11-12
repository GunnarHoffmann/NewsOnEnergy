import streamlit as st
import os
import re
import html
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Agent viewer",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for article tiles - E.ON inspired professional design
st.markdown("""
<style>
/* Import professional fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Sans+Pro:wght@400;600;700&display=swap');

/* Global styling */
.stApp {
    font-family: 'Inter', 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Article tile link wrapper */
.article-tile-link {
    display: block;
    text-decoration: none;
    color: inherit;
    position: relative;
    z-index: 1;
}
.article-tile-link:hover {
    text-decoration: none;
}
.article-tile-link:visited {
    color: inherit;
}

/* Article tile - E.ON professional style */
.article-tile {
    background: #ffffff;
    border-radius: 2px;
    padding: 24px 20px;
    margin: 0 0 16px 0;
    border-left: 3px solid #EA1C0A;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.12);
    cursor: pointer;
    position: relative;
    height: 100%;
    min-height: 160px;
}
.article-tile:hover {
    box-shadow: 0 4px 12px rgba(234,28,10,0.12), 0 2px 6px rgba(0,0,0,0.08);
    transform: translateY(-2px);
    border-left-color: #c01608;
}

/* Article title */
.article-title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 12px;
    line-height: 1.4;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.01em;
}

/* Article description */
.article-description {
    font-size: 13px;
    color: #5a5a5a;
    line-height: 1.6;
    margin-bottom: 0;
    font-weight: 400;
}

/* Category badge - E.ON red accent */
.category-badge {
    display: inline-block;
    background: #EA1C0A;
    color: white;
    padding: 5px 12px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 600;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'Inter', sans-serif;
}

/* Header styling */
h1 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: #1a1a1a;
    letter-spacing: -0.02em;
}

h2, h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #2a2a2a;
}

/* Streamlit button customization for E.ON style */
.stButton > button {
    border-radius: 2px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.02em;
}

/* Selectbox and input styling */
.stSelectbox, .stMultiSelect, .stDateInput {
    font-family: 'Inter', sans-serif;
}

/* Stylish caption */
.stylish-caption {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: #EA1C0A;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: -8px;
    margin-bottom: 24px;
    padding-left: 4px;
    position: relative;
    display: inline-block;
}

.stylish-caption::before {
    content: '';
    position: absolute;
    left: 0;
    bottom: -4px;
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, #EA1C0A 0%, rgba(234,28,10,0) 100%);
}
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_available_dates(directory):
    """Scan directory and extract all unique dates from filenames."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return set()

    dates = set()
    for file in dir_path.glob("*.md"):
        # Extract date from filename (YYYYMMDD format)
        match = re.match(r"(\d{8})_", file.name)
        if match:
            date_str = match.group(1)
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d").date()
                dates.add(date_obj)
            except ValueError:
                continue

    return dates

def parse_article_format1(text):
    """Parse format: **Title** Description [Link](url)"""
    articles = []
    # Split by numbered entries
    entries = re.split(r'\*\*\d+\.', text)

    for entry in entries[1:]:  # Skip first empty split
        # Extract title
        title_match = re.search(r'^(.*?)\*\*', entry)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # Extract link
        link_match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', entry)
        url = link_match.group(1) if link_match else ""

        # Extract description (text between title and link)
        desc_text = re.sub(r'\[.*?\]\(.*?\)', '', entry)
        desc_text = re.sub(r'^\*\*.*?\*\*', '', desc_text)
        description = desc_text.strip()

        if title and description:
            articles.append({
                'title': title,
                'description': description,
                'url': url
            })

    return articles

def parse_article_format2(text):
    """Parse format: ## N. Title **Kurzbeschreibung:** ... **URL:** ..."""
    articles = []
    # Split by ## headers
    entries = re.split(r'\n## \d+\.', text)

    for entry in entries[1:]:  # Skip first empty split
        lines = entry.strip().split('\n')
        if not lines:
            continue

        # Title is first line
        title = lines[0].strip()

        # Extract description
        desc_match = re.search(r'\*\*Kurzbeschreibung:\*\*\s*(.*?)(?:\*\*URL:\*\*|$)', entry, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""

        # Extract URL
        url_match = re.search(r'\*\*URL:\*\*\s*(https?://[^\s]+)', entry)
        url = url_match.group(1).strip() if url_match else ""

        if title and description:
            articles.append({
                'title': title,
                'description': description,
                'url': url
            })

    return articles

def parse_article_format3(text):
    """Parse format: ### N. Title \n Description \n [Mehr lesen](url) \n _Kurzbeschreibung:..._"""
    articles = []
    # Split by ### headers
    entries = re.split(r'\n### \d+\.', text)

    for entry in entries[1:]:  # Skip first empty split
        lines = entry.strip().split('\n')
        if not lines:
            continue

        # Title is first line
        title = lines[0].strip()

        # Extract URL from [Mehr lesen](url) or similar markdown links
        url_match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', entry)
        url = url_match.group(1) if url_match else ""

        # Build description from multiple sources
        description_parts = []

        # Get text before the link (usually the main description)
        text_before_link = '\n'.join(lines[1:]).split('[')[0].strip()
        if text_before_link:
            description_parts.append(text_before_link)

        # Extract Kurzbeschreibung if present
        kurz_match = re.search(r'_Kurzbeschreibung:\s*(.*?)_', entry, re.DOTALL)
        if kurz_match:
            kurz_text = kurz_match.group(1).strip()
            if kurz_text and kurz_text not in text_before_link:
                description_parts.append(kurz_text)

        description = ' '.join(description_parts).strip()

        if title and description:
            articles.append({
                'title': title,
                'description': description,
                'url': url
            })

    return articles

def parse_article_format4(text):
    """Parse format: N. **Title** *Description* [Link](url)"""
    articles = []
    # Split by numbered entries (1. 2. 3. etc.)
    # Match both at start of file and after newlines
    entries = re.split(r'(?:^|\n)(\d+)\.\s+', text)

    # entries will be: ['', '1', 'content1', '2', 'content2', ...]
    # Process in pairs (number, content)
    for i in range(1, len(entries), 2):
        if i + 1 >= len(entries):
            break

        entry = entries[i + 1]

        # Extract title from **Title**
        title_match = re.search(r'\*\*(.+?)\*\*', entry)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # Extract description from *Description* (italic text)
        desc_match = re.search(r'(?<!\*)\*([^*]+?)\*(?!\*)', entry)
        description = desc_match.group(1).strip() if desc_match else ""

        # Extract URL from [text](url)
        url_match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', entry)
        url = url_match.group(1) if url_match else ""

        if title:
            articles.append({
                'title': title,
                'description': description,
                'url': url
            })

    return articles

def parse_articles_from_file(file_path):
    """Parse articles from a markdown file, auto-detecting format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Detect format and parse accordingly
        # Check for ### headers (format 3 - weekly format)
        if re.search(r'\n### \d+\.', content):
            return parse_article_format3(content)
        # Check for ## headers with **Kurzbeschreibung:** (format 2)
        elif '**Kurzbeschreibung:**' in content:
            return parse_article_format2(content)
        # Check for format 4: N. **Title** (number before bold)
        elif re.search(r'(?:^|\n)\d+\.\s+\*\*', content):
            return parse_article_format4(content)
        # Default to format 1 (bold numbered entries)
        else:
            return parse_article_format1(content)

    except Exception as e:
        st.error(f"Error parsing file {file_path}: {str(e)}")
        return []

def deduplicate_articles(articles):
    """Remove duplicate articles based on URL or title similarity."""
    seen_urls = set()
    seen_titles = set()
    unique_articles = []

    for article in articles:
        url = article.get('url', '').strip()
        title = article.get('title', '').strip().lower()

        # Skip if we've seen this URL (primary deduplication key)
        if url and url in seen_urls:
            continue

        # Skip if we've seen very similar title (secondary check)
        if title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)

        unique_articles.append(article)

    return unique_articles

def display_article_tile(article, category):
    """Display an article as a nice clickable tile."""
    title = article.get('title', 'Untitled')
    description = article.get('description', '')
    url = article.get('url', '')

    # Escape HTML special characters to prevent rendering issues
    title = html.escape(title)
    description = html.escape(description)
    url_escaped = html.escape(url) if url else ''

    # Create tile HTML - wrap entire tile in a link if URL exists
    if url:
        tile_html = f"""
        <a href="{url_escaped}" target="_blank" rel="noopener noreferrer" class="article-tile-link" style="pointer-events: all;">
            <div class="article-tile" style="pointer-events: none;">
                <div class="category-badge">{category}</div>
                <div class="article-title">{title}</div>
                <div class="article-description">{description}</div>
            </div>
        </a>
        """
    else:
        tile_html = f"""
        <div class="article-tile" style="opacity: 0.7;">
            <div class="category-badge">{category}</div>
            <div class="article-title">{title}</div>
            <div class="article-description">{description}</div>
        </div>
        """

    st.markdown(tile_html, unsafe_allow_html=True)

# Title
st.title("Agent viewer")

# Create tabs
tab1, tab2 = st.tabs(["Show agent news", "Show agent events"])

with tab1:
    # Create two columns for the selectors
    col1, col2 = st.columns(2)

    with col1:
        # View type selector
        view_type = st.selectbox(
            "Select View Type",
            ["Daily", "Weekly"],
            index=0
        )

    # Determine directory based on view type
    directory = "DAILY" if view_type == "Daily" else "WEEKLY"
    dir_path = Path(directory)

    # Get available dates for the selected view
    available_dates = get_available_dates(directory)

    with col2:
        # Date selector with info about available dates
        if available_dates:
            min_date = min(available_dates)
            max_date = max(available_dates)

            selected_date = st.date_input(
                f"Select Date ({len(available_dates)} dates available)",
                value=max_date,  # Default to most recent date
                min_value=min_date,
                max_value=max_date
            )

            # Show info if selected date is not available
            if selected_date not in available_dates:
                st.warning(f"⚠️ No data available for {selected_date.strftime('%Y-%m-%d')}. Available dates: {len(available_dates)}")
        else:
            selected_date = st.date_input(
                "Select Date",
                value=datetime.now(),
                max_value=datetime.now()
            )
            st.error(f"No data found in '{directory}' directory!")

    # Format date as YYYYMMDD
    date_str = selected_date.strftime("%Y%m%d")

    # Check if directory exists
    if not dir_path.exists():
        st.error(f"Directory '{directory}' not found!")
    else:
        # Find all files for the selected date
        pattern = f"{date_str}_*.md"
        matching_files = list(dir_path.glob(pattern))

        if not matching_files:
            st.warning(f"No files found for date {selected_date.strftime('%Y-%m-%d')} in {view_type} view.")
            if available_dates:
                st.info(f"Try one of these available dates: {', '.join([d.strftime('%Y-%m-%d') for d in sorted(available_dates, reverse=True)[:5]])}")
        else:
            # Extract categories from filenames
            categories = []
            for file in matching_files:
                # Extract category name (part after date and underscore, before .md)
                category = file.stem.replace(f"{date_str}_", "")
                categories.append(category)

            # Multi-select for categories
            st.subheader("Select Topics")
            selected_categories = st.multiselect(
                "Available topics (select one or more)",
                categories,
                default=categories  # Select all by default
            )

            if not selected_categories:
                st.info("Please select at least one topic to view articles.")
            else:
                # Collect all articles from selected categories
                all_articles = []
                category_map = {}  # Map articles to their source category

                for category in selected_categories:
                    file_path = dir_path / f"{date_str}_{category}.md"
                    articles = parse_articles_from_file(file_path)

                    for article in articles:
                        all_articles.append(article)
                        # Store which category this article came from
                        article_key = article.get('url', '') or article.get('title', '')
                        if article_key not in category_map:
                            category_map[article_key] = category

                # Deduplicate articles
                unique_articles = deduplicate_articles(all_articles)

                # Display summary
                st.divider()
                st.subheader(f"📰 {len(unique_articles)} Articles - {selected_date.strftime('%Y-%m-%d')}")
                st.markdown('<div class="stylish-caption">Agent View</div>', unsafe_allow_html=True)

                # Display articles as tiles in 3-column grid
                if unique_articles:
                    # Create 3 columns for responsive grid layout
                    cols = st.columns(3)

                    # Distribute articles across columns
                    for idx, article in enumerate(unique_articles):
                        article_key = article.get('url', '') or article.get('title', '')
                        category = category_map.get(article_key, selected_categories[0])

                        # Use modulo to cycle through columns
                        with cols[idx % 3]:
                            display_article_tile(article, category)
                else:
                    st.warning("No articles found in the selected files.")

    # Footer
    st.divider()
    st.caption(f"Viewing from: {dir_path.absolute()}")

with tab2:
    st.info("in progress")
