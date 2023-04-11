<h1 align="center"> babyagi </h1>

# Objetivo

Este script Python é um exemplo de um sistema de gerenciamento de tarefas alimentado por IA. O sistema utiliza as APIs da OpenAI e Pinecone para criar, priorizar e executar tarefas. A ideia principal por trás deste sistema é criar tarefas com base no resultado das tarefas anteriores e em direção a um objetivo predefinido. 

O script usa então os recursos de processamento de linguagem natural (NLP) da OpenAI para criar novas tarefas com base no objetivo e o Pinecone para armazenar e recuperar resultados das  tarefas para o contexto atual. Esta é uma versão simplificada do original [Agente Autônomo Orientado a Tarefas](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 de março de 2023).

Este README abordará o seguinte:

- [Como o script funciona](https://chat.openai.com/chat?model=gpt-4#como-funciona)
- [Como usar o script](https://chat.openai.com/chat?model=gpt-4#como-usar)
- [Modelos suportados](https://chat.openai.com/chat?model=gpt-4#modelos-suportados)
- [Aviso sobre a execução contínua do script](https://chat.openai.com/chat?model=gpt-4#aviso-execucao-continua)

# Como funciona<a name="como-funciona"></a>

Quando iniciado, o script executa um loop infinito que realiza as seguintes funçōes:

1. Pega a primeira tarefa da lista de tarefas.
2. Envia a tarefa para o agente de execução, que usa a API da OpenAI para concluir a tarefa com base no contexto.
3. Enriquece o resultado e armazena-o no Pinecone.
4. Cria novas tarefas e reprioriza a lista de tarefas com base no objetivo e no resultado da tarefa anterior. A função execution_agent() é onde a API da OpenAI é utilizada. Ela recebe dois parâmetros: o objetivo e a tarefa. Em seguida, envia um prompt para a API da OpenAI, que retorna o resultado da tarefa. O prompt consiste em uma descrição da tarefa do sistema de IA, o objetivo e a própria tarefa. O resultado é então retornado como uma string.

A função task_creation_agent() é onde a API da OpenAI é usada para criar novas tarefas com base no objetivo e no resultado da tarefa anterior. A função recebe quatro parâmetros: o objetivo, o resultado da tarefa anterior, a descrição da tarefa e a lista de tarefas atual. Em seguida, envia um prompt para a API da OpenAI, que retorna uma lista de novas tarefas como strings. A função retorna as novas tarefas como uma lista de dicionários, onde cada dicionário contém o nome da tarefa.

A função prioritization_agent() é onde a API da OpenAI é usada para repriorizar a lista de tarefas. A função recebe um parâmetro, o ID da tarefa atual. Envia um prompt para a API da OpenAI, que retorna a lista de tarefas repriorizada como uma lista numerada.

Por fim, o script utilizaPinecone para armazenar e recuperar resultados de tarefas para contexto. O script cria um índice Pinecone com base no nome da tabela especificado na variável YOUR_TABLE_NAME. Pinecone é então usado para armazenar os resultados da tarefa no índice, juntamente com o nome da tarefa e quaisquer metadados adicionais.

# Como usar<a name="como-usar"></a>

Para usar o script, siga estas etapas:

1. Clone o repositório via `git clone https://github.com/yoheinakajima/babyagi.git` e entre no repositório clonado.
2. Instale os pacotes necessários: `pip install -r requirements.txt`
3. Copie o arquivo .env.example para .env: `cp .env.example .env`. É aqui que você definirá as seguintes variáveis.
4. Defina suas chaves de API da OpenAI e Pinecone nas variáveis OPENAI_API_KEY, OPENAPI_API_MODEL e PINECONE_API_KEY.
5. Defina o ambiente Pinecone na variável PINECONE_ENVIRONMENT.
6. Defina o nome da tabela onde os resultados das tarefas serão armazenados na variável TABLE_NAME.
7. (Opcional) Defina o objetivo do sistema de gerenciamento de tarefas na variável OBJECTIVE.
8. (Opcional) Defina a primeira tarefa do sistema na variável INITIAL_TASK.
9. Execute o script.

Todos os valores opcionais acima também podem ser especificados na linha de comando.

# Modelos suportados<a name="modelos-suportados"></a>

Este script funciona com todos os modelos da OpenAI, bem como com Llama através do Llama.cpp. O modelo padrão é **gpt-3.5-turbo**. Para usar um modelo diferente, especifique-o através da OpenAI_API_MODEL ou use a linha de comando.

## Llama

Baixe a versão mais recente do [Llama.cpp](https://github.com/ggerganov/llama.cpp) e siga as instruções para compilá-lo. Você também precisará dos pesos do modelo Llama.

- **Em hipótese alguma compartilhe IPFS, links magnéticos ou quaisquer outros links para downloads de modelos em qualquer lugar neste repositório, incluindo em problemas, discussões ou solicitações pull. Eles serão imediatamente excluídos.**

Depois disso, vincule `llama/main` ao llama.cpp/main e `models` à pasta onde você possui os pesos do modelo Llama. Em seguida, execute o script com `OPENAI_API_MODEL=llama` ou argumento `-l`.

# Aviso<a name="aviso-execucao-continua"></a>

Este script foi projetado para ser executado continuamente como parte de um sistema de gerenciamento de tarefas. Executar este script continuamente pode resultar em alto uso da API, então, por favor, use-o com responsabilidade. Além disso, o script requer que as APIs da OpenAI e Pinecone sejam configuradas corretamente, portanto, certifique-se de ter configurado as APIs antes de executar o script.

# Contribuição

Obviamente, o BabyAGI ainda está em sua infância e, portanto, ainda estamos determinando sua direção e as etapas para chegar lá. Atualmente, um objetivo-chave de design para o BabyAGI é ser *simples* de forma que seja fácil de entender e desenvolver a partir dele. Para manter essa simplicidade, pedimos gentilmente que você siga as seguintes diretrizes ao enviar PRs:

- Concentre-se em modificações pequenas e modulares em vez de refatorações extensas.
- Ao introduzir novos recursos, forneça uma descrição detalhada do caso de uso específico que você está abordando.

Um recado de @yoheinakajima (5 de abril de 2023):

> Eu sei que há um número crescente de PRs, agradeço sua paciência - já que sou novo no GitHub/OpenSource e não planejei adequadamente minha disponibilidade de tempo nesta semana. Re: direção, estive dividido entre manter a simplicidade e expandir - atualmente, estou inclinado a manter um Baby AGI central simples e usar isso como plataforma para apoiar e promover diferentes abordagens para expandir (por exemplo, BabyAGIxLangchain como uma direção). Acredito que existem várias abordagens opinativas que valem a pena explorar, e vejo valor em ter um local central para comparar e discutir. Em breve, mais atualizações.

Sou novo no GitHub e no código aberto, então, por favor, seja paciente enquanto aprendo a gerenciar este projeto adequadamente. Eu gerencio uma empresa de capital de risco durante o dia, então geralmente estarei verificando PRs e problemas à noite depois de colocar meus filhos para dormir - o que pode não ser todas as noites. Estou aberto à ideia de trazer apoio, atualizarei esta seção em breve (expectativas, visões, etc). Estou conversando com muitas pessoas e aprendendo - aguarde atualizações!

# Histórico

BabyAGI é uma versão simplificada do original [Agente Autônomo Orientado a Tarefas](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 de março de 2023) compartilhado no Twitter. Esta versão está reduzida a 140 linhas: 13 comentários, 22 espaços em branco e 105 de código. O nome do repositório surgiu na reação ao agente autônomo original - o autor não pretende insinuar que isso seja AGI.

Feito com amor por [@yoheinakajima](https://twitter.com/yoheinakajima), que por acaso é um VC (adoraria ver o que você está construindo!)

