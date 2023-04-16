# További fordítások:

[<img title="Français" alt="Français" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/fr.svg" width="22">](./README-fr.md)
[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="22">](./README-pt-br.md)
[<img title="Romanian" alt="Romanian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ro.svg" width="22">](./README-ro.md)
[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="22">](./README-ru.md)
[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="22">](./README-si.md)
[<img title="Spanish" alt="Spanish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/es.svg" width="22">](./README-es.md)
[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="22">](./README-tr.md)
[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="22">](./README-ua.md)
[<img title="简体中文" alt="Simplified Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="22">](./README-cn.md)
[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="22">](./README-zh-tw.md)
[<img title="日本語" alt="日本語" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/jp.svg" width="22">](./README-ja.md)

# Célkitűzés

Ez a Python szkript egy AI-alapú feladatkezelő rendszer példája. A rendszer az OpenAI és a Pinecone API-kat használja feladatok létrehozásához, prioritizálásához és végrehajtásához. A rendszer fő ötlete az, hogy a korábbi feladatok eredményeire és egy előre meghatározott célokra alapozva hozza létre az új feladatokat. A szkript az OpenAI természetes nyelvfeldolgozási (NLP) képességeit használja feladatok létrehozásához, és a Pinecone-t tárolja és visszakeresi a feladatok eredményeit a kontextus miatt. Ez egy lecsupaszított változata az eredeti [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (2023. március 28.) programnak.

Ez az OLVASSEL a következőket foglalja magába:

- [Hogyan működik?](#how-it-works)

- [Hogyan használható?](#how-to-use)

- [Támogatott modellek](#supported-models)

- [Figyelmeztetés a folyamatos futtatásra vonatkozóan](#continous-script-warning)

# Hogyan működik<a name="how-it-works"></a>

A szkript egy végtelen ciklus futtatásával működik, amely a következő lépéseket hajtja végre:

 1. Lekéri az első feladatot a feladatlistából.
 2. Elküldi a feladatot a végrehajtó ügynöknek, amely az OpenAI API-ját használja a feladat teljesítéséhez a kontextus alapján.
 3. Gazdagítja az eredményt, majd tárolja a Pinecone-ban.
 4. Új feladatokat hoz létre és prioritást állít be a feladatlista alapján az objektív és az előző feladat eredménye szerint.
   </br>

A "execution_agent()" funkcióban használjuk az OpenAI API-t ami két paramétert adunk meg: az objektumot és a feladatot. Ezután küld egy lekérdezést az OpenAI API-jához, ami visszaadja az utasítás eredményét. Az lekérdezésre kerülő utasítás tartalmazza az AI rendszer feladatának leírását, az objektumot és magát a feladatot. A választ egy String formátumban kapjuk vissza.
</br>
A "task_creation_agent()" funkcióban az OpenAI API-ját használjuk új lekérdezések és az azokhoz tartozó utasítások létrehozásához az objektum és az előző feladat eredménye alapján. A funkció négy paramétert vár: az objektumot, az előző feladat eredményét, a feladat leírását és a jelenlegi feladatlistát. Ezután küld egy lekérdezést az újonnan létrehozott utasítással az OpenAI API-jához, ami válaszként egy új feladatokból álló listával válaszol szintén String formátumban. A függvény ezután az új feladatokat szótárlistaként adja vissza, ahol minden szótár tartalmazza a feladat nevét.
</br>
A "prioritization_agent()" funkcióban az OpenAI API-ját használjuk a feladatlista prioritizálásához. A funkció egy paramétert vár, ami az aktuális feladat azonosítója. Küld egy lekérdezést az OpenAI API-jához az utasítással, ami válaszként a prioritizált feladatlistát adja vissza számozva.

Végül a szkript használja a Pinecone-t a feladat eredményeinek tárolásához és lekérdezéséhez a kontextusban. A script egy Pinecone indexet hoz létre a YOUR_TABLE_NAME változóban a megadott tábla alapján. A Pinecone ezután a feladat eredményeinek az indexben való tárolására szolgál, a feladat nevével és a további metaadatokkal együtt.

# Hogyan használható?<a name="how-to-use"></a>

A szkript használatához kövesse a következő lépéseket:

1. Klónozza a tárat a `git clone https://github.com/yoheinakajima/babyagi.git` majd a `cd` parancs segítségével lépjen a klónozott tároló mappájába.
2. Telepítse a szükséges csomagokat: `pip install -r requirements.txt`
3. Másolja az .env.example fájlt a .env fájlba: `cp .env.example .env`. Itt állíthatja be a következőkben megadott változókat.
4. Állítsa be az OpenAI és Pinecone API-kulcsokat az OPENAI_API_KEY, OPENAPI_API_MODEL és PINECONE_API_KEY változókban.
5. Állítsa be a Pinecone környezetet a PINECONE_ENVIRONMENT változóban.
6. Adja meg a TABLE_NAME változóban annak a táblának a nevét, ahol a feladat eredményeit tárolni fogja.
7. (Opcionális) Állítsa be a feladatkezelő rendszer célját az OBJEKTÍV változóban.
8. (Opcionális) Állítsa be a rendszer első feladatát az INITIAL_TASK változóban.
9. Futtassa a szkriptet.

Az összes fenti opcionális érték a parancssorban is megadható.


# Futtatás Docker konténeren

Előfeltételként telepítenie kell a `docker`-t és a `docker-compose`-t, ha még nem rendelkezik ezekkel. A Docker asztali verziója a legegyszerűbb lehetőség ezeknek a telepítéséhez https://www.docker.com/products/docker-desktop/

A rendszer docker-tárolón belüli futtatásához állítsa be az `.env` fájlt a fenti lépések szerint, majd futtassa a következőket:

```
docker-compose up
```

# Támogatott modellek<a name="supported-models"></a>

Ez a szkript minden OpenAI modellel működik, valamint a Llama.cpp-n keresztül a Llamával is. Az alapértelmezett modell a **gpt-3.5-turbo**. Másik modell használatához adja meg az OPENAI_API_MODEL segítségével, vagy használja a parancssort.

## Llama

Töltse le a [Llama.cpp](https://github.com/ggerganov/llama.cpp) legújabb verzióját, és kövesse az utasításokat az elkészítéséhez. Szükséged lesz a Llama modellsúlyokra is.

- **Semmilyen körülmények között ne ossza meg az IPFS-t, a mágneses hivatkozásokat vagy a modellletöltésekhez vezető más hivatkozásokat sehol ebben a tárhelyben, beleértve a problémákat, a vitákat vagy a lekérési kéréseket mert azok azonnal törlődnek.**

Ezután kapcsolja össze a `llama/main`-t a llama.cpp/main-hez, a `models`-t pedig ahhoz a mappához, ahol a Llama-modell súlyai vannak. Ezután futtassa a szkriptet `OPENAI_API_MODEL=llama` vagy `-l` argumentummal.

# Figyelmeztetés<a name="continous-script-warning"></a>

Ezt a szkriptet úgy tervezték, hogy a feladatkezelő rendszer részeként folyamatosan futhasson. A szkript folyamatos futtatása magas API-használatot eredményezhet, ezért kérjük, használja felelősségteljesen! Ezenkívül a szkript megköveteli az OpenAI és Pinecone API-k megfelelő beállítását, ezért a szkript futtatása előtt győződjön meg arról, hogy megfelelően beállította a szükséges API-kra vonatkozó beállításokat.

# Hozzájárulás

Mondanunk sem kell, hogy a BabyAGI még gyerekcipőben jár, ezért még mindig meg kell határozzuk a szkript irányát és a lépéseit. Jelenleg a BabyAGI legfontosabb tervezési célja, hogy _egyszerű_, _könnyen érthető_ és _építhető_ legyen. Az egyszerűség megőrzése érdekében kérjük, hogy a PR-ok benyújtásakor tartsa be az alábbi irányelveket:

- A kiterjedt átalakítás helyett a kis, moduláris módosításokra összpontosítson.
- Új funkciók bevezetésekor részletes leírást adjon az Ön által kezelt konkrét használati esetről.

Egy megjegyzés @yoheinakajima-tól (2023. április 5.):

> I know there are a growing number of PRs, appreciate your patience - as I am both new to GitHub/OpenSource, and did not plan my time availability accordingly this week. Re:direction, I've been torn on keeping it simple vs expanding - currently leaning towards keeping a core Baby AGI simple, and using this as a platform to support and promote different approaches to expanding this (eg. BabyAGIxLangchain as one direction). I believe there are various opinionated approaches that are worth exploring, and I see value in having a central place to compare and discuss. More updates coming shortly.

I am new to GitHub and open source, so please be patient as I learn to manage this project properly. I run a VC firm by day, so I will generally be checking PRs and issues at night after I get my kids down - which may not be every night. Open to the idea of bringing in support, will be updating this section soon (expectations, visions, etc). Talking to lots of people and learning - hang tight for updates!

# Inspirált projektek

A megjelenés óta eltelt rövid idő alatt a BabyAGI számos projektet inspirált. Mindegyiket megtekintheti [itt](inspired-projects.md).

# Háttértörténet

A BabyAGI a Twitteren megosztott eredeti [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) kicsinyített változata (2023. március 28.). Ez a verzió 140 soros: 13 megjegyzés, 22 üres és 105 kód. A tároló neve az eredeti autonóm ügynökre adott reakcióban merült fel – a szerző nem azt akarja sugallni, hogy ez az AGI!

Szeretettel készítette [@yoheinakajima](https://twitter.com/yoheinakajima), aki nagyon szívesen látná, mit építesz!
