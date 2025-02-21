import os
import subprocess
import shutil
import unittest
import tests.configure_logging

class TestIntegration(unittest.TestCase):
    def test_crawler_integration(self):
        domain_output = "output/example.com"
        sitemap_file = os.path.join(domain_output, "sitemap.dot")

        # Clean previous output if exists
        if os.path.exists(domain_output):
            shutil.rmtree(domain_output)

        # Run the crawler with default parameters (no explicit --depth)
        result = subprocess.run(
            ["python", "crawler.py", "https://example.com/", "--max-pages", "10"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        # Assert the process exited successfully.
        self.assertEqual(result.returncode, 0, msg="Crawler did not complete successfully.")

        # Check that the output folder and sitemap file exist.
        self.assertTrue(os.path.exists(domain_output), msg=f"Output directory {domain_output} not found.")
        self.assertTrue(os.path.exists(sitemap_file), msg="Sitemap file not created in the expected folder.")

        # Check that the all_docs.txt file exists in the output folder.
        all_docs_file = os.path.join(domain_output, "all_docs.txt")
        self.assertTrue(os.path.exists(all_docs_file), msg="all_docs.txt file not created in the expected folder.")

        # Optionally, check that there's at least one content file (.txt) in the output folder.
        txt_files = [f for f in os.listdir(domain_output) if f.endswith(".txt")]
        self.assertGreater(len(txt_files), 0, "No page content files found in the output folder.")

if __name__ == '__main__':
    unittest.main()
