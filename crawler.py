"""Web crawler for extracting and mapping website content.

This module provides functionality to crawl websites, extract content,
generate sitemaps, and save the results in various formats. It handles
both internal and external links while respecting domain boundaries.
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import signal
import sys
from utils import extract_text_from_html, classify_link, queue_internal_links, normalize_url, RobotsParser
import argparse
from urllib.parse import urljoin, urlparse
from utils import extract_text_from_html, classify_link, queue_internal_links, normalize_url
import os
from config import TIMEOUT, RETRIES
from sitemap import SitemapManager
import xlsxwriter
from datetime import datetime

def get_site_name(url):
    """Extract and format the site name from URL."""
    parsed = urlparse(url)
    site_name = parsed.netloc.lower()
    return f"{site_name}-content"

def create_output_file_name(url, output_format):
    """Create output file name with site name and current date."""
    site_name = get_site_name(url)
    current_date = datetime.now().strftime('%Y-%m-%d')
    return f"{site_name}_{current_date}.{output_format}"

def write_to_xlsx(output_file_path, page_contents):
    """Write the crawled content to an XLSX file."""
    workbook = xlsxwriter.Workbook(output_file_path)
    worksheet = workbook.add_worksheet()
    
    # Write headers
    worksheet.write(0, 0, 'url')
    worksheet.write(0, 1, 'content')
    
    # Write data
    for i, (url, content) in enumerate(page_contents.items(), 1):
        worksheet.write(i, 0, url)
        worksheet.write(i, 1, content)
    
    workbook.close()

def write_to_txt(output_file_path, url, text):
    """Write content to a text file."""
    with open(output_file_path, 'a') as output_file:
        output_file.write(f"\n####### START {url.upper()} #######\n\n")
        output_file.write(text)
        output_file.write(f"\n\n####### END {url.upper()} #######\n\n")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# Spinner animation frames
spinner_frames = ['|', '/', '-', '\\']


def animate_spinner(frame_index):
    """Displays the spinner animation."""
    frame_index = frame_index % len(spinner_frames)
    print(f"\r{spinner_frames[frame_index]}", end="")
    sys.stdout.flush()


def fetch_page(url):
    """Fetches an HTML page and handles potential errors.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        str: The HTML content of the page, or None if the fetch failed
        
    Note:
        Uses global TIMEOUT and RETRIES settings from config.py
    """
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return None


def parse_html(html):
    """Parses HTML content using BeautifulSoup.
    
    Args:
        html (str): Raw HTML content to parse
        
    Returns:
        BeautifulSoup: Parsed HTML document object
    """
    return BeautifulSoup(html, 'html.parser')


def crawl(url, sitemap, base_url, robots_parser=None, depth=None, current_depth=0, max_pages=10, output_format='txt'):
    """Recursively crawls a website starting from the given URL.
    
    Args:
        url (str): The URL to start crawling from
        sitemap (SitemapManager): Manager for tracking crawl state
        base_url (str): The root URL to stay within while crawling
        depth (int, optional): Maximum depth to crawl. None for unlimited
        current_depth (int): Current recursion depth. Used internally
        max_pages (int): Maximum number of pages to crawl. -1 for unlimited
        output_format (str): Format to save content in ('txt' or 'xlsx')
    
    Returns:
        SitemapManager: Updated sitemap with crawl results
        
    Note:
        Content is saved to files in the output directory as pages are crawled.
        The sitemap is continuously updated to show crawl progress.
    """
    # Ensure output directory exists
    os.makedirs(sitemap.output_folder, exist_ok=True)
    output_file_path = os.path.join(sitemap.output_folder, create_output_file_name(base_url, output_format))
    
    if robots_parser is None:
        robots_parser = RobotsParser(base_url)

    if not url.startswith(base_url):
        print(f"\rSkipping {url} - outside base URL {base_url}")
        return sitemap

    if not robots_parser.is_allowed(url):
        print(f"\rSkipping {url} - disallowed by robots.txt")
        return sitemap

    if depth is not None and depth >= 0 and current_depth > depth:
        return sitemap

    if url in sitemap.visited_urls:
        return sitemap

    sitemap.mark_visited(url)
    print(f"\rCrawling: {url}")
    
    robots_parser.respect_crawl_delay()
    html_content = fetch_page(url)
    if not html_content:
        print(f"\rFailed to fetch: {url}")
        return sitemap

    soup = parse_html(html_content)
    text = extract_text_from_html(soup)

    if text in sitemap.page_contents.values():
        print(f"\rSkipping duplicate content: {url}")
        return sitemap

    sitemap.page_contents[url] = text

    if output_format == 'xlsx':
        # For xlsx, we'll write everything at once at the end
        if len(sitemap.visited_urls) >= max_pages and max_pages != -1:
            write_to_xlsx(output_file_path, sitemap.page_contents)
    else:
        write_to_txt(output_file_path, url, text)

    links = [link.get('href') for link in soup.find_all('a')]
    print(f"\rFound {len(links)} links on {url}")

    for link in links:
        if link:
            normalized_link = normalize_url(urljoin(url, link))
            if sitemap.is_external(url, normalized_link):
                sitemap.add_external_edge(url, normalized_link)
            else:
                sitemap.add_url(url, normalized_link)

    while sitemap.has_unvisited_urls() and (max_pages == -1 or len(sitemap.visited_urls) < max_pages):
        next_url = sitemap.get_next_url()
        if next_url:
            crawl(next_url, sitemap, base_url, robots_parser, depth, current_depth + 1, max_pages)
        sitemap.update_sitemap_file()
        frame_index = 0
        animate_spinner(frame_index)
        frame_index += 1
        print_cli_output(sitemap)
        time.sleep(0.2)
    return sitemap

def print_cli_output(sitemap):
    """Prints the CLI output with the desired formatting."""
    print(f"\rMapped: {sitemap.mapped_count}  Unmapped: {sitemap.unmapped_count}", end="")
    sys.stdout.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl a website and generate a content map.')
    
    # Required arguments
    parser.add_argument('url', metavar='URL', type=str,
                      help='Starting URL to crawl (e.g., https://example.com)')
    
    # Optional crawl control arguments
    parser.add_argument('--depth', type=int, default=-1,
                      help='Maximum crawl depth. -1 for unlimited (default: -1)')
    parser.add_argument('--max-pages', type=int, default=-1,
                      help='Maximum pages to crawl. -1 for unlimited (default: -1)')
    
    # Output format selection
    parser.add_argument('--output-format', type=str, choices=['txt', 'xlsx'], default='txt',
                      help='Save content as text files or Excel spreadsheet (default: txt)')
    args = parser.parse_args()
    start_url = args.url
    crawl_depth = args.depth
    max_pages = args.max_pages
    output_format = args.output_format
    sitemap = SitemapManager(start_url)
    robots_parser = RobotsParser(start_url)
    sitemap.add_url(start_url, start_url)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    def signal_handler(sig, frame):
        print("\nCrawling interrupted. Saving progress...")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        sitemap = crawl(start_url, sitemap, start_url, robots_parser, crawl_depth, 0, max_pages, output_format)
        # Write xlsx file at the end if that's the chosen format
        if output_format == 'xlsx':
            output_file_path = os.path.join(sitemap.output_folder, create_output_file_name(start_url, output_format))
            write_to_xlsx(output_file_path, sitemap.page_contents)
        print("\nCrawling completed.")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
    except KeyboardInterrupt:
        print("\nCrawling interrupted. Saving progress...")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
        sys.exit(0)
