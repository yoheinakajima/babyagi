<h1 align="center">
 babyagi
</h1>

# Ziel

Dieses Python-Skript ist ein Beispiel für ein KI-gestütztes Aufgabenverwaltungssystem. Das System verwendet OpenAI und Chroma, um Aufgaben zu erstellen, zu priorisieren und auszuführen. Die Hauptidee hinter diesem System ist, dass es Aufgaben basierend auf dem Ergebnis vorheriger Aufgaben und einem vordefinierten Ziel erstellt. Das Skript verwendet dann die Funktionen zur Verarbeitung natürlicher Sprache (NLP) von OpenAI, um neue Aufgaben basierend auf dem Ziel zu erstellen, und Chroma, um Aufgabenergebnisse für den Kontext zu speichern und abzurufen. Dies ist eine abgespeckte Version des ursprünglichen [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28. März 2023).

Diese README-Datei behandelt Folgendes:

- [Wie das Skript funktioniert](#how-it-works)

- [So verwendet man das Skript](#how-to-use)

- [Unterstützte Modelle](#supported-models)

- [Warnung vor der kontinuierlichen Ausführung des Skripts](#continous-script-warning)

# Wie es funktioniert<a name="how-it-works"></a>

Das Skript funktioniert, indem es eine Endlosschleife ausführt, die die folgenden Schritte abarbeitet:

1. Zieht die erste Aufgabe aus der Aufgabenliste.
2. Sendet die Aufgabe an den Ausführungsagenten, der die API von OpenAI verwendet, um die Aufgabe basierend auf dem Kontext abzuschließen.
3. Reichert das Ergebnis an und speichert es in [Chroma](https://github.com/yoheinakajima/babyagi/blob/main/docs.trychroma.com).
4. Erstellt neue Aufgaben und priorisiert die Aufgabenliste basierend auf dem Ziel und dem Ergebnis der vorherigen Aufgabe neu.
</br>

Die Funktion `execute_agent()` ist die Stelle, an dem die OpenAI-API verwendet wird. Sie benötigt zwei Parameter: das Ziel und die Aufgabe. Anschließend sendet sie eine Eingabeaufforderung an die API von OpenAI, die das Ergebnis der Aufgabe zurückgibt. Die Aufforderung besteht aus einer Beschreibung der Aufgabe des KI-Systems, des Ziels und der Aufgabe selbst. Das Ergebnis wird dann als String zurückgegeben.
</br>

In der Funktion `task_creation_agent()` wird die API von OpenAI verwendet, um neue Aufgaben basierend auf dem Ziel und dem Ergebnis der vorherigen Aufgabe zu erstellen. Die Funktion nimmt vier Parameter entgegen: das Ziel, das Ergebnis der vorherigen Aufgabe, die Aufgabenbeschreibung und die aktuelle Aufgabenliste. Anschließend sendet es eine Eingabeaufforderung an die API von OpenAI, die eine Liste neuer Aufgaben als Zeichenfolgen zurückgibt. Die Funktion gibt dann die neuen Aufgaben als Liste von Wörterbüchern zurück, wobei jedes Wörterbuch den Namen der Aufgabe enthält.
</br>

In der Funktion `prioritization_agent()` wird die API von OpenAI verwendet, um die Aufgabenliste neu zu priorisieren. Die Funktion übernimmt einen Parameter, die ID der aktuellen Aufgabe. Sie sendet eine Eingabeaufforderung an die API von OpenAI, die die neu priorisierte Aufgabenliste als nummerierte Liste zurückgibt.
</br>

Schließlich verwendet das Skript Chroma, um Aufgabenergebnisse für den Kontext zu speichern und abzurufen. Das Skript erstellt eine Chroma-Sammlung basierend auf dem Tabellennamen, der in der Variablen TABLE_NAME angegeben ist. Chroma wird dann verwendet, um die Ergebnisse der Aufgabe zusammen mit dem Aufgabennamen und allen zusätzlichen Metadaten in der Sammlung zu speichern.

# Wie man es benutzt<a name="how-to-use"></a>

Um das Skript zu verwenden, müssen die folgenden Schritte ausgeführt werden:

1. Klone das Repository über den Befehl `git glone https://github.com/yoheinakajima/babyagi.git` und wechsle mit `cd` in das geklonte Repository.
2. Installiere die erforderlichen Pakete: `pip install -r requirements.txt`
3. Kopiere die .env.example-Datei nach .env: `cp .env.example .env`. Hier werden die folgenden Variablen gesetzt.
4. Lege deinen OpenAI-API-Schlüssel in den Variablen OPENAI_API_KEY und OPENAPI_API_MODEL fest.
5. Lege den Namen der Tabelle fest, in der die Aufgabenergebnisse in der Variablen TABLE_NAME gespeichert werden.
6. (Optional) Lege den Namen der BabyAGI-Instanz in der Variablen BABY_NAME fest.
7. (Optional) Lege das Ziel des Task-Management-Systems in der Variablen OBJECTIVE fest.
8. (Optional) Lege die erste Aufgabe des Systems in der Variablen INITIAL_TASK fest.
9. Führe das Skript aus: `python babyagi.py`

Alle obigen optionalen Werte können auch in der Befehlszeile angegeben werden.

# In einem Docker-Container ausführen

Als Voraussetzung müssen Docker und Docker-Compose installiert sein. Docker-Desktop ist die einfachste Option: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

Um das System in einem Docker-Container auszuführen, richte deine .env-Datei wie oben beschrieben ein und führe dann folgenden Befehl aus:

```
docker-compose up
```

# Unterstützte Modelle<a name="supported-models"></a>

Dieses Skript funktioniert mit allen OpenAI-Modellen sowie mit Llama und seinen Variationen über Llama.cpp. Das Standardmodell ist **gpt-3.5-turbo**. Um ein anderes Modell zu verwenden, geben Sie es über LLM_MODEL an oder verwenden Sie die Befehlszeile.

## Llama

Die Llama-Integration erfordert das Paket [Llama.cpp](https://github.com/ggerganov/llama.cpp). Sie benötigen auch die Gewichte des Llama-Modells.

- **Teilen Sie unter keinen Umständen IPFS, magnet-Links oder andere Links zu Modell-Downloads irgendwo in diesem Repository, auch nicht in Issues, Diskussionen oder Pull-Requests. Sie werden umgehend gelöscht.**

Sobald verfügbar, setze die LLAMA_MODEL_PATH auf den Pfad des spezifischen zu verwendenden Modells. Der Einfachheit halber können Sie `models` im BabyAGI-Repo mit dem Ordner verknüpfen, in dem Sie die Llama-Modellgewichte haben. Führen Sie dann das Skript mit dem Argument `LLM_MODEL=llama` oder `-l` aus.

# Warnung<a name="continous-script-warning"></a>

Dieses Skript wurde entwickelt, um als Teil eines Aufgabenverwaltungssystems kontinuierlich ausgeführt zu werden. Die kontinuierliche Ausführung dieses Skripts kann zu einer hohen API-Nutzung führen, gehe also bitte verantwortungsvoll damit um. Darüber hinaus erfordert das Skript die korrekte Einrichtung der OpenAI-API. Stelle also sicher, dass du die API eingerichtet hast, bevor du das Skript ausführst.

# Beiträge

Unnötig zu sagen, dass BabyAGI noch in den Kinderschuhen steckt und wir daher immer noch die Richtung und die Schritte dorthin bestimmen. Derzeit ist es ein wichtiges Designziel für BabyAGI, so einfach zu sein, dass es leicht zu verstehen und darauf aufzubauen ist. Um diese Einfachheit zu wahren, bitten wir, sich beim Einreichen von PRs an die folgenden Richtlinien zu halten:

- Konzentriere dich auf kleine, modulare Modifikationen statt auf umfangreiches Refactoring.
- Gebe bei der Einführung neuer Funktionen eine detaillierte Beschreibung des spezifischen Anwendungsfalls an, der angesprochen wird.

Ein Hinweis von @yoheinakajima (Apr 5th, 2023):

> Ich weiß, dass es eine wachsende Zahl von PRs gibt, danke für Ihre Geduld – da ich neu bei GitHub/OpenSource bin und meine zeitliche Verfügbarkeit diese Woche nicht entsprechend geplant habe. Re:direction, ich war hin- und hergerissen, es einfach zu halten oder zu erweitern – derzeit neige ich dazu, ein Kern-Baby-AGI einfach zu halten und dies als Plattform zu verwenden, um verschiedene Ansätze zur Erweiterung zu unterstützen und zu fördern (z. B. BabyAGIxLangchain als eine Richtung). Ich glaube, dass es verschiedene eigensinnige Ansätze gibt, die es wert sind, erkundet zu werden, und ich sehe Wert darin, einen zentralen Ort zum Vergleichen und Diskutieren zu haben. Weitere Updates folgen in Kürze.

Ich bin neu bei GitHub und Open Source, also haben Sie bitte etwas Geduld, während ich lerne, dieses Projekt richtig zu verwalten. Ich leite tagsüber eine VC-Firma, also überprüfe ich im Allgemeinen nachts PRs und Probleme, nachdem ich meine Kinder ins Bett gebracht habe – was möglicherweise nicht jede Nacht der Fall ist. Offen für die Idee, Unterstützung einzubringen, wird dieser Abschnitt bald aktualisiert (Erwartungen, Visionen usw.). Mit vielen Leuten reden und lernen – bleiben Sie dran für Updates!

# Inspirierte Projekte

In der kurzen Zeit seit der Veröffentlichung hat BabyAGI viele Projekte inspiriert. Sie können [hier](https://github.com/yoheinakajima/babyagi/blob/main/docs/inspired-projects.md) angesehen werden.

# Hintergrundgeschichte

BabyAGI ist eine abgespeckte Version des ursprünglichen [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)(28. März 2023), der auf Twitter geteilt wurde. Diese Version ist auf 140 Zeilen reduziert: 13 Kommentare, 22 Leerzeichen und 105 Code. Der Name des Repos tauchte in der Reaktion auf den ursprünglichen autonomen Agenten auf – der Autor will damit nicht implizieren, dass es sich um AGI handelt.

Mit Liebe gemacht von [@yoheinakajima](https://twitter.com/yoheinakajima), der zufällig ein VC ist (würde gerne sehen, was du baust!)
