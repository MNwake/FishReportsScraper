import os
import re
import json
import logging
import requests
from playwright.sync_api import sync_playwright

from model import FishData

from scraper import BaseScraper

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def create_directory(path: str):
    os.makedirs(path, exist_ok=True)

def fetch_lake_data(get_data_url: str):
    response = requests.get(get_data_url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.warning(f"Failed to fetch JSON data from: {get_data_url}, status code: {response.status_code}")
        return None

def save_lake_data(fish_data: FishData, county_name: str, lake_name: str):
    try:
        county_dir = os.path.join("python", "data", "surveys", county_name)
        create_directory(county_dir)
        output_file = os.path.join(county_dir, f"{lake_name.replace(' ', '_')}.json")
        with open(output_file, "w") as f:
            f.write(fish_data.model_dump_json(indent=4))
        logger.info(f"Successfully saved data to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save lake data to {output_file}")

def save_missing_surveys(county_name: str, missing_surveys: list):
    try:
        county_dir = os.path.join("python","data", "surveys", county_name)
        create_directory(county_dir)
        missing_file = os.path.join(county_dir, "missing_surveys.json")
        with open(missing_file, "w") as f:
            json.dump(missing_surveys, f, indent=4)
        logger.info(f"Saved missing surveys to {missing_file}")
    except Exception as e:
        logger.error(f"Failed to save missing surveys: {e}")

def escape_css_selector(value: str) -> str:
    return re.sub(r"([\"\'\\#.:;?!&,\[\](){}|=`<>])", r"\\\1", value)

def transform_fish_count(data):
    """
    Recursively transform any fishCount fields that are lists of lists into lists of dictionaries.
    For example, converts: [[21, 1], [26, 1]] into:
    [{"length": 21, "quantity": 1}, {"length": 26, "quantity": 1}]
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "fishCount" and isinstance(value, list) and all(isinstance(i, list) for i in value):
                data[key] = [{"length": item[0], "quantity": item[1]} for item in value]
            else:
                transform_fish_count(value)
    elif isinstance(data, list):
        for item in data:
            transform_fish_count(item)

class FishSurveysScraper(BaseScraper):
    def __init__(self, gui_callback=None):
        super().__init__(gui_callback)
        self.stop = False

    def update_progress(self, county_id, county_name, lake_name, current, total):
        message = f"County #{county_id}: {county_name} | Lake: {lake_name} ({current}/{total})"
        self.update_status(message)

    def process_lake(self, page, lake_name, county_name, county_id, current, total):
        if self.stop:
            self.update_status("Stop")
            return
        try:
            logger.info(f"Processing lake: {lake_name}")
            lake_name_escaped = escape_css_selector(lake_name)
            logger.debug(f"Escaped lake name: {lake_name_escaped}")
            lake_row = page.locator(f"table#lakes tbody tr:has-text('{lake_name_escaped}') td a").first
            if lake_row.count() == 0:
                logger.warning(f"Lake '{lake_name}' not found in table.")
                return "Lake not found"

            for attempt in range(3):
                try:
                    lake_row.click(timeout=5000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    break
                except Exception as e:
                    logger.warning(f"Retrying lake {lake_name} (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        try:
                            logger.info(f"Refreshing page for lake {lake_name}")
                            page.reload(timeout=10000)
                            page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception as reload_error:
                            logger.error(f"Failed to refresh page for lake {lake_name}: {reload_error}")
                    else:
                        logger.error(f"Failed to process lake {lake_name} after 3 attempts.")
                        return "Failed after retries"

            fisheries_link = page.locator("a", has_text="Fisheries Lake Survey")
            if fisheries_link.count() == 0:
                logger.info(f"No 'Fisheries Lake Survey' link found for {lake_name}")
                return "No fisheries lake survey found"
            fisheries_link.first.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=10000)

            get_data_link = page.locator("a", has_text="get the data")
            if get_data_link.count() == 0:
                logger.warning(f"No 'Get the Data' link found for {lake_name}")
                return "No 'Get the Data' link found"
            get_data_url = get_data_link.first.get_attribute("href")
            if get_data_url:
                json_data = fetch_lake_data(get_data_url)
                if json_data:
                    # Transform fishCount lists to dictionaries
                    transform_fish_count(json_data)
                    # Supply a default countyName if missing
                    if "result" in json_data and "countyName" not in json_data["result"]:
                        json_data["result"]["countyName"] = county_name
                    try:
                        fish_data = FishData(**json_data)
                        save_lake_data(fish_data, county_name, lake_name)
                        return "Data saved successfully"
                    except Exception as e:
                        logger.error(f"Pydantic validation error for {lake_name}: {e}")
                        return f"Pydantic validation error: {e}"
        except Exception as e:
            logger.error(f"Error processing lake: {lake_name} in county: {county_name}: {e}")
            return f"Error: {e}"
        finally:
            self.update_progress(county_id, county_name, lake_name, current, total)

    def process_county(self, page, county_id):
        missing_surveys = []
        county_url = f"https://www.dnr.state.mn.us/lakefind/search.html?name=&county={county_id}"
        logger.info(f"Starting county: {county_id}")
        try:
            page.goto(county_url, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            logger.error(f"Error navigating to county {county_id}: {e}")
            return

        lake_rows = page.locator("table#lakes tbody tr")
        lake_count = lake_rows.count()
        logger.info(f"Found {lake_count} lakes in county {county_id}.")
        county_name = f"County_{county_id}"
        try:
            first_data_row = page.get_by_role("row").nth(1)
            row_cells = first_data_row.get_by_role("cell")
            county_name = row_cells.nth(-1).text_content(timeout=5000).strip()
            logger.info(f"Extracted county name: {county_name}")
        except Exception as e:
            logger.error(f"Failed to extract county name for county_id {county_id}: {e}")

        for i in range(lake_count):
            if self.stop:
                self.update_status("Stop")
                return
            try:
                page.goto(county_url, timeout=10000)
                page.wait_for_load_state("networkidle", timeout=5000)
                lake_row = lake_rows.nth(i)
                lake_name = lake_row.locator("td a").first.text_content(timeout=5000).strip()
                result = self.process_lake(page, lake_name, county_name, county_id, i + 1, lake_count)
                if result:
                    logger.info(f"Result for lake '{lake_name}': {result}")
                    if "No fisheries lake survey" in result or "Error" in result:
                        missing_surveys.append({"lake_name": lake_name, "result": result})
            except Exception as e:
                logger.error(f"Error processing lake in county {county_id}: {e}")
                missing_surveys.append({"lake_name": lake_name if 'lake_name' in locals() else "Unknown", "error": str(e)})

        save_missing_surveys(county_name, missing_surveys)

    def retry_failed_lakes(self, playwright, county_lake_errors):
        logger.info("Retrying error logs")
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for county_id in range(1, 89):
            if self.stop:
                logger.info("Scraper stopped by user.")
                break
            logger.info(f"Checking county ID: {county_id}")
            try:
                county_url = f"https://www.dnr.state.mn.us/lakefind/search.html?name=&county={county_id}"
                page.goto(county_url, timeout=10000)
                page.wait_for_load_state("networkidle", timeout=5000)
                county_name = "Unknown"
                try:
                    first_data_row = page.get_by_role("row").nth(1)
                    row_cells = first_data_row.get_by_role("cell")
                    county_name = row_cells.nth(-1).text_content(timeout=5000).strip()
                    logger.info(f"Extracted county name: {county_name}")
                except Exception as e:
                    logger.warning(f"Failed to extract county name for county ID {county_id}: {e}")
                    continue

                if county_name not in county_lake_errors:
                    logger.info(f"No failed lakes for county: {county_name} (ID: {county_id})")
                    continue

                for lake_name in county_lake_errors[county_name]:
                    if self.stop:
                        logger.info("Scraper stopped by user.")
                        break
                    escaped_lake_name = escape_css_selector(lake_name)
                    logger.debug(f"Retrying lake: {lake_name} (escaped: {escaped_lake_name}) in county: {county_name}")
                    try:
                        lake_row = page.locator(
                            "table#lakes tbody tr",
                            has_text=re.compile(re.escape(lake_name), re.IGNORECASE)
                        ).locator("td a").first
                        if lake_row.count() == 0:
                            logger.warning(f"Lake '{lake_name}' not found in county: {county_name}")
                            continue
                        result = self.process_lake(page, lake_name, county_name, county_id, 0, len(county_lake_errors[county_name]))
                        if result != "Data saved successfully":
                            logger.warning(f"Retry failed for lake: {lake_name} in county: {county_name}")
                    except Exception as e:
                        logger.error(f"Error retrying lake: {lake_name} in county: {county_name}: {e}")
            except Exception as e:
                logger.error(f"Error processing county ID {county_id}: {e}")
        context.close()
        browser.close()

    def run(self):
        self.update_status("Starting full scrape...")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            for county_id in range(1, 88):
                if self.stop:
                    self.update_status("Stop")
                    return
                try:
                    self.process_county(page, county_id)
                except Exception as e:
                    logger.error(f"Error processing county {county_id}: {e}")
            context.close()
            browser.close()
        self.update_status("Fish Surveys scraping completed!")

