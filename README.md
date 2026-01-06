# SIF - Social Media Metrics Scraper

A Python application that scrapes social media metrics (likes, comments, views, shares) from Instagram and TikTok posts, with a Flask API for managing links and retrieving data.

## Features

- Scrape Instagram and TikTok post metrics
- Store metrics in MySQL database
- Flask REST API for link management
- Support for both direct MySQL and Metabase API connections
- Background scraper with rate limiting

## Requirements

- Python 3.11+
- MySQL database
- (Optional) Metabase instance

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sif
```

2. Create a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Metabase (optional - for Metabase API mode)
METABASE_EMAIL=your_email@example.com
METABASE_PASSWORD=your_password
METABASE_URL=https://your-metabase-url.com

# MySQL (required)
MYSQL_HOST=localhost:10110
MYSQL_PORT=10110
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=hanayo_prod
```

## Database Setup

The application automatically creates the required tables:

- `links` - Stores social media links and their metrics
- `link_locks` - Prevents concurrent scraping of the same link

## Usage

### Run the Flask API Server

```bash
python main.py
```

The API will be available at `http://localhost:5000`

### Run the Standalone Scraper

```bash
python scrapper.py
```

The scraper runs continuously, processing links every 60 seconds.

## API Endpoints

### Insert Links
```http
POST /insert/links
Content-Type: application/json

{
  "links": [
    "https://www.instagram.com/p/ABC123/",
    "https://www.tiktok.com/@user/video/123456"
  ]
}
```

### Get Post Metrics
```http
POST /get/post-links
Content-Type: application/json

{
  "links": [
    "https://www.instagram.com/p/ABC123/"
  ]
}
```

### Get COGS by Order IDs
```http
POST /get/cogs
Content-Type: application/json

{
  "user_claims": [
    {"user": "user1", "order_ids": ["123", "456"]}
  ],
  "all_order_ids": ["123", "456", "789"]
}
```

## Project Structure

```
sif/
├── main.py           # Flask API server
├── scrapper.py       # Standalone scraper script
├── requirements.txt  # Python dependencies
├── .env             # Environment variables (not in git)
├── .env.example     # Environment variables template
├── sif/
│   ├── __init__.py  # Database functions (vanilla MySQL & Metabase)
│   └── scrap.py     # Metabase-based scraper
└── backup/          # Old/duplicate files
```

## License

See LICENSE file.
