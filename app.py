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
    height: 240px;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
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

def get_country_flag(country_name):
    """Return country flag emoji based on country name from markdown section."""
    if not country_name:
        return ''

    country_lower = country_name.lower()

    # Map country names to flag emojis
    country_flags = {
        'schweiz': '🇨🇭',
        'switzerland': '🇨🇭',
        'suisse': '🇨🇭',
        'svizzera': '🇨🇭',
        'deutschland': '🇩🇪',
        'germany': '🇩🇪',
        'england': '🇬🇧',
        'uk': '🇬🇧',
        'united kingdom': '🇬🇧',
        'britain': '🇬🇧',
        'great britain': '🇬🇧'
    }

    return country_flags.get(country_lower, '')

def parse_events_from_file(file_path):
    """Parse events from a markdown file with event format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        events = []
        current_country = None

        # Split content into lines to track country sections
        lines_list = content.split('\n')

        # First, identify country sections (## CountryName)
        country_sections = {}
        current_section_country = None
        current_section_start = 0

        for i, line in enumerate(lines_list):
            # Check for country header (## followed by country name)
            if line.strip().startswith('## ') and not line.strip().startswith('###'):
                if current_section_country:
                    # Save previous section
                    country_sections[current_section_country] = (current_section_start, i)
                current_section_country = line.strip()[3:].strip()  # Remove "## "
                current_section_start = i

        # Save the last section
        if current_section_country:
            country_sections[current_section_country] = (current_section_start, len(lines_list))

        # Now parse events and assign them to countries based on their position
        entries = re.split(r'\n###\s+', content)

        for entry in entries[1:]:  # Skip first split (header info)
            event = {}

            # Extract event title (first line after ###)
            lines = entry.strip().split('\n')
            if not lines:
                continue

            # First line contains date and name
            title_line = lines[0].strip()
            event['title'] = title_line

            # Find which country section this event belongs to
            # Search for the event's title line in the original content
            event_position = content.find(f"### {title_line}")
            if event_position != -1:
                # Determine which country section this position falls into
                for country, (start, end) in country_sections.items():
                    section_start_pos = content.find('\n'.join(lines_list[start:end]))
                    section_end_pos = section_start_pos + len('\n'.join(lines_list[start:end]))
                    if section_start_pos <= event_position < section_end_pos:
                        event['country'] = country
                        break

            # Extract structured fields
            for line in lines[1:]:
                line = line.strip()

                # Extract date
                if line.startswith('- **Datum:**'):
                    date_str = line.replace('- **Datum:**', '').strip()
                    event['date'] = date_str

                # Extract name
                elif line.startswith('- **Name:**'):
                    name = line.replace('- **Name:**', '').strip()
                    event['name'] = name

                # Extract location
                elif line.startswith('- **Ort:**'):
                    location = line.replace('- **Ort:**', '').strip()
                    event['location'] = location

                # Extract link
                elif line.startswith('- **Link:**'):
                    url = line.replace('- **Link:**', '').strip()
                    event['url'] = url

                # Extract days until event
                elif line.startswith('- **Differenz zu heute:**'):
                    days_str = line.replace('- **Differenz zu heute:**', '').strip()
                    event['days_until'] = days_str

            if event.get('name') and event.get('date'):
                events.append(event)

        return events

    except Exception as e:
        st.error(f"Error parsing event file {file_path}: {str(e)}")
        return []

def display_event_tile(event, event_type):
    """Display an event as a nice clickable tile."""
    name = event.get('name', 'Untitled Event')
    date = event.get('date', '')
    location = event.get('location', '')
    url = event.get('url', '')
    days_until = event.get('days_until', '')
    country = event.get('country', '')

    # Get country flag from country section in markdown
    country_flag = get_country_flag(country)

    # Escape HTML special characters
    name = html.escape(name)
    date = html.escape(date)
    location = html.escape(location)
    url_escaped = html.escape(url) if url else ''
    days_until = html.escape(days_until)

    # Create description with location and days until (no flag here anymore)
    description = f"📍 {location}"
    if days_until:
        description += f" • ⏰ {days_until}"

    # Create flag element for top right corner
    flag_html = f'<div style="position: absolute; top: 20px; right: 20px; font-size: 32px; line-height: 1;">{country_flag}</div>' if country_flag else ''

    # Create tile HTML
    if url:
        tile_html = f"""
        <a href="{url_escaped}" target="_blank" rel="noopener noreferrer" class="article-tile-link" style="pointer-events: all;">
            <div class="article-tile" style="pointer-events: none; position: relative;">
                {flag_html}
                <div class="category-badge">{event_type}</div>
                <div class="article-title">{name}</div>
                <div style="font-size: 12px; color: #EA1C0A; font-weight: 600; margin-bottom: 8px;">📅 {date}</div>
                <div class="article-description">{description}</div>
            </div>
        </a>
        """
    else:
        tile_html = f"""
        <div class="article-tile" style="opacity: 0.7; position: relative;">
            {flag_html}
            <div class="category-badge">{event_type}</div>
            <div class="article-title">{name}</div>
            <div style="font-size: 12px; color: #EA1C0A; font-weight: 600; margin-bottom: 8px;">📅 {date}</div>
            <div class="article-description">{description}</div>
        </div>
        """

    st.markdown(tile_html, unsafe_allow_html=True)

def get_available_event_dates(directory):
    """Scan directory and extract all unique dates from event filenames."""
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

# Title with professional caption
st.markdown("""
<div style="margin-bottom: 2rem;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0;">
            <rect x="3" y="3" width="8" height="8" rx="1" stroke="#EA1C0A" stroke-width="1.5" fill="none"/>
            <rect x="13" y="3" width="8" height="8" rx="1" stroke="#EA1C0A" stroke-width="1.5" fill="none"/>
            <rect x="3" y="13" width="8" height="8" rx="1" stroke="#EA1C0A" stroke-width="1.5" fill="none"/>
            <rect x="13" y="13" width="8" height="8" rx="1" stroke="#EA1C0A" stroke-width="1.5" fill="none"/>
            <circle cx="7" cy="7" r="1.5" fill="#EA1C0A"/>
            <circle cx="17" cy="7" r="1.5" fill="#EA1C0A"/>
            <path d="M5 17L9 17" stroke="#EA1C0A" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M15 17L19 17" stroke="#EA1C0A" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <h1 style="margin: 0; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 2.5rem; color: #1a1a1a; letter-spacing: -0.02em;">
            Agent Viewer
        </h1>
    </div>
    <div style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #5a5a5a; font-weight: 400; padding-left: 40px;">
        Monitor and analyze AI-curated news across multiple topics
    </div>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["Show News", "Show Events"])

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
    directory = f"NEWS/{'DAILY' if view_type == 'Daily' else 'WEEKLY'}"
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

            # Generate Management Summary button
            if st.button("Generate Management Summary"):
                st.info("Management Summary generation feature coming soon!")

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
    # Events directory
    events_directory = "EVENTS"
    events_dir_path = Path(events_directory)

    # Get available dates for events
    available_event_dates = get_available_event_dates(events_directory)

    # Create two columns for the selectors
    col1, col2 = st.columns(2)

    with col1:
        # Date selector with info about available dates
        if available_event_dates:
            min_event_date = min(available_event_dates)
            max_event_date = max(available_event_dates)

            selected_event_date = st.date_input(
                f"Select Event Date ({len(available_event_dates)} dates available)",
                value=max_event_date,  # Default to most recent date
                min_value=min_event_date,
                max_value=max_event_date,
                key="event_date"
            )

            # Show info if selected date is not available
            if selected_event_date not in available_event_dates:
                st.warning(f"⚠️ No event data available for {selected_event_date.strftime('%Y-%m-%d')}. Available dates: {len(available_event_dates)}")
        else:
            selected_event_date = st.date_input(
                "Select Event Date",
                value=datetime.now(),
                max_value=datetime.now(),
                key="event_date"
            )
            st.error(f"No event data found in '{events_directory}' directory!")

    # Check if directory exists
    if not events_dir_path.exists():
        st.error(f"Directory '{events_directory}' not found!")
    else:
        # Format date as YYYYMMDD
        event_date_str = selected_event_date.strftime("%Y%m%d")

        # Find all event files for the selected date
        event_pattern = f"{event_date_str}_*.md"
        matching_event_files = list(events_dir_path.glob(event_pattern))

        if not matching_event_files:
            st.warning(f"No event files found for date {selected_event_date.strftime('%Y-%m-%d')}.")
            if available_event_dates:
                st.info(f"Try one of these available dates: {', '.join([d.strftime('%Y-%m-%d') for d in sorted(available_event_dates, reverse=True)[:5]])}")
        else:
            # Extract event types from filenames
            event_types = []
            for file in matching_event_files:
                # Extract event type (part after date and underscore, before .md)
                event_type = file.stem.replace(f"{event_date_str}_", "")
                event_types.append(event_type)

            with col2:
                # Multi-select for event types
                selected_event_types = st.multiselect(
                    "Available event types (select one or more)",
                    event_types,
                    default=event_types,  # Select all by default
                    key="event_types"
                )

            if not selected_event_types:
                st.info("Please select at least one event type to view events.")
            else:
                # Collect all events from selected types
                all_events = []
                event_type_map = {}  # Map events to their source type

                for event_type in selected_event_types:
                    file_path = events_dir_path / f"{event_date_str}_{event_type}.md"
                    events = parse_events_from_file(file_path)

                    for event in events:
                        all_events.append(event)
                        # Store which type this event came from
                        event_key = event.get('url', '') or event.get('name', '')
                        if event_key not in event_type_map:
                            event_type_map[event_key] = event_type

                # Sort events by date (upcoming events first)
                def parse_event_date(event):
                    """Parse event date for sorting, handling invalid dates."""
                    date_str = event.get('date', '')
                    if not date_str:
                        return datetime.max  # Put events without dates at the end
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        return datetime.max  # Put events with invalid dates at the end

                all_events.sort(key=parse_event_date)

                # Display summary
                st.divider()
                st.subheader(f"📅 {len(all_events)} Events - {selected_event_date.strftime('%Y-%m-%d')}")
                st.markdown('<div class="stylish-caption">Upcoming AI Events</div>', unsafe_allow_html=True)

                # Display events as tiles in 3-column grid
                if all_events:
                    # Create 3 columns for responsive grid layout
                    cols = st.columns(3)

                    # Distribute events across columns
                    for idx, event in enumerate(all_events):
                        event_key = event.get('url', '') or event.get('name', '')
                        event_type = event_type_map.get(event_key, selected_event_types[0])

                        # Use modulo to cycle through columns
                        with cols[idx % 3]:
                            display_event_tile(event, event_type)
                else:
                    st.warning("No events found in the selected files.")

    # Footer
    st.divider()
    st.caption(f"Viewing events from: {events_dir_path.absolute()}")
