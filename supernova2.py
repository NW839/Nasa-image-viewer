# Importowanie niezbędnych modułów
import tkinter as tk  # GUI
from tkinter import messagebox, scrolledtext  # Komunikaty, pole tekstowe z paskiem przewijania
from PIL import Image, ImageTk  # Obsługa obrazów
import requests  # Pobieranie danych z internetu API
from io import BytesIO  # Obsługa strumieni bajtów (dla obrazów)

# Funkcja do logowania działań użytkownika w bocznym panelu
def loguj_akcje(tekst):
    log_box.insert(tk.END, tekst + "\n")  # Dodaje tekst do końca log_box
    log_box.see(tk.END)  # Automatyczne przewijanie do ostatniego wpisu

# Funkcja otwierająca nowe okno z pełnym obrazem po kliknięciu miniatury
def pokaz_pelne_zdjecie(url):
    try:
        response = requests.get(url)  # Pobieranie obrazu z podanego URL
        response.raise_for_status()  # Błąd jeśli kod HTTP nie jest 200
        img_data = response.content  # Pobranie zawartości obrazka

        img = Image.open(BytesIO(img_data))  # Odczytanie obrazu z bajtów
        img_window = tk.Toplevel(okno)  # Nowe okno z obrazem
        img_window.title("Pełne zdjęcie")  # Tytuł okna

        full_img = ImageTk.PhotoImage(img)  # Konwersja do formatu obsługiwanego przez tkinter
        label = tk.Label(img_window, image=full_img)  # Utworzenie etykiety z obrazem
        label.image = full_img  # Przypisanie referencji do obrazu (żeby nie został usunięty przez GC)
        label.pack()  # Dodanie etykiety do okna
        loguj_akcje("Otworzono pełne zdjęcie.")  # Logowanie

    except requests.exceptions.RequestException as e:
        # Obsługa błędów pobierania
        messagebox.showerror("Błąd", f"Nie udało się pobrać pełnego zdjęcia:\n{e}")
        loguj_akcje(f"Błąd przy otwieraniu pełnego zdjęcia: {e}")

# Funkcja odpowiedzialna za wyszukiwanie zdjęć na podstawie wpisanego hasła
def szukaj_zdjec():
    haslo = pole_wyszukiwania.get().strip()  # Pobranie i oczyszczenie wpisanego tekstu
    if not haslo:
        messagebox.showwarning("Uwaga", "Wpisz coś, żeby wyszukać.")  # Ostrzeżenie gdy pole puste
        return

    loguj_akcje(f"Szukanie: {haslo}")  # Logowanie rozpoczęcia wyszukiwania
    url = f"https://images-api.nasa.gov/search?q={haslo}&media_type=image"  # Tworzenie URL do API NASA

    try:
        response = requests.get(url)  # Wysłanie żądania
        response.raise_for_status()  # Obsługa błędów
        data = response.json()  # Przetworzenie odpowiedzi jako JSON

        items = data.get("collection", {}).get("items", [])  # Pobranie listy wyników
        loguj_akcje(f"Znaleziono {len(items)} elementów")  # Logowanie liczby wyników

        for widget in wynik_frame.winfo_children():
            widget.destroy()  # Usunięcie poprzednich wyników

        col_count = 3  # Liczba kolumn do wyświetlenia miniaturek
        row = 0
        col = 0

        for i, item in enumerate(items):  # Iteracja po elementach
            title = item.get("data", [{}])[0].get("title", "Brak tytułu")  # Tytuł zdjęcia
            link = item.get("links", [{}])[0].get("href", "")  # Link do zdjęcia

            if not link:
                continue  # Pominięcie jeśli brak linku

            try:
                img_response = requests.get(link)  # Pobranie miniatury
                img_response.raise_for_status()
                img_data = img_response.content

                img = Image.open(BytesIO(img_data))  # Otwarcie obrazu
                img.thumbnail((180, 180))  # Zmniejszenie do miniaturki
                photo = ImageTk.PhotoImage(img)  # Konwersja do formatu tkintera

                frame = tk.Frame(wynik_frame, padx=10, pady=10, bg="black")  # Ramka wokół miniaturki
                frame.grid(row=row, column=col, sticky="n")  # Umieszczenie w siatce

                img_label = tk.Label(frame, image=photo, cursor="hand2", bg="black")  # Etykieta z obrazem
                img_label.image = photo  # Zapisanie referencji
                img_label.pack()  # Dodanie do ramki

                # Obsługa kliknięcia - otwarcie pełnego zdjęcia
                img_label.bind("<Button-1>", lambda e, url=link: pokaz_pelne_zdjecie(url))

                title_label = tk.Label(frame, text=title, wraplength=180, justify="center", bg="black", fg="green")  # Tytuł zdjęcia
                title_label.pack()  # Dodanie etykiety tytułu

                col += 1  # Przesunięcie do następnej kolumny
                if col >= col_count:
                    col = 0
                    row += 1  # Przejście do nowego wiersza

                loguj_akcje(f"Załadowano miniaturę: {title[:40]}...")  # Logowanie sukcesu

            except Exception as e:
                loguj_akcje(f"Błąd przy ładowaniu miniatury: {e}")  # Obsługa błędów pojedynczego obrazka
                continue

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")  # Komunikat o błędzie
        loguj_akcje(f"Błąd podczas wyszukiwania: {e}")

# Obsługa przewijania za pomocą kółka myszy
def on_mouse_wheel(event):
    canvas.yview_scroll(-1*(event.delta // 120), "units")

# Główne okno aplikacji
okno = tk.Tk()
okno.title("Wyszukiwarka zdjęć NASA")  # Tytuł okna
okno.geometry("1000x650")  # Wymiary okna
okno.configure(bg="black")  # Kolor tła

# Górny pasek z polem wyszukiwania i przyciskiem
gora_frame = tk.Frame(okno, bg="black")
gora_frame.pack(pady=10)

# Pole tekstowe do wpisania zapytania
pole_wyszukiwania = tk.Entry(gora_frame, width=50, font=("Consolas", 12), fg="green", bg="black", insertbackground="green")
pole_wyszukiwania.pack(side=tk.LEFT, padx=5)

# Obsługa klawisza Enter - uruchamia wyszukiwanie
pole_wyszukiwania.bind("<Return>", lambda event: szukaj_zdjec())

# Przycisk "Szukaj"
przycisk_szukaj = tk.Button(gora_frame, text="Szukaj", command=szukaj_zdjec, font=("Consolas", 12), fg="green", bg="black", relief="solid")
przycisk_szukaj.pack(side=tk.LEFT)

# Główna ramka na wyniki i logi
main_frame = tk.Frame(okno, bg="black")
main_frame.pack(fill="both", expand=True)

# Obszar przewijania (canvas) i pasek przewijania
canvas = tk.Canvas(main_frame, bg="black")
scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="left", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Ramka wewnątrz canvas, w której będą wyniki
wynik_frame = tk.Frame(canvas, bg="black")
canvas.create_window((0, 0), window=wynik_frame, anchor="nw")

# Obsługa kółka myszy dla przewijania
canvas.bind_all("<MouseWheel>", on_mouse_wheel)

# Dynamiczne dopasowanie obszaru przewijania do zawartości
def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

wynik_frame.bind("<Configure>", on_configure)

# Pole tekstowe z paskiem przewijania do logowania zdarzeń
log_box = scrolledtext.ScrolledText(main_frame, width=40, height=30, state="normal", font=("Consolas", 12), fg="green", bg="black", insertbackground="green")
log_box.pack(side="right", padx=10, pady=10, fill="y")

# Uruchomienie głównej pętli aplikacji
okno.mainloop()