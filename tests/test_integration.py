import os
import subprocess
import shutil
import unittest
import tests.configure_logging

class TestIntegration(unittest.TestCase):
    def test_crawler_integration(self):
        domain_output = "output/example.com"
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        sitemap_file = os.path.join(domain_output, f"example.com-sitemap_{current_date}.dot")

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
        self.assertTrue(os.path.exists(sitemap_file), msg=f"Sitemap {sitemap_file} file not created in the expected folder.")
        
        # Optionally, check that there's at least one content file (.txt) in the output folder.
        txt_files = [f for f in os.listdir(domain_output) if f.endswith(".txt")]
        self.assertGreater(len(txt_files), 0, "No page content files found in the output folder.")

if __name__ == '__main__':
    unittest.main()
