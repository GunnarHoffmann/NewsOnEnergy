import streamlit as st
import os
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="News On Energy Viewer",
    page_icon="⚡",
    layout="wide"
)

# Title
st.title("⚡ News On Energy Viewer")

# Create two columns for the selectors
col1, col2 = st.columns(2)

with col1:
    # View type selector
    view_type = st.selectbox(
        "Select View Type",
        ["Daily", "Weekly"],
        index=0
    )

with col2:
    # Date selector
    selected_date = st.date_input(
        "Select Date",
        value=datetime.now(),
        max_value=datetime.now()
    )

# Format date as YYYYMMDD
date_str = selected_date.strftime("%Y%m%d")

# Determine directory based on view type
directory = "DAILY" if view_type == "Daily" else "WEEKLY"
dir_path = Path(directory)

# Check if directory exists
if not dir_path.exists():
    st.error(f"Directory '{directory}' not found!")
else:
    # Find all files for the selected date
    pattern = f"{date_str}_*.md"
    matching_files = list(dir_path.glob(pattern))

    if not matching_files:
        st.warning(f"No files found for date {selected_date.strftime('%Y-%m-%d')} in {view_type} view.")
        st.info("Please try a different date or view type.")
    else:
        # Extract categories from filenames
        categories = []
        for file in matching_files:
            # Extract category name (part after date and underscore, before .md)
            category = file.stem.replace(f"{date_str}_", "")
            categories.append(category)

        # Category selector
        st.subheader("Select Category")
        selected_category = st.selectbox(
            "Available categories",
            categories,
            index=0
        )

        # Construct the full file path
        file_path = dir_path / f"{date_str}_{selected_category}.md"

        # Display file information
        st.divider()
        st.subheader(f"📄 {view_type} News - {selected_date.strftime('%Y-%m-%d')} - {selected_category}")

        # Read and display file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Display the content as markdown
            st.markdown(content)

            # Optional: Add a download button
            st.divider()
            st.download_button(
                label="📥 Download File",
                data=content,
                file_name=file_path.name,
                mime="text/markdown"
            )

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Footer
st.divider()
st.caption(f"Viewing from: {dir_path.absolute()}")
