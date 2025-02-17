# view/main_screen.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from scraper import CountyScraper, FishImagesScraper, FishSurveysScraper


class FishSurveyView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.sort_column = None
        self.sort_order = True
        self.rows = []
        self.selected_counties = set(controller.get_county_list())  # All counties selected by default
        self.scraper = None  # Track the current scraper
        self.setup_gui()

    def setup_gui(self):
        # --- Scraper Control Section (Nested Frame in Column 0) ---
        self.scraper_frame = ttk.Frame(self.root)
        self.scraper_frame.grid(row=0, column=0, columnspan=1, sticky="nw", padx=10, pady=5)

        # Nested grid inside scraper_frame.
        self.scraper_var = tk.StringVar(value="County Scraper")
        self.dropdown = ttk.Combobox(
            self.scraper_frame,
            textvariable=self.scraper_var,
            values=["County Scraper", "Fish Images Scraper", "Fish Surveys Scraper"],
            state="readonly",
            width=30
        )
        self.dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.start_button = ttk.Button(
            self.scraper_frame,
            text="Start Scraping",
            command=self.start_scraper
        )
        self.start_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(
            self.scraper_frame,
            textvariable=self.status_var
        )
        self.status_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # --- Fish Survey Controls Section (Columns 1-3 of Outer Grid) ---
        species_label = tk.Label(self.root, text="Select Fish Species:")
        species_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        species_list = ["All Species"] + self.controller.get_species_list()
        self.species_dropdown = ttk.Combobox(
            self.root, values=species_list, state="readonly", width=30
        )
        self.species_dropdown.current(0)  # Default to "All Species"
        self.species_dropdown.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.species_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_table())

        year_label = tk.Label(self.root, text="Select Year:")
        year_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        year_list = ["All Years"] + self.controller.get_year_list()
        self.year_dropdown = ttk.Combobox(
            self.root, values=year_list, state="readonly", width=30
        )
        self.year_dropdown.current(0)  # Default to "All Years"
        self.year_dropdown.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.year_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_table())

        county_filter_button = tk.Button(self.root, text="Filter by County", command=self.open_county_filter)
        county_filter_button.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        self.county_filter_button = county_filter_button

        export_button = tk.Button(self.root, text="Export to CSV", command=self.export_table)
        export_button.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        # --- Table Section ---
        columns = [
            "DOW Number", "County Name", "Lake Name", "Survey Date",
            "Species", "Total Caught", "Min Length", "Max Length",
        ]
        self.table = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        for col in columns:
            self.table.heading(col, text=col, command=lambda c=col: self.sort_table(c))
            self.table.column(col, width=150)
        self.table.grid(row=3, column=0, columnspan=4, padx=10, pady=10)
        self.table.bind("<<TreeviewSelect>>", self.display_fish_count_graph)

        # --- Graph Section ---
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.ax.set_title("Fish Count")
        self.ax.set_xlabel("Length")
        self.ax.set_ylabel("Quantity")
        self.fig.tight_layout(pad=2.0)
        self.fig.subplots_adjust(bottom=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        self.update_table()

    def update_status(self, message):
        if message == 'Stop':
            self.status_var.set("Idle")
            self.root.update_idletasks()
            self.dropdown.config(state="enabled")
            self.start_button.config(text="Start Scraping")

        self.status_var.set(message)
        self.root.update_idletasks()

    def start_scraper(self):
        # If a scraper is already running, then this button acts as a Stop.
        if self.scraper is not None:
            self.update_status("Stopping scraper...")
            self.scraper.stop = True  # Signal the scraper to stop.
            # Optionally, wait until it stops (using after to poll).
            self.check_scraper()
            return

        # No scraper is running; start a new one.
        scraper_choice = self.dropdown.get()
        self.update_status(f"Running {scraper_choice}...")
        if scraper_choice == "County Scraper":
            scraper = CountyScraper(gui_callback=self.update_status)
        elif scraper_choice == "Fish Images Scraper":
            scraper = FishImagesScraper(gui_callback=self.update_status)
        elif scraper_choice == "Fish Surveys Scraper":
            scraper = FishSurveysScraper(gui_callback=self.update_status)
        else:
            self.update_status("Unknown scraper selected.")
            return

        self.scraper = scraper
        # Disable the dropdown so the selection cannot change while running.
        self.dropdown.config(state="disabled")
        # Change the start button text to "Stop Scraping"
        self.start_button.config(text="Stop Scraping")
        scraper.start()
        # Begin polling to check when the scraper thread finishes.
        self.root.after(100, self.check_scraper)

    def check_scraper(self):
        if self.scraper is not None and self.scraper.thread.is_alive():
            # If the thread is still alive, poll again.
            self.root.after(100, self.check_scraper)
        else:
            # Scraper has finished (or was stopped). Reset controls.
            self.dropdown.config(state="normal")
            self.start_button.config(text="Start Scraping")
            self.scraper = None
            self.update_status("Scraping complete!")

    def update_table(self):
        selected_species = self.species_dropdown.get()
        selected_year = self.year_dropdown.get()
        if selected_species == "All Species":
            selected_species = None
        if selected_year == "All Years":
            selected_year = None
        self.rows = self.controller.filter_and_sort_data(selected_species, selected_year, self.selected_counties)
        self.refresh_table()

    def open_county_filter(self):
        counties = self.controller.get_county_list()
        CountyFilterPopup(self.root, counties, self.selected_counties, self.apply_county_filter,
                          self.county_filter_button)

    def apply_county_filter(self, selected_counties):
        self.selected_counties = selected_counties
        self.update_table()

    def refresh_table(self):
        for row in self.table.get_children():
            self.table.delete(row)
        sorted_rows = self.sort_rows() if self.sort_column else self.rows
        for row in sorted_rows:
            self.table.insert("", "end", values=row)

    def sort_table(self, column):
        if self.sort_column == column:
            self.sort_order = not self.sort_order
        else:
            self.sort_column = column
            self.sort_order = True
        self.refresh_table()

    def sort_rows(self):
        col_index = self.table["columns"].index(self.sort_column)
        return sorted(
            self.rows,
            key=lambda row: row[col_index] if row[col_index] is not None else "",
            reverse=not self.sort_order,
        )

    def display_fish_count_graph(self, event):
        selected_item = self.table.selection()
        if not selected_item:
            return
        row_values = self.table.item(selected_item, "values")
        dow_number = row_values[0]
        survey_date = row_values[3]
        species_common_name = row_values[4]
        print("Selected Row Data:", row_values)
        lengths = []
        quantities = []
        for fish_data in self.controller.model.fish_data_objects:
            if fish_data.result and fish_data.result.DOWNumber == int(dow_number):
                for survey in fish_data.result.surveys:
                    if survey.surveyDate == survey_date:
                        for abbreviation, length_data in survey.lengths.items():
                            if length_data.species.common_name == species_common_name:
                                lengths = [fc.length for fc in (length_data.fishCount or [])]
                                quantities = [fc.quantity for fc in (length_data.fishCount or [])]
                                break
                break
        print("Graph Data - Lengths:", lengths)
        print("Graph Data - Quantities:", quantities)
        self.ax.clear()
        if not lengths or not quantities:
            self.ax.set_title("No Data Available")
            self.ax.set_xlabel("Length")
            self.ax.set_ylabel("Quantity")
            self.canvas.draw()
            return
        self.ax.bar(lengths, quantities, color="blue")
        self.ax.set_title(f"Fish Count: {species_common_name}")
        self.ax.set_xlabel("Length")
        self.ax.set_ylabel("Quantity")
        self.canvas.draw()

    def export_table(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        rows = [self.table.item(row, "values") for row in self.table.get_children()]
        with open(file_path, "w") as f:
            f.write("DOW Number,County Name,Lake Name,Survey Date,Species,Total Caught,Min Length,Max Length\n")
            for row in rows:
                f.write(",".join(map(str, row)) + "\n")
        messagebox.showinfo("Export Successful", f"Data exported to {file_path}")

