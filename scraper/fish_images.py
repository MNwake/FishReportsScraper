import json, time
from playwright.sync_api import sync_playwright

from .base import BaseScraper


# File paths
LOCAL_SPECIES_FILE = "python/data/fish_species.json"
SERVER_SPECIES_FILE = "backend/data/fish_species.json"
DEFAULT_IMAGE = "https://static.pokemonpets.com/images/monsters-images-800-800/2129-Shiny-Magikarp.webp"


def load_fish_species():
    with open(LOCAL_SPECIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fish_species(data):
    for file_path in [LOCAL_SPECIES_FILE, SERVER_SPECIES_FILE]:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


class FishImagesScraper(BaseScraper):
    def run(self):
        self.update_status("Starting Fish Images Scraper...")
        fish_data = load_fish_species()
        with sync_playwright() as playwright:
            for code, fish in fish_data.items():
                if self.stop:
                    self.update_status("Stop")
                    return
                common_name = fish["common_name"]
                if "image_url" in fish and fish["image_url"] and "description" in fish and fish["description"]:
                    self.update_status(f"Skipping {common_name} (data already exists)")
                    continue
                image_url, description = self.fetch_fish_image_url_and_description(playwright, common_name)
                fish_data[code]["image_url"] = image_url
                fish_data[code]["description"] = description
                save_fish_species(fish_data)
                self.update_status(f"Updated data for {common_name}")
                time.sleep(2)
        self.update_status("Fish species JSON updated successfully!")

    def fetch_fish_image_url_and_description(self, playwright, common_name):
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        fish_url = f"https://en.wikipedia.org/wiki/{common_name.replace(' ', '_')}"
        if self.stop:
            self.update_status("Stop")
            return
        try:
            page.goto(fish_url, timeout=5000)  # Limit page load to 5 seconds
        except Exception as e:
            self.update_status(f"Page load timed out for {common_name}")
            context.close()
            browser.close()
            return DEFAULT_IMAGE, ""

        image_url = DEFAULT_IMAGE
        description = ""
        try:

            self.update_status(f"Looking for image for {common_name}")
            # Wait up to 5 seconds for the image element to appear
            img_element = page.locator(".infobox img").first
            img_element.wait_for(timeout=5000)
            img_src = img_element.get_attribute("src")
            if img_src:
                image_url = f"https:{img_src}"
            # Get paragraphs for description; no extra wait is applied here.
            paragraphs = page.locator(".mw-parser-output p").all()
            for p in paragraphs:
                text = p.inner_text().strip()
                if text and "may refer to:" not in text and "This article is about" not in text:
                    description = text
                    break
        except Exception as e:
            self.update_status(f'No image found for {common_name}')
        finally:
            context.close()
            browser.close()
        return image_url, description
