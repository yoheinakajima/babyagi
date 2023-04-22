# Cel

Ten skrypt Pythona jest przykładem systemu zarządzania zadaniami napędzanego przez AI. System wykorzystuje API OpenAI i Pinecone do tworzenia zadań, ustalania ich priorytetów i wykonywania. Główną ideą tego systemu jest to, że tworzy on zadania na podstawie wyników poprzednich zadań i predefiniowanego celu. Następnie skrypt wykorzystuje możliwości OpenAI w zakresie przetwarzania języka naturalnego (NLP) do tworzenia nowych zadań w oparciu o cel, a Pinecone do przechowywania i pobierania wyników zadań w kontekście. Jest to okrojona wersja oryginalnego [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 marca 2023).

W tym README zostaną omówione następujące kwestie:

- [Jak działa skrypt](#how-it-works)

- [Jak korzystać ze skryptu](#how-to-use)

- [Obsługiwane modele](#supported-models)

- [Ostrzeżenie przed ciągłym działaniem skryptu](#continous-script-warning)

# Jak działa skrypt<a name="how-it-works"></a>

Skrypt zbudowany jest w formie nieskończonej pętli, która wykonuje następujące czynności:

1. Pobiera pierwsze zadanie z listy zadań.
2. Wysyła zadanie do agenta wykonawczego, który używa API OpenAI do wykonania zadania w oparciu o kontekst.
3. Wzbogaca wynik i zapisuje go w Pinecone.
4. Tworzy nowe zadania i dokonuje repriorytetyzacji listy zadań w oparciu o cel i wynik poprzedniego zadania.
   </br>

Funkcja execution_agent() jest miejscem, w którym wykorzystywane jest API OpenAI. Przyjmuje ona dwa parametry: cel i zadanie. Następnie wysyła monit do API OpenAI, które zwraca wynik zadania. Zachęta składa się z opisu zadania systemu AI, celu oraz samego zadania. Wynik jest następnie zwracany jako ciąg znaków.
</br>
Funkcja task_creation_agent() jest miejscem, w którym API OpenAI jest wykorzystywane do tworzenia nowych zadań na podstawie celu i wyniku poprzedniego zadania. Funkcja przyjmuje cztery parametry: cel, wynik poprzedniego zadania, opis zadania oraz aktualną listę zadań. Następnie wysyła monit do API OpenAI, które zwraca listę nowych zadań jako ciągi znaków. Następnie funkcja zwraca nowe zadania jako listę słowników, gdzie każdy słownik zawiera nazwę zadania.
</br>
Funkcja prioritization_agent() jest miejscem, w którym API OpenAI jest wykorzystywane do zmiany priorytetów na liście zadań. Funkcja przyjmuje jeden parametr, ID bieżącego zadania. Wysyła ona monit do API OpenAI, które zwraca listę zadań do ponownego ustalenia priorytetów w postaci listy numerycznej.

Na koniec skrypt wykorzystuje Pinecone do przechowywania i pobierania wyników zadań w kontekście. Skrypt tworzy indeks Pinecone na podstawie nazwy tabeli określonej w zmiennej YOUR_TABLE_NAME. Pinecone jest następnie używany do przechowywania wyników zadania w indeksie, wraz z nazwą zadania i wszelkimi dodatkowymi metadanymi.

# Jak korzystać ze skryptu<a name="how-to-use"></a>

Aby skorzystać ze skryptu, należy wykonać następujące kroki:

1. Sklonuj repozytorium poprzez `git clone https://github.com/yoheinakajima/babyagi.git` i przejdź (`cd`) do sklonowanego repozytorium.
2. Zainstaluj wymagane pakiety: `pip install -r requirements.txt`.
3. Skopiuj plik .env.example do .env: `cp .env.example .env`. W tym miejscu ustawisz następujące zmienne.
4. Ustaw swoje klucze API OpenAI i Pinecone w zmiennych OPENAI_API_KEY, OPENAPI_API_MODEL oraz PINECONE_API_KEY.
5. Ustaw środowisko Pinecone w zmiennej PINECONE_ENVIRONMENT.
6. Ustaw nazwę tabeli, w której będą przechowywane wyniki zadań w zmiennej TABLE_NAME.
7. (Opcjonalnie) Ustaw cel systemu zarządzania zadaniami w zmiennej OBJECTIVE.
8. (Opcjonalnie) Ustaw pierwsze zadanie systemu w zmiennej INITIAL_TASK.
9. Uruchom skrypt.

Wszystkie powyższe wartości opcjonalne mogą być również określone w linii poleceń.

# Uruchomienie wewnątrz kontenera docker

Jako warunek wstępny, będziesz potrzebował mieć zainstalowany docker i docker-compose. Najprostszą opcją jest docker desktop:  https://www.docker.com/products/docker-desktop/.

Aby uruchomić system wewnątrz kontenera docker, skonfiguruj swój plik .env jak w krokach powyżej, a następnie uruchom poniższe polecenie:

```
docker-compose up
```

# Obsługiwane modele<a name="supported-models"></a>

Ten skrypt działa ze wszystkimi modelami OpenAI, a także z Llama poprzez Llama.cpp. Domyślnym modelem jest **gpt-3.5-turbo**. Aby użyć innego modelu, określ go poprzez parametr OPENAI_API_MODEL lub użyj linii poleceń.

## Llama

Pobierz najnowszą wersję [Llama.cpp](https://github.com/ggerganov/llama.cpp) i postępuj zgodnie z instrukcjami, aby ją zbudować. Do modelu Llama będziesz również potrzebował wag.

- **W żadnym wypadku nie udostępniaj IPFS, linków magnet ani żadnych innych linków do pobierania modeli w tym repozytorium, włączając w to issues, dyskusje i pull requesty. Zostaną one natychmiast usunięte.**

Następnie podlinkuj `llama/main` z llama.cpp/main i `models` do folderu, w którym masz wagi modelu Llama. Następnie uruchom skrypt z argumentem `OPENAI_API_MODEL=llama` lub `-l`.

# Ostrzeżenie<a name="continous-script-warning"></a>

Ten skrypt został zaprojektowany do ciągłego działania jako część systemu zarządzania zadaniami. Uruchomienie tego skryptu w trybie ciągłym może powodować duże zużycie API, więc proszę korzystać z niego w sposób odpowiedzialny. Dodatkowo, skrypt wymaga poprawnego skonfigurowania API OpenAI i Pinecone, dlatego przed uruchomieniem skryptu upewnij się, że skonfigurowałeś te API.

# Twój wkład

Nie trzeba dodawać, że BabyAGI jest wciąż w powijakach i dlatego wciąż określamy jego kierunek i kroki, które należy podjąć, aby go osiągnąć. Obecnie, głównym celem BabyAGI jest bycie _prostym_, tak aby było łatwe do zrozumienia i rozwijania. Aby utrzymać tę prostotę, prosimy o przestrzeganie następujących wytycznych przy wysyłaniu PR-ów:

- Skup się na małych, modularnych modyfikacjach, a nie na rozległych przeróbkach / refaktoryzacji.
- Przy wprowadzaniu nowych funkcji przedstaw szczegółowy opis konkretnego przypadku użycia, do którego się odnosisz.

Uwaga od @yoheinakajima (5. kwietnia 2023):

> Wiem, że jest coraz więcej PR-ów, doceniam waszą cierpliwość - jestem nowy na GitHubie/OpenSource i nie zaplanowałem odpowiednio mojego czasu w tym tygodniu. Re:kierunek, byłem rozdarty w kwestii utrzymania prostoty vs rozszerzania - obecnie skłaniam się ku utrzymaniu prostoty rdzenia Baby AGI i użyciu tego jako platformy do wspierania i promowania różnych podejść do rozszerzania tego (np. BabyAGIxLangchain jako jeden kierunek). Wierzę, że istnieją różne opiniotwórcze podejścia, które są warte zbadania i widzę wartość w posiadaniu centralnego miejsca do porównania i dyskusji. Więcej aktualizacji wkrótce.

Jestem nowy w GitHubie i open source, więc proszę o cierpliwość, gdy będę się uczyć, jak prawidłowo zarządzać tym projektem. W dzień prowadzę firmę VC, więc generalnie będę sprawdzał PR-y i problemy w nocy, po tym jak zejdą mi dzieci - co może nie być codziennością. Jestem otwarty na pomysł wprowadzenia wsparcia, wkrótce będę aktualizował tę sekcję (oczekiwania, wizje, itp.). Rozmawiam z wieloma ludźmi i uczę się - czekajcie na aktualizacje!

# Inne projekty zainspirowane tym projektem

W krótkim czasie od premiery, BabyAGI zainspirowało wiele projektów. Możesz zobaczyć je wszystkie [tutaj](docs/inspired-projects.md).

# Tło

BabyAGI to okrojona wersja oryginalnego [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 marca 2023) udostępnionego na Twitterze. Ta wersja sprowadza się do 140 linii: 13 komentarzy, 22 puste miejsca i 105 kodu. Nazwa repo pojawiła się w reakcji na oryginalnego autonomicznego agenta - autor nie ma zamiaru sugerować, że jest to AGI.

Wykonane z miłością przez [@yoheinakajima](https://twitter.com/yoheinakajima), który tak się składa jest też VC (chętnie zobaczyłbym, co budujesz!).
