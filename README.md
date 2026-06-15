# Optymalizator Tras Dronów

System algorytmu genetycznego do optymalizacji tras patrolowych wielu dronów na siatce 2D. Na podstawie zestawu stref docelowych i ograniczeń dronów, silnik ewolucyjny wyznacza zapętlone trasy patrolowe maksymalizujące równomierne pokrycie wszystkich stref jednocześnie.

Potok pracy składa się z trzech etapów: **konfiguracja** scenariusza w edytorze graficznym → **trening** optymalnego rozwiązania przez backend ewolucyjny → **wizualizacja** wyniku jako animowanej symulacji.

---

## Struktura projektu

```
.
├── backend/
│   ├── evolution.py        # Algorytm genetyczny — selekcja, krzyżowanie, mutacja
│   ├── drone.py            # Dataclass drona (pozycja, tickspeed, promień)
│   ├── first_gen.py        # Generator losowej populacji początkowej
│   ├── path_generator.py   # Rozwijanie punktów trasy na komórki ścieżki (linie Bresenhama)
│   ├── json_parser.py      # Odczyt i zapis plików parametrów i symulacji (JSON)
│   └── input_validation.py # Weryfikacja ograniczeń siatki, obiektów i dronów
├── frontend/
│   ├── configuration.py    # GUI PySide6 do budowania plików scenariuszy
│   ├── template.py         # Animacja matplotlib wytrenowanej symulacji
│   └── assets/             # Obrazy interfejsu (drone.png, field.png, …)
└── shared/                 # Folder wymiany plików JSON (dodany do .gitignore)
```

---

## Wymagania

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** — menedżer pakietów i uruchamiacz skryptów

Wszystkie zależności instaluje się z katalogu głównego projektu:

```bash
uv sync
```

| Pakiet | Używany w |
|---|---|
| `PySide6` | `frontend/configuration.py` — GUI edytora scenariuszy |
| `matplotlib` | `frontend/template.py` — animacja symulacji |
| `bresenham` | `backend/path_generator.py` — interpolacja linii ruchu |

---

## Użycie

### Krok 1 — Budowanie scenariusza w edytorze graficznym

Z **katalogu głównego projektu** należy uruchomić edytor konfiguracji:

```bash
uv run frontend/configuration.py
```

Edytor otwiera interaktywną siatkę w ciemnym motywie. Narzędzia dostępne na lewym panelu:

- **Add Field** — zamalowanie komórek tworzących docelowe strefy obserwacji (ortogonalnie połączone regiony są automatycznie grupowane w obiekty)
- **Remove** — usunięcie komórek
- Przeciąganie środkowym przyciskiem myszy przesuwa widok; `Ctrl + Scroll` — przybliża i oddala

Drony dodaje się przez panel **Active Drones** po prawej stronie. Dla każdego drona można ustawić:

| Właściwość | Opis |
|---|---|
| Pos X / Pos Y | Komórka startowa na siatce |
| Speed | Tickspeed — liczba tyknięć symulacji między kolejnymi ruchami (niższa wartość = szybszy ruch) |
| Radius | Promień pokrycia w metryce Czebyszewa (w komórkach) |

Po przygotowaniu scenariusza należy kliknąć **Export to JSON**. W oknie zapisu należy przejść do folderu `shared/` i zapisać plik pod nazwą:

```
parameters_{nazwa}.json
```

`{nazwa}` można wybrać dowolnie — identyfikuje ona dany scenariusz.

---

### Krok 2 — Uruchomienie optymalizatora ewolucyjnego

Należy przejść do folderu `backend/`:

```bash
cd backend
```

Opcjonalnie można otworzyć `evolution.py` i dostosować stałe algorytmu na początku klasy `Evolution`:

```python
self.total_generations      = 100   # liczba pokoleń do wykonania
self.population_size        = 100   # liczba osobników w pokoleniu
self.selection_rate         = 0.5   # frakcja populacji zachowana po selekcji
self.crossover_elitism_rate = 0.2   # prawdopodobieństwo skopiowania genu rodzica wprost
self.mutation_rate          = 0.75  # prawdopodobieństwo pominięcia mutacji dla osobnika
self.mutation_swap_rate     = 0.1   # prawdopodobieństwo zamiany dwóch tras dronów po mutacji
self.mutation_jitter_stdev  = 1.5   # odchylenie standardowe szumu Gaussa w point_jitter
self.tickcount              = 200   # tyknięcia symulacji używane do oceny sprawności
```

Następnie uruchamia się optymalizator, podając wyłącznie nazwę scenariusza — **bez** przedrostka `parameters_` i **bez** rozszerzenia `.json`:

```bash
uv run evolution.py {nazwa}
```

**Przykład:**
```bash
uv run evolution.py miasto
```

Postęp jest wypisywany po każdym pokoleniu:

```
generation 1 best score: 34.21%
generation 2 best score: 41.07%
...
```

Po zakończeniu najlepsze znalezione rozwiązanie jest zapisywane do:

```
shared/simulation_{nazwa}.json
```

---

### Krok 3 — Wizualizacja wyniku

W pliku `frontend/template.py` należy zaktualizować **linię 24**, wskazując na plik symulacji:

```python
# linia 24 — zastąpić simulation_test_1 nazwą scenariusza
json_path = os.path.join(base_path, '..', 'shared', 'simulation_{nazwa}.json')
```

Następnie wizualizator uruchamia się z **katalogu głównego projektu**:

```bash
uv run frontend/template.py
```

Animacja pokazuje drony poruszające się po siatce z historią tras zakodowaną kolorami i półprzezroczystymi nakładkami promienia widzenia. Przycisk **PAUSE / RESUME** wstrzymuje odtwarzanie, a pola wyboru po prawej stronie pozwalają włączać i wyłączać trasy poszczególnych dronów.