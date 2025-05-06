# Import biblioteki tkinter do tworzenia GUI
import tkinter as tk

# Import dodatkowych komponentów tkinter (okna komunikatów i przewijane pole tekstowe)
from tkinter import messagebox, scrolledtext

# Import biblioteki PIL do pracy z obrazami
from PIL import Image, ImageTk

# Import biblioteki requests do wykonywania zapytań HTTP
import requests

# Import klasy BytesIO do buforowania obrazów w pamięci
from io import BytesIO


# Definicja klasy głównej aplikacji
class NasaImageSearcher:
    # Konstruktor klasy, wywoływany przy tworzeniu obiektu
    def __init__(self, master):
        # Przypisanie głównego okna do zmiennej instancyjnej
        self.master = master

        # Ustawienie tytułu okna
        self.master.title("Wyszukiwarka zdjęć NASA")

        # Ustawienie rozmiaru okna
        self.master.geometry("1000x650")

        # Ustawienie koloru tła okna na czarny
        self.master.configure(bg="black")

        # Ustawienie domyślnego limitu zdjęć do załadowania
        self.limit = 15

        # Wywołanie metody konfigurującej interfejs użytkownika
        self.setup_ui()


    # Metoda konfigurująca interfejs graficzny
    def setup_ui(self):
        # Utworzenie górnej ramki na pole wyszukiwania i przycisk
        self.gora_frame = tk.Frame(self.master, bg="black")
        self.gora_frame.pack(pady=10)

        # Utworzenie pola tekstowego do wpisywania zapytań
        self.pole_wyszukiwania = tk.Entry(
            self.gora_frame, width=50, font=("Consolas", 12),
            fg="green", bg="black", insertbackground="green"
        )
        self.pole_wyszukiwania.pack(side=tk.LEFT, padx=5)

        # Dodanie obsługi klawisza Enter do pola wyszukiwania
        self.pole_wyszukiwania.bind("<Return>", lambda event: self.szukaj_zdjec())

        # Utworzenie przycisku "Szukaj"
        self.przycisk_szukaj = tk.Button(
            self.gora_frame, text="Szukaj", command=self.szukaj_zdjec,
            font=("Consolas", 12), fg="green", bg="black", relief="solid"
        )
        self.przycisk_szukaj.pack(side=tk.LEFT)

        # Utworzenie głównej ramki na wyniki i logi
        self.main_frame = tk.Frame(self.master, bg="black")
        self.main_frame.pack(fill="both", expand=True)

        # Utworzenie płótna (canvas) do przewijania wyników
        self.canvas = tk.Canvas(self.main_frame, bg="black")

        # Utworzenie paska przewijania pionowego
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)

        # Powiązanie paska przewijania z płótnem
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Umieszczenie paska przewijania po lewej stronie
        self.scrollbar.pack(side="left", fill="y")

        # Umieszczenie płótna obok paska przewijania
        self.canvas.pack(side="left", fill="both", expand=True)

        # Utworzenie ramki wewnątrz płótna, gdzie będą wyświetlane miniatury
        self.wynik_frame = tk.Frame(self.canvas, bg="black")

        # Dodanie ramki do płótna jako okno osadzone
        self.canvas.create_window((0, 0), window=self.wynik_frame, anchor="nw")

        # Powiązanie kółka myszy z przewijaniem
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # Ustawienie dynamicznego obszaru przewijania
        self.wynik_frame.bind("<Configure>", self.on_configure)

        # Utworzenie pola tekstowego do logowania zdarzeń
        self.log_box = scrolledtext.ScrolledText(
            self.main_frame, width=40, height=30, state="normal",
            font=("Consolas", 12), fg="green", bg="black", insertbackground="green"
        )
        self.log_box.pack(side="right", padx=10, pady=10, fill="y")


    # Metoda do przewijania zawartości po zmianie rozmiaru
    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    # Metoda do przewijania zawartości kółkiem myszy
    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")


    # Metoda logująca zdarzenia do pola log_box
    def loguj_akcje(self, tekst):
        self.log_box.insert(tk.END, tekst + "\n")
        self.log_box.see(tk.END)


    # Metoda do wyświetlania pełnego zdjęcia w nowym oknie
    def pokaz_pelne_zdjecie(self, url):
        try:
            # Pobranie obrazu z URL
            response = requests.get(url)
            response.raise_for_status()
            img_data = response.content

            # Otworzenie obrazu
            img = Image.open(BytesIO(img_data))

            # Utworzenie nowego okna
            img_window = tk.Toplevel(self.master)
            img_window.title("Pełne zdjęcie")

            # Konwersja obrazu do formatu Tkintera
            full_img = ImageTk.PhotoImage(img)

            # Utworzenie etykiety z obrazem
            label = tk.Label(img_window, image=full_img)
            label.image = full_img  # Zatrzymanie referencji
            label.pack()

            # Logowanie akcji
            self.loguj_akcje("Otworzono pełne zdjęcie.")
        except requests.exceptions.RequestException as e:
            # Obsługa błędu pobierania
            messagebox.showerror("Błąd", f"Nie udało się pobrać pełnego zdjęcia:\n{e}")
            self.loguj_akcje(f"Błąd przy otwieraniu pełnego zdjęcia: {e}")


    # Metoda do pobierania i wyświetlania miniatur NASA
    def szukaj_zdjec(self):
        # Pobranie zapytania z pola tekstowego
        haslo = self.pole_wyszukiwania.get().strip()

        # Jeśli pole jest puste, pokaż ostrzeżenie
        if not haslo:
            messagebox.showwarning("Uwaga", "Wpisz coś, żeby wyszukać.")
            return

        # Logowanie rozpoczęcia wyszukiwania
        self.loguj_akcje(f"Szukanie: {haslo}")

        # Budowanie URL do API NASA
        url = f"https://images-api.nasa.gov/search?q={haslo}&media_type=image"

        try:
            # Wysłanie zapytania HTTP
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Pobranie wyników
            items = data.get("collection", {}).get("items", [])

            # Logowanie liczby znalezionych wyników
            self.loguj_akcje(f"Znaleziono {len(items)} elementów")

            # Usunięcie poprzednich wyników z ramki
            for widget in self.wynik_frame.winfo_children():
                widget.destroy()

            # Konfiguracja siatki
            col_count = 3
            row = 0
            col = 0

            # Iteracja po wynikach (ograniczona limitem)
            for i, item in enumerate(items):
                if i >= self.limit:
                    break

                # Pobranie tytułu i linku do obrazka
                title = item.get("data", [{}])[0].get("title", "Brak tytułu")
                link = item.get("links", [{}])[0].get("href", "")

                # Pomijanie elementów bez obrazka
                if not link:
                    continue

                try:
                    # Pobranie obrazka
                    img_response = requests.get(link)
                    img_response.raise_for_status()
                    img_data = img_response.content

                    # Przetworzenie obrazu
                    img = Image.open(BytesIO(img_data))
                    img.thumbnail((180, 180))
                    photo = ImageTk.PhotoImage(img)

                    # Utworzenie ramki na miniaturę
                    frame = tk.Frame(self.wynik_frame, padx=10, pady=10, bg="black")
                    frame.grid(row=row, column=col, sticky="n")

                    # Utworzenie etykiety z miniaturą
                    img_label = tk.Label(frame, image=photo, cursor="hand2", bg="black")
                    img_label.image = photo
                    img_label.pack()

                    # Powiązanie kliknięcia z otwarciem pełnego zdjęcia
                    img_label.bind("<Button-1>", lambda e, url=link: self.pokaz_pelne_zdjecie(url))

                    # Dodanie tytułu pod miniaturą
                    title_label = tk.Label(
                        frame, text=title, wraplength=180,
                        justify="center", bg="black", fg="green"
                    )
                    title_label.pack()

                    # Aktualizacja siatki
                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1

                    # Logowanie sukcesu
                    self.loguj_akcje(f"Załadowano miniaturę: {title[:40]}...")

                except Exception as e:
                    # Logowanie błędu miniatury
                    self.loguj_akcje(f"Błąd przy ładowaniu miniatury: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            # Obsługa błędu zapytania
            messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")
            self.loguj_akcje(f"Błąd podczas wyszukiwania: {e}")


# Główna część programu - uruchomienie aplikacji
if __name__ == "__main__":
    # Utworzenie głównego okna
    root = tk.Tk()

    # Stworzenie obiektu aplikacji
    app = NasaImageSearcher(root)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()