<h1 align="center">
 babyagi
</h1>

# Objectif

Ce script Python est un exemple de système de gestion de tâches alimenté par l'IA. Le système utilise les API OpenAI et Pinecone pour créer, hiérarchiser et exécuter des tâches. L'idée principale derrière ce système est qu'il crée des tâches en fonction du résultat des tâches précédentes et d'un objectif prédéfini. Le script utilise ensuite les capacités de traitement du langage naturel (NLP) d'OpenAI pour créer de nouvelles tâches en fonction de l'objectif, et Pinecone pour stocker et récupérer les résultats des tâches pour le contexte. Il s'agit d'une version simplifiée du [Task-Driven Autonomous Agent (Agent Autonome Piloté par les Tâches)](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 mars 2023).

Ce fichier README couvrira les éléments suivants :

- [Comment fonctionne le script](#how-it-works)

- [Comment utiliser le script](#how-to-use)

- [Les modèles pris en charge](#supported-models)

- [Avertissement concernant l'exécution continue du script](#continous-script-warning)

# Comment ça marche<a name="how-it-works"></a>

Le script fonctionne en exécutant une boucle infinie qui effectue les étapes suivantes :

1. Récupère la première tâche de la liste des tâches.
2. Envoie la tâche à l'agent d'exécution, qui utilise l'API d'OpenAI pour effectuer la tâche en fonction du contexte.
3. Enrichit le résultat et le stocke dans Pinecone.
4. Crée de nouvelles tâches et réorganise la liste des tâches en fonction de l'objectif et du résultat de la tâche précédente.
</br>

La fonction `execution_agent()` est l'endroit où l'API d'OpenAI est utilisée. Elle prend deux paramètres : l'objectif et la tâche. Ensuite, elle envoie une requête à l'API d'OpenAI, qui renvoie le résultat de la tâche. La requête est constituée d'une description de la tâche du système d'IA, de l'objectif et de la tâche elle-même. Le résultat est ensuite renvoyé sous forme de chaîne de caractères.
</br>

La fonction `task_creation_agent()` est l'endroit où l'API d'OpenAI est utilisée pour créer de nouvelles tâches en fonction de l'objectif et du résultat de la tâche précédente. La fonction prend quatre paramètres : l'objectif, le résultat de la tâche précédente, la description de la tâche et la liste des tâches actuelles. Ensuite, elle envoie une requête à l'API d'OpenAI, qui renvoie une liste de nouvelles tâches sous forme de chaînes de caractères. La fonction renvoie ensuite les nouvelles tâches sous forme d'une liste de dictionnaires, où chaque dictionnaire contient le nom de la tâche.
</br>

La fonction `prioritization_agent()` est l'endroit où l'API d'OpenAI est utilisée pour réorganiser la liste des tâches. La fonction prend un paramètre, l'ID de la tâche actuelle. Elle envoie une requête à l'API d'OpenAI, qui renvoie la liste des tâches réorganisée sous forme d'une liste numérotée.

Enfin, le script utilise Pinecone pour stocker et récupérer les résultats des tâches pour le contexte. Le script crée un index Pinecone basé sur le nom de la table spécifié dans la variable YOUR_TABLE_NAME. Pinecone est ensuite utilisé pour stocker les résultats de la tâche dans l'index, ainsi que le nom de la tâche et tout métadonnées supplémentaires.

# Comment l'utiliser<a name="how-to-use"></a>

Pour utiliser le script, vous devrez suivre les étapes suivantes :

1. Clonez le dépôt en utilisant la commande `git clone https://github.com/yoheinakajima/babyagi.git` et allez dans le répertoire cloné avec la commande `cd babyagi`.
2. Installez les packages requis : `pip install -r requirements.txt`.
3. Copiez le fichier .env.example en .env : cp .env.example .env. C'est là que vous définirez les variables suivantes.
4. Définissez vos clés d'API OpenAI et Pinecone dans les variables OPENAI_API_KEY, OPENAPI_API_MODEL et PINECONE_API_KEY.
5. Définissez l'environnement Pinecone dans la variable PINECONE_ENVIRONMENT.
6. Définissez le nom de la table où les résultats de la tâche seront stockés dans la variable TABLE_NAME.
7. (Optionnel) Définissez l'objectif du système de gestion de tâches dans la variable OBJECTIVE.
8. (Optionnel) Définissez la première tâche du système dans la variable INITIAL_TASK.
9. Exécutez le script.

Toutes les valeurs facultatives ci-dessus peuvent également être spécifiées en ligne de commande.

# Exécution à l'intérieur d'un conteneur Docker.

Assurez-vous d'avoir docker et docker-compose installés. Docker Desktop est l'option la plus simple https://www.docker.com/products/docker-desktop/.

Pour exécuter le système à l'intérieur d'un conteneur Docker, configurez votre fichier .env comme indiqué dans les étapes ci-dessus, puis exécutez ce qui suit :

```
docker-compose up
```

# Les modèles pris en charge<a name="supported-models"></a>

Ce script fonctionne avec tous les modèles OpenAI, ainsi qu'avec Llama via Llama.cpp. Le modèle par défaut est gpt-3.5-turbo. Pour utiliser un modèle différent, spécifiez-le via OPENAI_API_MODEL ou utilisez la ligne de commande.

## Llama

Téléchargez la dernière version de [Llama.cpp](https://github.com/ggerganov/llama.cpp) puis suivez les instructions pour la compiler. Vous aurez également besoin des données pour allimenter le modèle Llama.

- **Ne partagez sous saucun prétexte des liens IPFS, des liens magnet ou tout autre lien de téléchargement de modèles nulle part dans ce dépôt, y compris dans la section 'Issues', les discussions ou les 'pull request'. Ils seront immédiatement supprimés.**

Après cela, liez `llama/main` à `llama.cpp/main` et `models` au dossier où vous avez données du modèle Llama. Ensuite, exécutez le script avec `OPENAI_API_MODEL=llama` ou l'argument `-l`.

# Avertissement<a name="continous-script-warning"></a>

Ce script est conçu pour être exécuté en continu dans le cadre d'un système de gestion de tâches. L'exécution continue de ce script peut entraîner une utilisation élevée de l'API, veuillez donc l'utiliser de manière responsable. De plus, le script nécessite que les API OpenAI et Pinecone soient correctement configurées, veuillez donc vous assurer d'avoir configuré les API avant d'exécuter le script.

# Contribution

Il va sans dire que BabyAGI en est à ses débuts et que nous sommes donc en train de déterminer sa direction et les étapes à suivre. Actuellement, un objectif de conception clé pour BabyAGI est d'être simple de manière à ce qu'il soit facile à comprendre et à développer. Pour maintenir cette simplicité, nous vous demandons gentiment de respecter les directives suivantes lorsque vous soumettez des PR :

- Concentrez-vous sur des modifications modulaires et petites plutôt que sur des changements (refactoring) importants.
- Lorsque vous implémentez de nouvelles fonctionnalités, fournissez une description détaillée du cas d'utilisation spécifique que vous voulez adresser.

Une note de @yoheinakajima (Apr 5th, 2023):

> Je sais qu'il y a de plus en plus de pull requests, j'apprécie votre patience - étant donné que je suis nouveau sur GitHub/OpenSource et que je n'ai pas planifié correctement ma disponibilité cette semaine. En ce qui concerne l'orientation, j'ai été tiraillé entre la volonté de maintenir la simplicité de BabyAGI et celle de l'étendre - je penche actuellement pour la première option, en gardant un noyau central simple pour BabyAGI et en utilisant cela comme une plate-forme pour soutenir et promouvoir différentes approches d'expansion (par exemple, BabyAGIxLangchain comme une direction possible). Je crois qu'il existe différentes approches argumentées qui valent la peine d'être explorées, et je vois de la valeur dans le fait d'avoir un lieu central pour les comparer et en discuter. Plus de mises à jour à venir sous peu.

Je suis nouveau sur GitHub et l'open source, donc veuillez être patient pendant que j'apprends à gérer ce projet correctement. Je dirige une entreprise de capital-risque le jour, donc je vérifierai généralement les PRs et Issues le soir après avoir couché mes enfants - ce qui ne sera peut-être pas tous les soirs. Je suis ouvert à l'idée d'apporter un soutien, je mettrai bientôt à jour cette section (attentes, visions, etc.). Je parle à beaucoup de gens et j'apprends - restez à l'écoute pour les mises à jour !

# Contexte

BabyAGI est a une version simplifiée du [Task-Driven Autonomous Agent (Agent Autonome Piloté par les Tâches)](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 mars 2023) partagé sur Twitter. Cette version ne contient plus que 140 lignes : 13 commentaires, 22 espaces, et 105 lignes de code. Le nom du référentiel est apparu en réaction à l'agent autonome original - l'auteur ne veut pas impliquer que ceci est un AGI.

Fait avec amour par [@yoheinakajima](https://twitter.com/yoheinakajima), qui se trouve être un investisseur (j'aimerais voir ce sur quoi vous travaillez !)