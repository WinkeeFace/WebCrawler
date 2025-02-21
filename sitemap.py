import logging
import os
from urllib.parse import urlparse, urljoin

debug_step = 0

def debug_log(message):
    global debug_step
    debug_step += 1
    # logging.debug(f"[SITEMAP STEP {debug_step}] {message}")

class SitemapManager:
    def __init__(self, base_url=None):
        self.visited_urls = set()
        self.unvisited_urls = []
        self.external_links = set()
        self.mapped_count = 0
        self.unmapped_count = 0
        self.page_contents = {}
        self.parent_urls = {}
        self.external_edges = []  # store (source, external_target)
        if base_url:
            domain = urlparse(base_url).netloc
            if not domain:
                domain = base_url.split('/')[0]
            self.output_folder = f"output/{domain}"
        else:
            self.output_folder = "output"
        os.makedirs(self.output_folder, exist_ok=True)

    def add_url(self, base_url, link_url):
        # debug_log(f"add_url() called with base_url={base_url}, link_url={link_url}")
        absolute_url = urljoin(base_url, link_url)
        is_external = self.is_external(base_url, absolute_url)
        if absolute_url != base_url and absolute_url not in self.visited_urls and absolute_url not in self.unvisited_urls:
            self.unvisited_urls.append(absolute_url)
            self.unmapped_count += 1
            self.parent_urls[absolute_url] = {'parent': base_url, 'is_external': is_external}
        # debug_log(f"After add_url, unvisited_urls={len(self.unvisited_urls)}")

    def mark_visited(self, url):
        logging.info(f"mark_visited() called with url: {url}")  # Add logging statement
        self.visited_urls.add(url)
        self.mapped_count += 1
        self.update_sitemap_file()

    def log_external_link(self, url):
        logging.info(f"External link logged: {url}")

    def is_external(self, base_url, link_url):
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(link_url).netloc
        if not link_domain:  # Check if link_url is a relative URL
            return False  # Treat relative URLs as internal
        return base_domain != link_domain

    def get_next_url(self):
        if self.unvisited_urls:
            logging.info(f"get_next_url() called, unvisited_urls before pop: {self.unvisited_urls}")  # Add logging statement
            next_url = self.unvisited_urls.pop()
            logging.info(f"get_next_url() called, unvisited_urls after pop: {self.unvisited_urls}")  # Add logging statement
            return next_url
        return None

    def has_unvisited_urls(self):
        print("has_unvisited_urls() called")  # Add print statement
        logging.info(f"has_unvisited_urls() called, unvisited_urls length: {len(self.unvisited_urls)}")  # Add logging statement
        return len(self.unvisited_urls) > 0

    def generate_sitemap_file(self, filename="sitemap.dot"):
        """Generates a sitemap.txt file in DOT format with the crawled URLs."""
        filepath = os.path.join(self.output_folder, filename)
        with open(filepath, "w") as f:
            f.write("/* DOT Tutorial: Hybrid Site Map Example Potential*/\n")
            f.write("digraph SiteMap {\n")
            f.write("    /* General Graph Attributes */\n")
            f.write("    graph [layout=neato, overlap=false, splines=true]; /* Hybrid layout */\n")
            f.write('    node [shape=circle, fontname="Arial", fontsize=12, style=filled, fillcolor=lightgray];\n')
            f.write("    edge [fontname=\"Arial\", fontsize=10];\n\n")

            f.write("    /* Hierarchical Structure */\n")
            for url in self.visited_urls:
                if url in self.parent_urls:
                    parent_url = self.parent_urls[url]['parent']
                    f.write(f'    "{parent_url}" -> "{url}";\n')
                else:
                    f.write(f'    "{url}" [fillcolor=lightblue];\n')

            f.write("\n    /* Cross-Links to Show Page Interconnections */\n")
            f.write("    edge [color=red, style=dashed];\n")
            # Basic cross-link implementation (can be improved)
            
            # Store URLs to avoid redundant cross-linking
            processed_urls = set()

            for url in self.visited_urls:
                for other_url in self.visited_urls:
                    # Avoid self-loops and duplicate cross-links
                    if url != other_url and (url, other_url) not in processed_urls and (other_url, url) not in processed_urls:
                        # Add cross-links for pages without hierarchical relationships
                        if url not in self.parent_urls and other_url not in self.parent_urls:
                            f.write(f'    "{url}" -> "{other_url}";\n')
                            processed_urls.add((url, other_url))  # Mark as processed

            f.write("}\n")
        # logging.info(f"Sitemap generated: {filepath}")

    def add_external_edge(self, parent_url, external_url):
        # logging.info(f"External link recorded: {external_url}")
        self.external_edges.append((parent_url, external_url))
        self.update_sitemap_file()

    def update_sitemap_file(self, filename="sitemap.dot"):
        # debug_log(f"update_sitemap_file() called with filename={filename}")
        """Updates the sitemap.dot file with the current state of the crawl."""
        filepath = os.path.join(self.output_folder, filename)
        try:
            with open(filepath, "w") as f:
                f.write("/* DOT Tutorial: Hybrid Site Map Example Potential*/\n")
                f.write("digraph SiteMap {\n")
                f.write("    /* General Graph Attributes */\n")
                f.write("    graph [layout=neato, overlap=false, splines=true]; /* Hybrid layout */\n")
                f.write('    node [shape=circle, fontname="Arial", fontsize=12, style=filled, fillcolor=lightgray];\n')
                f.write("    edge [fontname=\"Arial\", fontsize=10];\n\n")

                f.write("    /* Hierarchical Structure */\n")
                for url in self.visited_urls:
                    if url in self.parent_urls:
                        parent_url = self.parent_urls[url]['parent']
                        is_external = self.parent_urls[url]['is_external']
                        if is_external:
                            f.write(f'    "{parent_url}" -> "{url}" [color=blue];\n')
                            f.write(f'    "{url}" [shape=box, fillcolor=lightgreen];\n')
                        else:
                            f.write(f'    "{parent_url}" -> "{url}";\n')
                    else:
                        f.write(f'    "{url}" [fillcolor=lightblue];\n')

                f.write("\n    /* Cross-Links to Show Page Interconnections */\n")
                f.write("    edge [color=red, style=dashed];\n")
                # Basic cross-link implementation (can be improved)
                
                # Store URLs to avoid redundant cross-linking
                processed_urls = set()

                for url in self.visited_urls:
                    for other_url in self.visited_urls:
                        # Avoid self-loops and duplicate cross-links
                        if url != other_url and (url, other_url) not in processed_urls and (other_url, url) not in processed_urls:
                            # Add cross-links for pages without hierarchical relationships
                            if url not in self.parent_urls and other_url not in self.parent_urls:
                                f.write(f'    "{url}" -> "{other_url}";\n')
                                processed_urls.add((url, other_url))  # Mark as processed

                f.write("\n    /* External Edges to Show Exits */\n")
                for (source, target) in self.external_edges:
                    f.write(f'    "{source}" -> "{target}" [style=dotted, color=blue];\n')

                f.write("}\n")
            # logging.info(f"Sitemap updated: {filepath}")
            # debug_log(f"Finished writing {filepath}")
        except Exception as e:
            logging.error(f"Error updating sitemap file: {e}")
