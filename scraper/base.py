import threading


class BaseScraper:
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.thread = None
        self.stop = False  # Stop flag

    def update_status(self, message):
        if self.gui_callback:
            self.gui_callback(message)

    def run(self):
        raise NotImplementedError("Subclasses must implement the run() method")

    def start(self):
        self.stop = False  # reset stop flag
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()