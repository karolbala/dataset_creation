# Automatyczne tworzenie zbioru danych przestrzennych z wykorzystaniem GIS, OSM i Sentinel-2

## Opis projektu

Projekt polegał na stworzeniu w pełni automatycznego pipeline’u w języku Python, który generuje spójny zbiór danych geoprzestrzennych do zastosowań w analizie przestrzennej lub trenowaniu modeli uczenia maszynowego. Pipeline integruje dane drogowe z OpenStreetMap (przez Overpass API) oraz obrazy satelitarne Sentinel-2 (poprzez OpenEO).

Dane wektorowe są przetwarzane przy użyciu narzędzi GIS: wykonywana jest transformacja współrzędnych (EPSG:2180 ↔ WGS84 ↔ Web Mercator), filtrowanie typów dróg, obliczanie bufora zależnego od kategorii drogi i rasteryzacja geometrii. Równocześnie pobierany jest odpowiadający obraz Sentinel-2, co pozwala na stworzenie pary: **obraz + maska rastrowa**. Tak przygotowane dane mogą być użyte np. do trenowania modeli segmentacji semantycznej.

Projekt działa w pełni automatycznie — generuje losowe obszary w Polsce, pobiera dane, przetwarza je i zapisuje do plików TIFF.

## Technologie

- **Python**
- **GeoPandas** - manipulacja danymi geoprzestrzennymi
- **Rasterio** - rasteryzacja i praca z obrazami rastrowymi
- **PyProj** - transformacje współrzędnych
- **NumPy** - operacje na danych numerycznych
- **Matplotlib** - wizualizacja danych
- **OpenEO** - dostęp do danych satelitarnych Sentinel-2
- **OSM Overpass API** - pobieranie danych drogowych z OpenStreetMap


## Funkcjonalności

- **Pobieranie danych**:
  - Automatyczne pobieranie danych o drogach z OpenStreetMap (OSM) dla zadanych obszarów.
  - Pobieranie obrazów satelitarnych z usługi Sentinel-2 (przez OpenEO API) dla tych samych obszarów.
  
- **Przetwarzanie danych**:
  - Transformacja współrzędnych z EPSG:2180 na WGS84 oraz Web Mercator.
  - Filtrowanie dróg na podstawie typu (np. autostrady, drogi główne).
  - Tworzenie buforów zależnych od typu drogi (dla różnych klas dróg).
  - Rasteryzacja geometrii dróg i tworzenie odpowiadających masek.

- **Wizualizacja**:
  - Wizualizacja wyników w postaci obrazów rastrowych
  -  Wizualizacja pobranych danych dorgowych w postaci obrazów rastrowych na podkładzie mapowym
