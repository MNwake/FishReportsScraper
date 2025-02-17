import time
from controller import FishSurveyController
from model import FishSurveyModel

SPECIES_FILE = "../data/fish_species.json"

# 1️⃣ Load JSON data **only once**
start_time = time.monotonic()
model = FishSurveyModel("data/surveys", "data/fish_species.json")
json_parse_time = time.monotonic() - start_time


# 2️⃣ Pass the preloaded model to the controller
controller = FishSurveyController(model, lambda x, y: None)
start_time = time.monotonic()
species_data = controller.load_species_map(SPECIES_FILE)
species_time = time.monotonic() - start_time


# 3️⃣ Render all data
start_time = time.monotonic()
all_data = controller.filter_and_sort_data()
render_time = time.monotonic() - start_time

# 4️⃣ Filter by county
start_time = time.monotonic()
controller.filter_and_sort_data(counties={"Hennepin"})
county_filter_time = time.monotonic() - start_time

# 5️⃣ Reset & Filter by species
start_time = time.monotonic()
controller.filter_and_sort_data(species="Walleye")
species_filter_time = time.monotonic() - start_time

# 6️⃣ Reset & Filter by min year
start_time = time.monotonic()
controller.filter_and_sort_data(min_year="2000")
min_year_filter_time = time.monotonic() - start_time

# 7️⃣ Sort entire dataset
start_time = time.monotonic()
all_data.sort(key=lambda x: x[3])  # Sort by survey date
sort_time = time.monotonic() - start_time

# 8️⃣ Total Time
total_time = (
    json_parse_time
    + render_time
    + county_filter_time
    + species_filter_time
    + min_year_filter_time
    + sort_time
)
