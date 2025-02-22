import json
from playwright.sync_api import sync_playwright

from scraper import BaseScraper



WIKI_URL = "https://en.wikipedia.org/wiki/List_of_counties_in_Minnesota"


class CountyScraper(BaseScraper):
    def run(self):
        self.update_status("Starting County Scraper...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(WIKI_URL, timeout=60000)
            page.wait_for_selector("table.wikitable tbody tr")
            rows = page.query_selector_all("table.wikitable tbody tr")

            counties_data = []
            for row in rows:
                if self.stop:
                    self.update_status("Stop")
                    return
                cols = row.query_selector_all("td")
                if len(cols) >= 8:
                    county_name = row.query_selector("th a").inner_text() if row.query_selector("th a") else "Unknown"
                    fips_code = cols[0].inner_text().strip()
                    county_seat = cols[1].inner_text().strip()
                    established = int(cols[2].inner_text().strip())
                    origin = cols[3].inner_text().strip()
                    etymology = cols[4].inner_text().strip().replace("\u2013", "-")
                    population = int(cols[5].inner_text().replace(",", ""))
                    area_sq_miles = float(cols[6].inner_text().split("sq")[0].replace(",", ""))
                    map_image_element = cols[7].query_selector("img")
                    map_image_url = "https:" + map_image_element.get_attribute("src") if map_image_element else ""

                    counties_data.append({
                        "county_name": county_name,
                        "fips_code": fips_code,
                        "county_seat": county_seat,
                        "established": established,
                        "origin": origin,
                        "etymology": etymology,
                        "population": population,
                        "area_sq_miles": area_sq_miles,
                        "map_image_url": map_image_url
                    })
            browser.close()
            # Save data (update the file paths as needed)
            with open("scraper/data/minnesota_counties.json", "w", encoding="utf-8") as f:
                json.dump(counties_data, f, indent=4)
            self.update_status("County data successfully scraped and saved!")