# Jak implementujemy system tapet

# Modele dla tapet
do pliku [models.md](/Wiki/WIKI.md#tabele) dodajemy kolejne klasy.

## Device:
informacja o urządzeniach (np. "mobile", "desktop").
|parametr|opis|
|---|---|
|device_id (PRIMARY KEY)|unikalny identyfikator urządzenia|
|name|nazwa urządzenia (np. "mobile", "desktop")

**Relacje:**
- Jedno device ma wiele kolekcji

## Collection
Kolekcja tapet stworzona przez konkretnego użytkownika. Nie są kolaboracyjne.
|parametr|opis|
|---|---|
|collection_id (PRIMARY KEY)|unikalny identyfikator kolekcji|
|name|nazwa kolekcji|
| user_id (FOREIGN KEY do user)|autor kolekcji|
|device_id (FOREIGN KEY do device)|typ urządzenia powiązanego z kolekcją|

**Relacje:**
- Jeden user może mieć wiele collection. 
- Jedno device może mieć wiele collection.
- Collection posiada dokładnie jednego user i jedno device.

## Wallpaper
Konkretna tapeta. Jest to plik graificzny z obrazem.
|parametr|opis|
|---|---|
 wallpaper_id (PRIMARY KEY)|unikalny identyfikator tapety| 
 name|nazwa tapety|
|resolution|rozdzielczość tapety (np. "1920x1080")|
|path|ścieżka do pliku graficznego na serwerze|
|user_id (FOREIGN KEY do user)|użytkownik, który dodał tapetę|

### Tabela pośrednicząca wallpaper collection
Tabela mówi jakie tapety są w kolekcji
|parametr|
|---|
|wallpaper_id (FOREIGN KEY do wallpaper)|
|colection_id (FOREIGN KEY do collection)|

**Relacje:**
- Jeden user może mieć wiele wallpaper.
- Każda wallpaper jest przypisana do jednego user.

## Color
Tabela przechowująca kolory, którymi oznaczone są tapety.
|parametr|opis|
|---|---|
|color_id (PRIMARY KEY)|unikalny identyfikator koloru|
|name|nazwa koloru (np. "red", "blue")|

### Tabela pośrednicząca Wallpaper Color
|parametr|
|---|
|wallpaper_id (FOREIGN KEY do wallpaper)|
|color_id (FOREIGN KEY do color)|

**Relacje:**
- Wallpaper może mieć wiele color.
- Color może być przypisany do wielu wallpaper.

## Tag
Opcjonalne taki dla tapet.
|parametr|opis|
|---|---|
|tag_id (PRIMARY KEY)|unikalny identyfikator tagu|
|name|nazwa tagu (np. "nature", "abstract")|

### Tabela pośrednicząca wallpaper tag
|parametr|
|---|
|wallpaper_id (FOREIGN KEY do wallpaper)|
|tag_id (FOREIGN KEY do tag)|

**Relacje:**
- Wallpaper może mieć wiele tag.
- Tag może być przypisany do wielu wallpaper.