import json
from typing import List, Optional, Tuple


class FishSurveyController:
    def __init__(self,model, root, view_class):
        self.model = model
        self.view = view_class(root, self)

    def load_species_map(self, species_file: str) -> dict:
        """
        Load species data from the JSON file and map abbreviation to common name.
        """
        with open(species_file, "r") as f:
            data = json.load(f)
        # Map species code to common names (capitalized)
        species_map = {k: v["common_name"].capitalize() for k, v in data.items()}
        return species_map

    def get_species_list(self) -> List[str]:
        """
        Get a sorted list of species' common names for the dropdown.
        """
        species_abbreviations = set()
        for fish_data in self.model.fish_data_objects:
            if fish_data.result and fish_data.result.surveys:
                for survey in fish_data.result.surveys:
                    if survey.lengths:
                        species_abbreviations.update(survey.lengths.keys())

        species_common_names = []
        for abbr in species_abbreviations:
            species_obj = self.model.species_map.get(abbr)
            if species_obj:
                # Use the common_name attribute (capitalized)
                species_common_names.append(species_obj.common_name.capitalize())
            else:
                species_common_names.append(abbr)

        return sorted(species_common_names)

    def get_year_list(self) -> List[str]:
        """
        Get a sorted list of survey years for the dropdown.
        """
        years = set()
        for fish_data in self.model.fish_data_objects:
            if fish_data.result and fish_data.result.surveys:
                for survey in fish_data.result.surveys:
                    years.add(survey.surveyDate.split("-")[0])
        return sorted(years, reverse=True)

    def filter_and_sort_data(self, species: Optional[str] = None, min_year: Optional[str] = None,
                             counties: Optional[set] = None) -> List[Tuple]:
        """
        Filter and sort the fish data based on species, year, and counties.
        Returns a list of rows for the table.
        Each species in each survey gets its own row.
        """
        # Convert min_year to an integer if it's not None
        min_year = int(min_year) if min_year else None

        species_abbreviation = None
        if species and species != "All Species":
            species_abbreviation = next(
                (abbr for abbr, species_obj in self.model.species_map.items()
                 if species_obj.common_name.capitalize() == species), None
            )
            if not species_abbreviation:
                return []

        rows = []
        for fish_data in self.model.fish_data_objects:
            if fish_data.result and fish_data.result.surveys:
                if counties and fish_data.result.countyName not in counties:
                    continue  # Skip counties not in the filter

                for survey in fish_data.result.surveys:
                    survey_year = int(survey.surveyDate.split("-")[0])
                    if min_year and survey_year < min_year:
                        continue

                    # Iterate through all species in the survey lengths
                    for abbreviation, length_data in survey.lengths.items():
                        # Skip species not matching the selected filter
                        if species_abbreviation and abbreviation != species_abbreviation:
                            continue

                        # Calculate total caught for the species
                        total_caught = sum(
                            catch_summary.totalCatch or 0
                            for catch_summary in survey.fishCatchSummaries or []
                            if catch_summary.species == abbreviation
                        )

                        # Add a row for each species
                        rows.append((
                            fish_data.result.DOWNumber,  # DOW Number
                            fish_data.result.countyName,  # County Name
                            fish_data.result.lakeName,  # Lake Name
                            survey.surveyDate,  # Survey Date
                            length_data.species.common_name,  # Species Common Name
                            total_caught,  # Total Caught
                            length_data.minimum_length,  # Min Length
                            length_data.maximum_length,  # Max Length
                        ))

        # Return rows sorted by DOW Number and Survey Date
        return sorted(rows, key=lambda x: (x[0], x[3]))

    def get_county_list(self) -> List[str]:
        """
        Retrieve a list of unique county names from the data.
        """
        counties = set()
        for fish_data in self.model.fish_data_objects:
            if fish_data.result and fish_data.result.countyName:
                counties.add(fish_data.result.countyName)
        return sorted(counties)
