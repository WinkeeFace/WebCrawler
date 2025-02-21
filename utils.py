"""Utility functions for web crawling and URL handling."""

import logging
import os
from urllib.parse import urlparse, urljoin
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# HTML Processing Functions
def extract_text_from_html(soup):
    """Extracts readable text from the HTML body."""
    try:
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        else:
            logging.warning("No body tag found in HTML.")
            return ""
    except Exception as e:
        logging.error(f"Error extracting text: {e}")
        return ""


# URL Classification and Management
def classify_link(base_url, link_url):
    """Classifies a link as internal or external."""
    try:
        absolute_url = urljoin(base_url, link_url)
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(absolute_url).netloc

        if link_domain == base_domain:
            return "internal"
        else:
            return "external"
    except Exception as e:
        logging.error(f"Error classifying link {link_url}: {e}")
        return "unknown"


# File Operations
def save_content(url, text):
    """Saves extracted content to a file."""
    try:
        # Create directory based on the domain
        domain = urlparse(url).netloc
        output_dir = f"output/{domain}"
        os.makedirs(output_dir, exist_ok=True)

        # Sanitize the URL to create a valid filename
        filename = re.sub(r'https?://', '', url).replace("/", "-").replace("?", "_") + ".txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        logging.info(f"Saved content from {url} to {filepath}")

    except Exception as e:
        logging.error(f"Error saving content from {url}: {e}")


# URL Normalization
def normalize_url(url, params_to_remove=['utm_source', 'session_id']):
    """Normalizes a URL by removing fragments and specified query parameters.
    
    Args:
        url (str): The URL to normalize
        params_to_remove (list): Query parameters to strip from URL, defaults to
            ['utm_source', 'session_id']. Common tracking and session parameters
            that don't affect page content.
    
    Returns:
        str: Normalized URL with specified parameters and fragments removed
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Remove specified parameters
        query_params = {k: v for k, v in query_params.items() if k not in params_to_remove}

        # Reconstruct the query string
        new_query = urlencode(query_params, doseq=True)

        # Reconstruct the URL, removing the fragment
        new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                                parsed_url.params, new_query, None))  # None removes the fragment

        return new_url
    except Exception as e:
        logging.error(f"Error normalizing URL {url}: {e}")
        return url


# Queue Management
def queue_internal_links(url_queue, base_url, links):
    """Queues internal links for further crawling.
    
    Args:
        url_queue (list): Queue of URLs to be crawled
        base_url (str): Base URL of the website being crawled
        links (list): List of links found on the current page
        
    Note:
        Only internal links (same domain as base_url) are added to the queue.
        External links are logged but not queued for crawling.
    """
    try:
        for link in links:
            normalized_url = normalize_url(urljoin(base_url, link))
            if classify_link(base_url, normalized_url) == "internal":
                if normalized_url not in url_queue:
                    url_queue.append(normalized_url)
            else:
                logging.info(f"Skipping external link: {normalized_url}")
    except Exception as e:
        logging.error(f"Error queueing links: {e}")
