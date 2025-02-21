import requests
from bs4 import BeautifulSoup
import logging
import time
import signal
import sys
import argparse
from urllib.parse import urljoin, urlparse
from utils import extract_text_from_html, classify_link, queue_internal_links, normalize_url
import os
from config import TIMEOUT, RETRIES
from sitemap import SitemapManager

import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# Spider animation frames
spider_frames = [
    "   / _ \\  ",
    "  \\_\\(_)/_/ ",
    "   _//\"\\\\_  ",
    "      /   \\   ",
]

spider_frames_alt = [
    "   / _ \\  ",
    " _\\(_)/_\\_ ",
    "  _//\"\\\\_  ",
    "   /   \\   ",
]

spider_frames_alt2 = [
    "   / _ \\  ",
    "  \\_\\(_)/_/ ",
    "  _//\"\\\\_  ",
    "   \\   /   ",
]

spider_frames_alt3 = [
    "   / _ \\  ",
    " _\\(_)/_\\_ ",
    "   //\"\\\\_  ",
    "   /   \\   ",
]

debug_step = 0

def debug_log(message):
    global debug_step
    debug_step += 1
    # logging.debug(f"[STEP {debug_step}] {message}")

def animate_spider(frame_index):
    """Displays the spider animation."""
    frame_index = frame_index % 4
    if frame_index == 0:
        frames = spider_frames
    elif frame_index == 1:
        frames = spider_frames_alt
    elif frame_index == 2:
        frames = spider_frames_alt2
    else:
        frames = spider_frames_alt3
    for line in frames:
        print(f"\r{line}", end="")
    sys.stdout.flush()

def fetch_page(url):
    """Fetches an HTML page and handles potential errors."""
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        # logging.info(f"Successfully fetched {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        # logging.error(f"Error fetching {url}: {e}")
        return None

def parse_html(html):
    """Parses HTML content and extracts relevant information."""
    return BeautifulSoup(html, 'html.parser')

def crawl(url, sitemap, base_url, depth=None, current_depth=0, max_pages=10):
    logging.info(f"crawl() called with url={url}")  # Add logging statement
    debug_log(f"Entered crawl() with url={url}, depth={depth}, current_depth={current_depth}")
    # logging.info(f"Starting crawl for {url} at depth {current_depth}")
    """Crawls a single page and extracts data."""
    if not url.startswith(base_url):
        logging.info(f"Skipping {url} as it does not start with the base URL {base_url}.")
        return sitemap

    if depth is not None and depth >= 0 and current_depth > depth:
        # logging.info(f"Skipping {url} due to depth limit.")
        return sitemap

    if url in sitemap.visited_urls:
        # logging.info(f"Skipping {url} as it is already visited.")
        return sitemap

    sitemap.mark_visited(url)
    debug_log(f"Marking {url} visited (visited count: {len(sitemap.visited_urls)})")
    # logging.info(f"Crawling {url} at depth {current_depth}")

    html_content = fetch_page(url)
    if not html_content:
        # logging.warning(f"No content fetched for {url}")
        return sitemap

    soup = parse_html(html_content)
    text = extract_text_from_html(soup)
    debug_log(f"Fetched page for {url}, text length={len(text) if text else 0}")

    # Check if the content is a duplicate
    if text in sitemap.page_contents.values():
        # logging.info(f"Skipping duplicate page: {url}")
        return sitemap

    # Add the content to the set of crawled page contents
    sitemap.page_contents[url] = text

    # Append content to all_docs.txt
    output_file_path = os.path.join(sitemap.output_folder, 'all_docs.txt')
    with open(output_file_path, 'a') as output_file:
        output_file.write(f"\n####### {url.upper()} #######\n\n")
        output_file.write(text)

    # Add all links to sitemap
    links = [link.get('href') for link in soup.find_all('a')]
    # logging.debug(f"Extracted links: {links}")
    debug_log(f"Found {len(links)} links on this page")
    # logging.debug(f"Extracted links from {url}: {links}")

    # Add all links to sitemap
    for link in links:
        if link:
            normalized_link = normalize_url(urljoin(url, link))
            sitemap.add_external_edge(url, normalized_link)
            # logging.debug(f"Added link {normalized_link} to sitemap")

    logging.info(f"Unvisited URLs after initial crawl: {sitemap.unvisited_urls}")  # Add logging statement
    while sitemap.has_unvisited_urls() and (max_pages == -1 or len(sitemap.visited_urls) < max_pages):
        print(f"has_unvisited_urls: {sitemap.has_unvisited_urls()}, visited_urls length: {len(sitemap.visited_urls)}, max_pages: {max_pages}")  # Add print statement
        next_url = sitemap.get_next_url()
        debug_log(f"Next URL to crawl: {next_url}")
        print(f"Next URL: {next_url}")  # Add print statement
        logging.info(f"Next URL: {next_url}, Visited URLs: {sitemap.visited_urls}")  # Add logging statement
        if next_url:
            logging.info(f"Crawling next URL: {next_url}")  # Add logging statement
            crawl(next_url, sitemap, base_url, depth, current_depth + 1, max_pages)
        sitemap.update_sitemap_file()
        import time
        frame_index = 0
        animate_spider(frame_index)
        frame_index += 1
        print_cli_output(sitemap)
        time.sleep(0.2)
    return sitemap

def print_cli_output(sitemap):
    """Prints the CLI output with the desired formatting."""
    print(f"\rMapped: {sitemap.mapped_count}  Unmapped: {sitemap.unmapped_count}", end="")
    sys.stdout.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl a website.')
    parser.add_argument('url', metavar='URL', type=str, help='The URL to crawl.')
    parser.add_argument('--depth', type=int, default=-1, help='Maximum crawl depth (optional).')
    parser.add_argument('--max-pages', type=int, default=-1, help='Maximum number of pages to crawl (optional).')
    args = parser.parse_args()
    start_url = args.url
    crawl_depth = args.depth
    max_pages = args.max_pages
    sitemap = SitemapManager(start_url)  # Pass start_url, so output folder becomes output/<domain>
    sitemap.add_url(start_url, start_url)  # Seed the sitemap with the start URL
    # sitemap.mark_visited(start_url)         # Mark the seed as visited

    # Configure logging
    # logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # logger.addHandler(handler)

    # Graceful exit handling
    def signal_handler(sig, frame):
        print("\nCrawling interrupted. Saving progress...")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        sitemap = crawl(start_url, sitemap, start_url, crawl_depth, 0, max_pages)
        print("\nCrawling completed.")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
        # sitemap.generate_sitemap_file()
    except KeyboardInterrupt:
        print("\nCrawling interrupted. Saving progress...")
        print(f"Mapped pages: {sitemap.mapped_count}")
        print(f"Unmapped pages: {sitemap.unmapped_count}")
        sys.exit(0)
