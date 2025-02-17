import json
import os
from pathlib import Path
from typing import List, Dict

from pydantic import ValidationError

from . import FishData
from . import Species




class FishSurveyModel:
    def __init__(self, data_dir: str, species_file: str):
        self.data_dir = data_dir
        self.species_file = species_file
        self.species_map = self.load_species_map()
        self.fish_data_objects = self.load_fish_data_objects()


    def load_species_map(self) -> Dict[str, Species]:
        """
        Load species data from the JSON file and map abbreviation to Species objects.
        """
        with open(self.species_file, "r") as f:
            data = json.load(f)
        return {
            key: Species(
                code=key,
                common_name=value["common_name"],
                scientific_name=value["scientific_name"],
                game_fish=value["game_fish"],
                species_group=value["species_group"],
            )
            for key, value in data.items()
        }

    def load_fish_data_objects(self) -> List[FishData]:
        """
        Load all valid JSON files into FishData objects.
        """
        fish_data_objects = []
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file == "missing_surveys.json":  # Skip files named 'missing_surveys.json'
                    continue

                if file.endswith(".json"):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)

                        if not isinstance(data, dict):
                            raise ValueError(f"Top-level structure in {file_path} is not a dictionary.")

                        self.transform_fish_count(data)
                        fish_data = FishData(**data)

                        # Assign species to LengthData
                        self.assign_species_to_length_data(fish_data)
                        fish_data_objects.append(fish_data)

                    except (ValidationError, ValueError) as e:
                        print(f"Validation error in {file_path}: {e}")
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")

        return fish_data_objects

    def assign_species_to_length_data(self, fish_data: FishData):
        """
        Assign the species object to each LengthData entry in the surveys.
        """
        if not fish_data.result or not fish_data.result.surveys:
            return

        for survey in fish_data.result.surveys:
            if survey.lengths:
                for abbreviation, length_data in survey.lengths.items():
                    if abbreviation in self.species_map:
                        length_data.species = self.species_map[abbreviation]

    def transform_fish_count(self, data: dict):
        """
        Recursively transform 'fishCount' from a list of lists to a list of dictionaries.
        Example: [[11, 1], [12, 2]] -> [{"length": 11, "quantity": 1}, {"length": 12, "quantity": 2}]
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "fishCount" and isinstance(value, list) and all(isinstance(i, list) for i in value):
                    data[key] = [{"length": item[0], "quantity": item[1]} for item in value]
                else:
                    self.transform_fish_count(value)
        elif isinstance(data, list):
            for item in data:
                self.transform_fish_count(item)
