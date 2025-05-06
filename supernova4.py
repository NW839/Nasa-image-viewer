# Import modułu tkinter do tworzenia GUI
import tkinter as tk
# Import dodatkowych komponentów z tkinter
from tkinter import messagebox, scrolledtext
# Import modułów do pracy z obrazami
from PIL import Image, ImageTk
# Import modułu do wysyłania żądań HTTP
import requests
# Import modułu do pracy z danymi binarnymi
from io import BytesIO

# Klasa przechowująca konfigurację interfejsu użytkownika
class UIConfig:
    # Ustawienia czcionki
    FONT = ("Consolas", 12)
    # Kolor tła
    BG_COLOR = "black"
    # Kolor tekstu
    FG_COLOR = "green"
    # Limit wyświetlanych obrazów
    IMAGE_LIMIT = 15

# Klasa implementująca pole do logowania zdarzeń
class LogBox(scrolledtext.ScrolledText):
    # Inicjalizacja komponentu
    def __init__(self, parent):
        # Wywołanie konstruktora klasy nadrzędnej
        super().__init__(
            parent, width=40, height=30, font=UIConfig.FONT,
            fg=UIConfig.FG_COLOR, bg=UIConfig.BG_COLOR,
            insertbackground=UIConfig.FG_COLOR, state="normal"
        )
        # Ustawienie pozycji komponentu
        self.pack(side="right", padx=10, pady=10, fill="y")

    # Metoda do dodawania tekstu do logu
    def log(self, text):
        # Wstawienie tekstu na koniec pola
        self.insert(tk.END, text + "\n")
        # Przewinięcie do końca
        self.see(tk.END)

# Klasa panelu wyszukiwania
class SearchPanel(tk.Frame):
    # Inicjalizacja komponentu
    def __init__(self, parent, search_callback):
        # Wywołanie konstruktora klasy nadrzędnej
        super().__init__(parent, bg=UIConfig.BG_COLOR)
        # Ustawienie odstępów
        self.pack(pady=10)

        # Tworzenie pola wprowadzania tekstu
        self.entry = tk.Entry(
            self, width=50, font=UIConfig.FONT,
            fg=UIConfig.FG_COLOR, bg=UIConfig.BG_COLOR,
            insertbackground=UIConfig.FG_COLOR
        )
        # Ustawienie pozycji pola
        self.entry.pack(side=tk.LEFT, padx=5)
        # Powiązanie zdarzenia Enter z funkcją callback
        self.entry.bind("<Return>", lambda e: search_callback())

        # Tworzenie przycisku wyszukiwania
        self.button = tk.Button(
            self, text="Search", command=search_callback,
            font=UIConfig.FONT, fg=UIConfig.FG_COLOR,
            bg=UIConfig.BG_COLOR, relief="solid"
        )
        # Ustawienie pozycji przycisku
        self.button.pack(side=tk.LEFT)

    # Metoda pobierająca zapytanie z pola tekstowego
    def get_query(self):
        # Zwraca wprowadzony tekst bez białych znaków na końcach
        return self.entry.get().strip()

# Klasa wyświetlająca wyniki wyszukiwania obrazów
class ImageResults(tk.Frame):
    # Inicjalizacja komponentu
    def __init__(self, parent, log_callback, preview_callback):
        # Wywołanie konstruktora klasy nadrzędnej
        super().__init__(parent, bg=UIConfig.BG_COLOR)
        # Tworzenie canvas do przewijania
        self.canvas = tk.Canvas(self, bg=UIConfig.BG_COLOR)
        # Tworzenie paska przewijania
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        # Konfiguracja przewijania canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Ustawienie pozycji paska przewijania
        self.scrollbar.pack(side="left", fill="y")
        # Ustawienie pozycji canvas
        self.canvas.pack(side="left", fill="both", expand=True)

        # Tworzenie ramki na wyniki
        self.result_frame = tk.Frame(self.canvas, bg=UIConfig.BG_COLOR)
        # Umieszczenie ramki w canvas
        self.canvas.create_window((0, 0), window=self.result_frame, anchor="nw")

        # Powiązanie zdarzenia scrollowania myszy
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        # Konfiguracja obszaru przewijania
        self.result_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Ustawienie pozycji głównej ramki
        self.pack(fill="both", expand=True)

        # Przypisanie funkcji callback
        self.log = log_callback
        self.preview = preview_callback

    # Obsługa scrollowania myszą
    def _on_mouse_wheel(self, event):
        # Przewijanie w górę lub w dół
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # Czyszczenie wyników
    def clear(self):
        # Usuwanie wszystkich widżetów z ramki wyników
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    # Wyświetlanie miniaturek obrazów
    def display_thumbnails(self, items):
        # Ustawienia siatki
        col_count = 3
        row = col = 0

        # Iteracja przez wyniki wyszukiwania
        for i, item in enumerate(items[:UIConfig.IMAGE_LIMIT]):
            # Pobranie tytułu obrazu
            title = item.get("data", [{}])[0].get("title", "No title")
            # Pobranie linku do obrazu
            link = item.get("links", [{}])[0].get("href", "")
            # Pominięcie jeśli brak linku
            if not link:
                continue

            try:
                # Pobranie obrazu
                img_response = requests.get(link)
                # Sprawdzenie czy odpowiedź jest poprawna
                img_response.raise_for_status()
                # Pobranie danych obrazu
                img_data = img_response.content

                # Otwarcie obrazu przy użyciu PIL
                img = Image.open(BytesIO(img_data))
                # Zmiana rozmiaru na miniaturkę
                img.thumbnail((180, 180))
                # Konwersja na format Tkinter
                photo = ImageTk.PhotoImage(img)

                # Tworzenie ramki na miniaturkę
                frame = tk.Frame(self.result_frame, padx=10, pady=10, bg=UIConfig.BG_COLOR)
                # Umieszczenie ramki w siatce
                frame.grid(row=row, column=col, sticky="n")

                # Tworzenie etykiety z obrazem
                img_label = tk.Label(frame, image=photo, cursor="hand2", bg=UIConfig.BG_COLOR)
                # Zachowanie referencji do obrazu
                img_label.image = photo
                # Ustawienie pozycji etykiety
                img_label.pack()
                # Powiązanie kliknięcia z podglądem pełnego obrazu
                img_label.bind("<Button-1>", lambda e, url=link: self.preview(url))

                # Tworzenie etykiety z tytułem
                title_label = tk.Label(
                    frame, text=title, wraplength=180, justify="center",
                    bg=UIConfig.BG_COLOR, fg=UIConfig.FG_COLOR
                )
                # Ustawienie pozycji etykiety
                title_label.pack()

                # Przejście do następnej kolumny
                col += 1
                # Przejście do następnego wiersza jeśli kolumny się skończyły
                if col >= col_count:
                    col = 0
                    row += 1

                # Logowanie informacji o załadowaniu miniatury
                self.log(f"Loaded thumbnail: {title[:40]}...")
            except Exception as e:
                # Logowanie błędu
                self.log(f"Error loading thumbnail: {e}")

# Główna klasa aplikacji
class NASAImageSearcher:
    # Inicjalizacja aplikacji
    def __init__(self, master):
        # Przypisanie głównego okna
        self.master = master
        # Ustawienie tytułu okna
        self.master.title("NASA Image Searcher")
        # Ustawienie rozmiaru okna
        self.master.geometry("1000x650")
        # Ustawienie koloru tła
        self.master.configure(bg=UIConfig.BG_COLOR)

        # Utworzenie panelu wyszukiwania
        self.search_panel = SearchPanel(master, self.search_images)
        # Utworzenie głównej ramki
        self.main_frame = tk.Frame(master, bg=UIConfig.BG_COLOR)
        # Ustawienie pozycji głównej ramki
        self.main_frame.pack(fill="both", expand=True)

        # Utworzenie pola logu
        self.log_box = LogBox(self.main_frame)
        # Utworzenie panelu wyników
        self.image_results = ImageResults(self.main_frame, self.log_box.log, self.show_full_image)

    # Wyświetlanie pełnego obrazu
    def show_full_image(self, url):
        try:
            # Pobranie obrazu
            response = requests.get(url)
            # Sprawdzenie odpowiedzi
            response.raise_for_status()
            # Otwarcie obrazu
            img = Image.open(BytesIO(response.content))

            # Utworzenie nowego okna
            img_window = tk.Toplevel(self.master)
            # Ustawienie tytułu okna
            img_window.title("Full Image")
            # Konwersja obrazu na format Tkinter
            full_img = ImageTk.PhotoImage(img)
            # Utworzenie etykiety z obrazem
            label = tk.Label(img_window, image=full_img)
            # Zachowanie referencji do obrazu
            label.image = full_img
            # Ustawienie pozycji etykiety
            label.pack()

            # Logowanie informacji
            self.log_box.log("Opened full image.")
        except requests.exceptions.RequestException as e:
            # Wyświetlenie komunikatu o błędzie
            messagebox.showerror("Error", f"Could not fetch full image:\n{e}")
            # Logowanie błędu
            self.log_box.log(f"Error opening full image: {e}")

    # Wyszukiwanie obrazów
    def search_images(self):
        # Pobranie zapytania
        query = self.search_panel.get_query()
        # Sprawdzenie czy zapytanie nie jest puste
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return

        # Logowanie zapytania
        self.log_box.log(f"Searching for: {query}")
        # Budowanie URL do API NASA
        url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"

        try:
            # Wysłanie żądania
            response = requests.get(url)
            # Sprawdzenie odpowiedzi
            response.raise_for_status()
            # Pobranie wyników
            items = response.json().get("collection", {}).get("items", [])

            # Logowanie liczby wyników
            self.log_box.log(f"Found {len(items)} items")
            # Wyczyszczenie poprzednich wyników
            self.image_results.clear()
            # Wyświetlenie nowych wyników
            self.image_results.display_thumbnails(items)
        except requests.exceptions.RequestException as e:
            # Wyświetlenie komunikatu o błędzie
            messagebox.showerror("Error", f"An error occurred: {e}")
            # Logowanie błędu
            self.log_box.log(f"Search error: {e}")

# Uruchomienie aplikacji
if __name__ == "__main__":
    # Utworzenie głównego okna
    root = tk.Tk()
    # Utworzenie instancji aplikacji
    app = NASAImageSearcher(root)
    # Uruchomienie pętli głównej
    root.mainloop()
