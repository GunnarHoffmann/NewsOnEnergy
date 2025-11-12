# News On Energy Viewer - Streamlit App

A Streamlit web application for viewing daily and weekly energy news articles.

## Features

- **View Type Selection**: Choose between Daily or Weekly news views
- **Date Selection**: Pick any date to view news from that day
- **Category Selection**: Browse available news categories (Energiepolitik, Energietechnologien, Energiewirtschaft)
- **Markdown Display**: View formatted news articles with links
- **Download Option**: Download news files directly from the app

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the App

Run the Streamlit app with:

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Usage

1. Select either "Daily" or "Weekly" view from the dropdown
2. Choose a date using the date picker
3. Select a category from the available options
4. View the news content displayed as formatted markdown
5. Optionally download the file using the download button

## Directory Structure

The app expects the following directory structure:

```
NewsOnEnergy/
├── app.py
├── DAILY/
│   └── YYYYMMDD_Category.md
└── WEEKLY/
    └── YYYYMMDD_Category.md
```

## File Naming Convention

Files should follow the pattern: `YYYYMMDD_CategoryName.md`

Example: `20251112_Energiewirtschaft.md`
