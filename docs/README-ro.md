<h1 align="center">
 babyagi

</h1>

# Obiectiv
Acest script Python este un exemplu de sistem de gestionare a sarcinilor alimentat de AI. Sistemul utilizează API-urile OpenAI și Pinecone pentru a crea, prioritiza și executa sarcini. Ideea principală din spatele acestui sistem este de a creea sarcini pe baza rezultatelor sarcinilor anterioare și a unui obiectiv predefinit. Apoi, scriptul utilizează capacitățile de procesare a limbajului natural (NLP) ale OpenAI pentru a crea sarcini noi pe baza obiectivului și a Pinecone pentru a stoca și recupera rezultatele sarcinilor pentru context. Aceasta este o versiune redusă a [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 martie 2023).

Acest README va acoperi următoarele:

* [Cum funcționează scriptul](#cum-functioneaza)

* [Cum se utilizează scriptul](#cum-se-utilizeaza)

* [Modele acceptate](#modele-acceptate)

* [Avertisment despre rularea continuă a scriptului](#avertisment-rulare-continua)
# Cum funcționează <a name="cum-functioneaza"></a>
Scriptul funcționează prin executarea unei bucle infinite care face următorii pași:

1. Extrage prima sarcină din lista de sarcini.
2. Trimite sarcina la agentul de execuție, care utilizează API-ul OpenAI pentru a finaliza sarcina în funcție de context.
3. Îmbogățește rezultatul și îl stochează în Pinecone.
4. Creează noi sarcini și reprioritizează lista de sarcini în funcție de obiectiv și de rezultatul sarcinii anterioare.
Funcția execution_agent() este locul unde se utilizează API-ul OpenAI. Aceasta primește doi parametri: obiectivul și sarcina. Apoi, trimite o solicitare către API-ul OpenAI, care returnează rezultatul sarcinii. Solicitarea constă dintr-o descriere a sarcinii sistemului AI, a obiectivul și a sarcina însași. Rezultatul este apoi returnat sub forma unui șir de caractere.

Funcția task_creation_agent() este locul unde se utilizează API-ul OpenAI pentru a crea sarcini noi în funcție de obiectivul și rezultatul sarcinii anterioare. Funcția primește patru parametri: obiectivul, rezultatul sarcinii anterioare, descrierea sarcinii și lista de sarcini curentă. Apoi, trimite o solicitare către API-ul OpenAI, care returnează o listă de sarcini noi sub formă de șiruri de caractere. Funcția returnează apoi sarcinile noi sub forma unei liste de dicționare, unde fiecare dicționar conține numele sarcinii.

Funcția prioritization_agent() este locul unde se utilizează API-ul OpenAI pentru a reprioritiza lista de sarcini. Funcția primește un singur parametru, ID-ul sarcinii curente. Aceasta trimite o solicitare către API-ul OpenAI, care returnează lista de sarcini reprioritizează sub forma unei liste de numere.

În cele din urmă, scriptul utilizează Pinecone pentru a stoca și recupera rezultatele sarcinilor pentru context. Scriptul creează un index Pinecone bazat pe numele tabelului specificat în variabila YOUR_TABLE_NAME. Pinecone este apoi utilizat pentru a stoca rezultatele sarcinilor în index, împreună cu numele sarcinii și orice metadate suplimentare.

# Cum se utilizează<a name="cum-se-utilizeaza"></a>
Pentru a utiliza acest script, trebuie să faceți următorii pași:

1. Clonați repository-ul folosind comanda `git clone https://github.com/yoheinakajima/babyagi.git` și navigați în directorul clonat cu comanda `cd`.
2. Instalați pachetele necesare: `pip install -r requirements.txt`
3. Copiați fișierul .env.example în .env cu comanda `cp .env.example .env`. Acesta este locul unde veți seta variabilele următoare.
4. Setați-vă cheile API OpenAI și Pinecone în variabilele OPENAI_API_KEY, OPENAPI_API_MODEL și PINECONE_API_KEY.
5. Setați mediul Pinecone în variabila PINECONE_ENVIRONMENT.
6. Setați numele tabelului, unde vor fi stocate rezultatele sarcinilor, în variabila TABLE_NAME.
7. (Opțional) Setați obiectivul sistemului de gestionare a sarcinilor în variabila OBJECTIVE.
8. (Opțional) Setați prima sarcină a sistemului în variabila INITIAL_TASK.
9. Rulați scriptul.

Toate valorile opționale de mai sus pot fi specificate și în linia de comandă.

# Modele acceptate<a name="modele-acceptate"></a>

Acest script funcționează cu toate modelele OpenAI, precum și cu Llama prin intermediul Llama.cpp. Modelul implicit este **gpt-3.5-turbo**. Pentru a utiliza un alt model, specificați-l prin intermediul variabilei OPENAI_API_MODEL sau utilizați linia de comandă.

## Llama

Descărcați ultima versiune a [Llama.cpp](https://github.com/ggerganov/llama.cpp) și urmați instrucțiunile. De asemenea, veți avea nevoie si de ponderile (weights) modelului Llama.

 - **Sub nicio formă să nu partajați IPFS, link-uri magnetice sau orice alte link-uri către descărcări de modele în niciun loc din acest repository, inclusiv în issues, discussions sau pull requests. Acestea vor fi șterse imediat.**

După aceea, legați `llama/main` de llama.cpp/main și `models` de folderul în care aveți ponderile modelului Llama. Apoi rulați scriptul cu `OPENAI_API_MODEL=llama` sau cu argumentul `-l`.

# Avertisment<a name="#avertisment-rulare-continua"></a>
Acest script este conceput să fie rulat continuu ca parte a unui sistem de gestionare a sarcinilor. Rularea continuă a acestui script poate duce la utilizarea ridicată a API-ului, deci vă rugăm să-l utilizați responsabil. În plus, scriptul necesită ca API-urile OpenAI și Pinecone să fie configurate corect, deci asigurați-vă de asta înainte de a rula scriptul.

# Contribuție

Nu mai e nevoie sa spun că BabyAGI este încă în stadiul său incipient, și de aceea încă încercam să-i determinăm direcția și pașii necesari pentru a ajunge acolo. În prezent, un obiectiv de design cheie pentru BabyAGI este să fie *simplu*, astfel încât să fie ușor de înțeles și de dezvoltat pe el. Pentru a menține această simplitate, vă rugăm să respectați următoarele instrucțiuni atunci când trimiteți PR-uri:

* Concentrați-vă pe modificări mici și modulare, în loc să refactorizați extensiv.
* Când introduceți noi funcționalități, furnizați o descriere detaliată a cazului specific pe care îl abordați.

Un mesaj de la @yoheinakajima (5 aprilie 2023):

> Știu că există un număr crescut de PR-uri și vă apreciez răbdarea - sunt nou în GitHub/OpenSource și nu mi-am planificat disponibilitatea timpului corespunzător în această săptămână. Re: direcție: sunt în dubii dacă să păstrez BabyAGI simplu sau să-l extind - în prezent, sunt înclinat să mențin un nucleu de Baby AGI simplu și să-l folosesc ca platformă pentru a susține și promova diferite abordări de extindere a acestuia (de ex. BabyAGIxLangchain ca o direcție). Cred că există diverse abordări opinate care merită explorate și văd valoare în a avea un loc central pentru a le compara și discuta. Mai multe actualizări în curând.
Sunt nou pe GitHub și în lumea open source, deci vă rog să fiți răbdători în timp ce învăț să gestionez acest proiect în mod corespunzător. În timpul zilei, conduc o firmă de capital de risc (VC), astfel încât în general voi verifica PR-urile și problemele noaptea, după ce îmi culc copiii - ceea ce s-ar putea să nu fie în fiecare noapte. Sunt deschis ideii de a aduce suport, voi actualiza această secțiune în curând (așteptări, viziuni, etc.). Vorbind cu mulți oameni și învățând - țineți aproape pentru actualizări!

# Povestea din spate
BabyAGI este o versiune simplificată a originalului [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 martie 2023), fiind distribuit pe Twitter. Această versiune este redusă la 140 de linii de cod: 13 comentarii, 22 blank-uri și 105 linii de cod efectiv. Numele repo-ului a apărut ca o reacție la agentul autonom original - autorul nu intenționează să sugereze că acesta este AGI.

Realizat cu dragoste de [@yoheinakajima](https://twitter.com/yoheinakajima), care se întâmplă să fie un VC (ar fi încântat să vadă ce construiți!)
