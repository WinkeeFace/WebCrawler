import os
from urllib.parse import urlparse

def store_content(domain_dir, url, content, duplicate_of=None):
    if not os.path.isdir(domain_dir):
        os.makedirs(domain_dir, exist_ok=True)
    filename = urlparse(url).netloc + urlparse(url).path
    filename = filename.replace("/", "_").replace(":", "") + ".txt"
    filepath = os.path.join(domain_dir, filename)
    with open(filepath, 'w') as f:
        if duplicate_of:
            f.write(f"URL: {url}\n")
            f.write(f"Content: duplicate of {duplicate_of}\n\n")
        else:
            f.write(f"URL: {url}\n")
            f.write(f"Content: {content}\n\n")
