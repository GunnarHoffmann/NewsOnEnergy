import streamlit as st
import os
import re
import html
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Agent news viewer",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for article tiles
st.markdown("""
<style>
.article-tile {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border-radius: 12px;
    padding: 24px;
    margin: 16px 0;
    border-left: 6px solid #1f77b4;
    transition: all 0.3s ease;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    cursor: pointer;
    position: relative;
}
.article-tile:hover {
    box-shadow: 0 8px 20px rgba(31,119,180,0.15);
    transform: translateY(-4px);
    border-left-color: #0d5aa7;
}
.article-title {
    font-size: 20px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 12px;
    line-height: 1.4;
}
.article-description {
    font-size: 15px;
    color: #555;
    line-height: 1.7;
    margin-bottom: 14px;
}
.article-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 12px;
    padding: 10px 20px;
    background-color: #1f77b4;
    color: white !important;
    text-decoration: none;
    font-weight: 600;
    font-size: 14px;
    border-radius: 6px;
    transition: all 0.2s ease;
}
.article-link:hover {
    background-color: #0d5aa7;
    transform: translateX(4px);
    text-decoration: none;
}
.article-link::after {
    content: '→';
    font-size: 16px;
    transition: transform 0.2s ease;
}
.article-link:hover::after {
    transform: translateX(4px);
}
.category-badge {
    display: inline-block;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
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

    # Create tile HTML
    tile_html = f"""
    <div class="article-tile">
        <div class="category-badge">{category}</div>
        <div class="article-title">{title}</div>
        <div class="article-description">{description}</div>
    """

    if url:
        tile_html += f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="article-link">Artikel lesen</a>'

    tile_html += "</div>"

    st.markdown(tile_html, unsafe_allow_html=True)

# Title
st.title("⚡ Agent news viewer")

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
            st.caption("Agent View")

            # Display articles as tiles
            if unique_articles:
                for article in unique_articles:
                    article_key = article.get('url', '') or article.get('title', '')
                    category = category_map.get(article_key, selected_categories[0])
                    display_article_tile(article, category)
            else:
                st.warning("No articles found in the selected files.")

# Footer
st.divider()
st.caption(f"Viewing from: {dir_path.absolute()}")
