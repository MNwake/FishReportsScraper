import tkinter as tk
from tkinter import ttk


class CountyFilterPopup:
    def __init__(self, parent, counties, selected_counties, on_submit, button):
        """
        Initialize the popup.
        :param parent: The parent window.
        :param counties: List of all available counties.
        :param selected_counties: Set of currently selected counties.
        :param on_submit: Callback to apply selected counties.
        :param button: The button widget to anchor the popup window.
        """
        # Create a popup window
        self.top = tk.Toplevel(parent)
        self.top.title("Filter by Counties")
        self.top.transient(parent)  # Makes the popup always on top of the parent
        self.top.overrideredirect(True)  # Removes the window border to make it look integrated

        # Get the button's screen coordinates
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()

        # Position the popup window
        self.top.geometry(f"+{x}+{y}")

        self.counties = counties
        self.selected_counties = selected_counties
        self.on_submit = on_submit

        # Bind to detect clicks outside the popup
        self.top.bind("<FocusOut>", lambda e: self.close_popup())
        self.top.focus_set()  # Set focus to the popup window

        # "Select/Deselect All" checkbox
        self.select_all_var = tk.BooleanVar(value=len(selected_counties) == len(counties))
        select_all_checkbox = ttk.Checkbutton(
            self.top,
            text="Select/Deselect All",
            variable=self.select_all_var,
            command=self.toggle_select_all,
        )
        select_all_checkbox.grid(row=0, column=0, columnspan=5, pady=5, sticky="w")

        # Frame for individual county checkboxes
        self.checkbox_frame = ttk.Frame(self.top)
        self.checkbox_frame.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        self.county_vars = {}
        for index, county in enumerate(sorted(counties)):
            var = tk.BooleanVar(value=county in selected_counties)
            self.county_vars[county] = var
            checkbox = ttk.Checkbutton(self.checkbox_frame, text=county, variable=var)
            row = index // 5  # Determine the row in the grid (5 columns)
            col = index % 5   # Determine the column in the grid
            checkbox.grid(row=row, column=col, padx=5, pady=5, sticky="w")

        # Submit button
        submit_button = ttk.Button(self.top, text="Submit", command=self.submit)
        submit_button.grid(row=2, column=0, columnspan=5, pady=10)

    def toggle_select_all(self):
        """
        Select or deselect all checkboxes based on the "Select/Deselect All" checkbox.
        """
        is_selected = self.select_all_var.get()
        for var in self.county_vars.values():
            var.set(is_selected)

    def submit(self):
        """
        Collect selected counties and pass them to the callback.
        """
        selected = {county for county, var in self.county_vars.items() if var.get()}
        self.on_submit(selected)
        self.close_popup()

    def close_popup(self):
        """
        Destroy the popup window.
        """
        self.top.destroy()

