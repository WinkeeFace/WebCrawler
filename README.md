# Web Crawler

A Python-based web crawler that maps website structure and extracts content. This tool can generate both text and Excel outputs of crawled pages along with visual sitemaps.

## Features

- Crawls websites and extracts content
- Generates visual sitemaps in DOT format
- Supports both TXT and XLSX output formats
- Configurable crawl depth and page limits
- Handles both internal and external links
- Normalizes URLs and removes unwanted parameters

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python crawler.py <URL>
```

Options:
- `--depth`: Maximum crawl depth (default: unlimited)
- `--max-pages`: Maximum number of pages to crawl (default: unlimited)
- `--output-format`: Output format, either 'txt' or 'xlsx' (default: txt)

Example:
```bash
python crawler.py https://example.com --depth 2 --max-pages 10 --output-format xlsx
```

## Output

The crawler generates two types of output:
1. Content files (TXT or XLSX) containing extracted text from crawled pages
2. A sitemap.dot file visualizing the website structure

Output files are organized in folders by domain name in the `output` directory.

## Dependencies

- requests: For making HTTP requests
- beautifulsoup4: For HTML parsing
- xlsxwriter: For Excel file generation
