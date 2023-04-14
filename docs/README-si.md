<h1 align="center">
 babyagi

</h1>

# Cilj

Ta Python skripta je primer sistema za upravljanje opravil, ki ga poganja AI oz. umetna inteligenca (UI). Sistem uporablja OpenAI-jev API in Pinecone za ustvarjanje in določanje prioritet ter izvajanje nalog. Glavna ideja tega sistema je, da ustvarja naloge na podlagi rezultatov prejšnjih nalog in vnaprej določenega cilja. Skripta nato uporabi obdelavo naravnega jezika (NLP) ponudnika OpenAI za ustvarjanje novih nalog na podlagi cilja ter Pinecone za shranjevanje in pridobivanje rezultatov nalog za kontekst. To je poenostavljena različica izvirnega [avtonomnega agenta, ki temelji na opravilih](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28. marec 2023).

Ta README zajema naslednje:

- [Kako deluje skripta](#how-it-works)

- [Kako uporabljati skripto](#how-to-use)

- [Podprti modeli](#supported-models)

– [Opozorilo o neprekinjenem izvajanju skripte](#continous-script-warning)

# Kako deluje<a name="how-it-works"></a>

Skripta deluje tako, da izvaja neskončno zanko, ki izvaja naslednje korake:

1. Izvleče prvo opravilo s seznama opravil.
2. Pošlje nalogo izvršilnemu posredniku (agentu), ki uporablja API OpenAI za dokončanje naloge glede na kontekst.
3. Obogati rezultat in ga shrani v Pinecone.
4. Ustvari nove naloge in ponovno določi prednost seznama nalog glede na cilj in rezultat prejšnje naloge.
   V funkciji execution_agent() se uporablja OpenAI API. Zajema dva parametra: cilj in nalogo. Nato pošlje poziv API-ju OpenAI, ki vrne rezultat naloge. Poziv je sestavljen iz opisa naloge sistema AI, cilja in same naloge. Rezultat je nato vrnjen kot niz.

Funkcija task_creation_agent() je mesto, kjer se API OpenAI uporablja za ustvarjanje novih nalog na podlagi cilja in rezultata prejšnje naloge. Funkcija ima štiri parametre: cilj, rezultat prejšnje naloge, opis naloge in trenutni seznam nalog. Nato pošlje poziv API-ju OpenAI, ki vrne seznam novih nalog kot nize. Funkcija nato vrne nova opravila kot seznam slovarjev, kjer vsak slovar vsebuje ime opravila.

Funkcija prioritization_agent() je mesto, kjer se API OpenAI uporablja za ponovno določanje prioritet seznama opravil. Funkcija sprejme en parameter, ID trenutne naloge. Pošlje poziv API-ju OpenAI, ki vrne ponovno prednostni seznam opravil kot oštevilčen seznam.

Skripta uporablja Pinecone za shranjevanje in pridobivanje rezultatov nalog za kontekst. Skripta ustvari Pinecone indeks na podlagi imena tabele, določenega v spremenljivki YOUR_TABLE_NAME. Pinecone se nato uporabi za shranjevanje rezultatov opravila v indeksu, skupaj z imenom opravila in vsemi dodatnimi metapodatki.

# Navodila za uporabo<a name="how-to-use"></a>

Za uporabo skripte sledite naslednjim korakom:

1. Klonirajte repozitorij prek `git clone https://github.com/yoheinakajima/babyagi.git` in `cd` v klonirano repozitorij.
2. Namestite zahtevane pakete: `pip install -r requirements.txt`
3. Kopirajte datoteko .env.example v .env: `cp .env.example .env`. Tukaj nastavite naslednje spremenljivke.
4. Nastavite API ključe za OpenAI in Pinecone v spremenljivkah OPENAI_API_KEY, OPENAPI_API_MODEL in PINECONE_API_KEY.
5. Nastavite okolje Pinecone v spremenljivki PINECONE_ENVIRONMENT.
6. V spremenljivki TABLE_NAME nastavite ime tabele, v katero bodo shranjeni rezultati naloge.
7. (Izbirno) Nastavite cilj sistema za upravljanje opravil v spremenljivki OBJECTIVE.
8. (Izbirno) Nastavite prvo nalogo sistema v spremenljivki INITIAL_TASK.
9. Zaženite skripto.

Vse izbirne vrednosti zgoraj lahko podate tudi v ukazni vrstici.

# Podprti modeli<a name="supported-models"></a>

Skripta deluje z vsemi modeli OpenAI, pa tudi z Llamo prek Llama.cpp. Privzeti model je **gpt-3.5-turbo**. Če želite uporabiti drug model, ga določite prek OPENAI_API_MODEL ali uporabite ukazno vrstico (CLI).

## Llama

Prenesite najnovejšo različico [Llama.cpp](https://github.com/ggerganov/llama.cpp) in sledite navodilom za namestitev. Potrebovali boste tudi uteži za model Llama.

- **Pod nobenim pogojem ne delite IPFS, magnetnih povezav ali kakršnih koli drugih povezav do prenosov modelov kjer koli v tem repozitoriju, vključno z vprašanji, razpravami ali pull requesti. Objave bodo nemudoma izbrisane.**

Po tem povežite `llama/main` na llama.cpp/main in `models` v mapo, kjer imate uteži modela Llama. Nato zaženite skripto z argumentom `OPENAI_API_MODEL=llama` ali `-l`.

# Opozorilo<a name="continous-script-warning"></a>

Skripta je zasnovana tako, da se neprekinjeno izvaja kot del sistema za upravljanje opravil. Neprekinjeno izvajanje tega skripta lahko povzroči visoko uporabo API-ja, zato ga uporabljajte odgovorno. Poleg tega skripta zahteva, da sta API-ja OpenAI in Pinecone pravilno nastavljena, zato se prepričajte, da ste nastavili API-je preden zaženete skripto.

# Prispevanje

BabyAGI je še vedno v povojih, zato še vedno določamo njegovo smer in korake. Trenutno je ključni cilj oblikovanja za BabyAGI biti _preprost_, tako da ga je enostavno razumeti in graditi na njem. Da bi ohranili to preprostost, vas vljudno prosimo, da pri oddaji PR-jev upoštevate naslednje smernice:

- Osredotočite se na majhne, modularne spremembe namesto na obsežno preoblikovanje.
- Ko uvajate nove funkcije, navedite podroben opis specifičnega primera uporabe, ki ga obravnavate.

Zapis od @yoheinakajima (5. april 2023):

> I know there are a growing number of PRs, appreciate your patience - as I am both new to GitHub/OpenSource, and did not plan my time availability accordingly this week. Re:direction, I've been torn on keeping it simple vs expanding - currently leaning towards keeping a core Baby AGI simple, and using this as a platform to support and promote different approaches to expanding this (eg. BabyAGIxLangchain as one direction). I believe there are various opinionated approaches that are worth exploring, and I see value in having a central place to compare and discuss. More updates coming shortly.

Sem (@yoheinkajima) nov uporabnik GitHub-a in odprtokodnih programov ter okolja, zato bodite potrpežljivi, da se naučim pravilno upravljati ta projekt. Podnevi vodim podjetje za tvegani kapital, zato bom ponoči, potem ko spravim svoje otroke, na splošno preverjal PR-je in težave – kar morda ne bo vsako noč. Odprt sem za idejo o zagotavljanju podpore, kmalu bom posodobil ta razdelek (pričakovanja, vizije itd.). Pogovarjam se z veliko ljudmi in se še učim – počakajte na novosti!

# Backstory

BabyAGI je poenostavljena različica izvirnega [avtonomnega agenta, ki temelji na opravilih](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28. marec 2023), ki je bil predstavljen na Twitterju. Ta različica ima 140 vrstic: 13 komentarjev, 22 presledkov in 105 kode. Ime repozitorija se je pojavilo kot odziv na prvotnega avtonomnega agenta - avtor ne želi namigovati, da je to AGI (splošna umetna inteligenca).

Z ljubeznijo naredil [@yoheinakajima](https://twitter.com/yoheinakajima), ki je po naključju VC (rad bi videl, kaj gradite!)
