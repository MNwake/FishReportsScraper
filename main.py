from view.main_screen import FishSurveyView
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    from model.model import FishSurveyModel
    from controller.controller import FishSurveyController
    DATA_DIR = "scraper/data/surveys"
    SPECIES_FILE = "scraper/data/fish_species.json"
    model = FishSurveyModel(DATA_DIR, SPECIES_FILE)
    controller = FishSurveyController(model, root, FishSurveyView)
    app = FishSurveyView(root, controller)
    root.mainloop()

