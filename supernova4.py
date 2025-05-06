import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Konfiguracja interfejsu użytkownika
class UIConfig:
    FONT = ("Consolas", 12)
    BG_COLOR = "black"
    FG_COLOR = "green"
    IMAGE_LIMIT = 15

# Komponent logujący zdarzenia
class LogBox(scrolledtext.ScrolledText):
    def __init__(self, parent):
        super().__init__(
            parent, width=40, height=30, font=UIConfig.FONT,
            fg=UIConfig.FG_COLOR, bg=UIConfig.BG_COLOR,
            insertbackground=UIConfig.FG_COLOR, state="normal"
        )
        self.pack(side="right", padx=10, pady=10, fill="y")

    def log(self, text):
        self.insert(tk.END, text + "\n")
        self.see(tk.END)

# Panel górny z polem wyszukiwania i przyciskiem
class SearchPanel(tk.Frame):
    def __init__(self, parent, search_callback):
        super().__init__(parent, bg=UIConfig.BG_COLOR)
        self.pack(pady=10)

        self.entry = tk.Entry(
            self, width=50, font=UIConfig.FONT,
            fg=UIConfig.FG_COLOR, bg=UIConfig.BG_COLOR,
            insertbackground=UIConfig.FG_COLOR
        )
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", lambda e: search_callback())

        self.button = tk.Button(
            self, text="Search", command=search_callback,
            font=UIConfig.FONT, fg=UIConfig.FG_COLOR,
            bg=UIConfig.BG_COLOR, relief="solid"
        )
        self.button.pack(side=tk.LEFT)

    def get_query(self):
        return self.entry.get().strip()

# Komponent wyświetlający wyniki wyszukiwania obrazów
class ImageResults(tk.Frame):
    def __init__(self, parent, log_callback, preview_callback):
        super().__init__(parent, bg=UIConfig.BG_COLOR)
        self.canvas = tk.Canvas(self, bg=UIConfig.BG_COLOR)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="left", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.result_frame = tk.Frame(self.canvas, bg=UIConfig.BG_COLOR)
        self.canvas.create_window((0, 0), window=self.result_frame, anchor="nw")

        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.result_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.pack(fill="both", expand=True)

        self.log = log_callback
        self.preview = preview_callback

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def clear(self):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def display_thumbnails(self, items):
        col_count = 3
        row = col = 0

        for i, item in enumerate(items[:UIConfig.IMAGE_LIMIT]):
            title = item.get("data", [{}])[0].get("title", "No title")
            link = item.get("links", [{}])[0].get("href", "")
            if not link:
                continue

            try:
                img_response = requests.get(link)
                img_response.raise_for_status()
                img_data = img_response.content

                img = Image.open(BytesIO(img_data))
                img.thumbnail((180, 180))
                photo = ImageTk.PhotoImage(img)

                frame = tk.Frame(self.result_frame, padx=10, pady=10, bg=UIConfig.BG_COLOR)
                frame.grid(row=row, column=col, sticky="n")

                img_label = tk.Label(frame, image=photo, cursor="hand2", bg=UIConfig.BG_COLOR)
                img_label.image = photo
                img_label.pack()
                img_label.bind("<Button-1>", lambda e, url=link: self.preview(url))

                title_label = tk.Label(
                    frame, text=title, wraplength=180, justify="center",
                    bg=UIConfig.BG_COLOR, fg=UIConfig.FG_COLOR
                )
                title_label.pack()

                col += 1
                if col >= col_count:
                    col = 0
                    row += 1

                self.log(f"Loaded thumbnail: {title[:40]}...")
            except Exception as e:
                self.log(f"Error loading thumbnail: {e}")

# Główna klasa aplikacji
class NASAImageSearcher:
    def __init__(self, master):
        self.master = master
        self.master.title("NASA Image Searcher")
        self.master.geometry("1000x650")
        self.master.configure(bg=UIConfig.BG_COLOR)

        self.search_panel = SearchPanel(master, self.search_images)
        self.main_frame = tk.Frame(master, bg=UIConfig.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True)

        self.log_box = LogBox(self.main_frame)
        self.image_results = ImageResults(self.main_frame, self.log_box.log, self.show_full_image)

    # Wyświetla pełne zdjęcie w nowym oknie
    def show_full_image(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            img_window = tk.Toplevel(self.master)
            img_window.title("Full Image")
            full_img = ImageTk.PhotoImage(img)
            label = tk.Label(img_window, image=full_img)
            label.image = full_img
            label.pack()

            self.log_box.log("Opened full image.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not fetch full image:\n{e}")
            self.log_box.log(f"Error opening full image: {e}")

    # Obsługuje zapytanie do API NASA i wyświetla wyniki
    def search_images(self):
        query = self.search_panel.get_query()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return

        self.log_box.log(f"Searching for: {query}")
        url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"

        try:
            response = requests.get(url)
            response.raise_for_status()
            items = response.json().get("collection", {}).get("items", [])

            self.log_box.log(f"Found {len(items)} items")
            self.image_results.clear()
            self.image_results.display_thumbnails(items)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.log_box.log(f"Search error: {e}")

# Uruchamia aplikację
if __name__ == "__main__":
    root = tk.Tk()
    app = NASAImageSearcher(root)
    root.mainloop()