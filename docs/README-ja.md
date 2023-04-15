# 翻訳:

[<img title="Français" alt="Français" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/fr.svg" width="22">](docs/README-fr.md)
[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="22">](docs/README-pt-br.md)
[<img title="Romanian" alt="Romanian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ro.svg" width="22">](docs/README-ro.md)
[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="22">](docs/README-ru.md)
[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="22">](docs/README-si.md)
[<img title="Spanish" alt="Spanish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/es.svg" width="22">](docs/README-es.md)
[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="22">](docs/README-tr.md)
[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="22">](docs/README-ua.md)
[<img title="简体中文" alt="Simplified Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="22">](docs/README-cn.md)
[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="22">](docs/README-zh-tw.md)

# 目的

このPythonスクリプトは、AIを活用したタスク管理システムの一例です。このシステムは、OpenAIとPinecone APIを使用して、タスクの作成、優先順位付け、および実行を行います。このシステムの主な考え方は、以前のタスクの結果と事前に定義された目的に基づいてタスクを作成することです。その後、スクリプトはOpenAIの自然言語処理（NLP）機能を使って目的に基づいて新しいタスクを作成し、Pineconeでタスクの結果を保存してコンテキストを取得する。これは、オリジナルの[Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023)の縮小版です。

このREADMEでは、次のことを説明します:

- [スクリプトの動作について](#スクリプトの動作について)

- [スクリプトの使用方法について](#使用方法について)

- [サポートされるモデル](#サポートされるモデル)

- [スクリプトの連続実行に関する警告](#連続使用スクリプト警告)

# 仕組みについて<a name="スクリプトの動作について"></a>

このスクリプトは、以下のステップを実行する無限ループによって動作します:

1. タスクリストから最初のタスクを引き出します。
2. タスクを実行エージェントに送り、実行エージェントは OpenAI の API を使用して、コンテキストに基づいてタスクを完了させる。
3. 結果をエンリッチし、Pinecone に保存する。
4. 新しいタスクを作成し、目的と前のタスクの結果に基づいて、タスクリストを再優先化する。
   </br>

execution_agent() 関数は、OpenAI API が使用される場所です。この関数は、目的とタスクという2つのパラメータを受け取ります。そして、OpenAI の API にプロンプトを送信し、タスクの結果を返します。プロンプトは、AI システムのタスクの説明、目的、タスクそのものから構成されています。そして、結果は文字列として返されます。
</br>
task_creation_agent() 関数は、OpenAI の API を使用して、目的と前のタスクの結果に基づいて、新しいタスクを作成するところです。この関数は、目的、前のタスクの結果、タスクの説明、現在のタスクリストという4つのパラメータを受け取ります。そして、OpenAI の API にプロンプトを送信し、新しいタスクのリストを文字列として返します。そして、この関数は、新しいタスクを辞書のリストとして返し、各辞書にはタスクの名前が含まれています。
</br>
prioritization_agent() 関数は、OpenAI の API を使用して、タスクリストの再優先順位を決定するところです。この関数は、現在のタスクの ID を1つのパラメータとして受け取ります。OpenAI の API にプロンプトを送信し、再優先化されたタスクリストを番号付きリストとして返します。

最後に、スクリプトは Pinecone を使用して、コンテキストのためにタスクの結果を保存および取得します。スクリプトは YOUR_TABLE_NAME 変数で指定されたテーブル名に基づいて Pinecone のインデックスを作成します。そして、Pinecone を使用して、タスクの結果をタスク名と追加のメタデータと一緒にインデックスに格納します。

# 使用方法について<a name="使用方法について"></a>

スクリプトを使用するには、次の手順が必要です:

1. `git clone https://github.com/yoheinakajima/babyagi.git` でリポジトリをクローンし、クローンしたリポジトリに `cd` を入れる。
2. 必要なパッケージをインストールします： `pip install -r requirements.txt` を実行します。
3. .env.example ファイルを .env にコピーします： `cp .env.example .env`。ここで、以下の変数を設定します。
4. OPENAI_API_KEY、OPENAPI_API_MODEL、PINECONE_API_KEY 変数に、OpenAI と Pinecone API キーを設定します。
5. PINECONE_ENVIRONMENT 変数に Pinecone の環境を設定します。
6. TABLE_NAME 変数にタスクの結果を保存するテーブルの名前を設定します。
7. （オプション）OBJECTIVE 変数にタスク管理システムの目的を設定します。
8. （オプション）INITIAL_TASK 変数に、システムの最初のタスクを設定する。
9. スクリプトを実行する。

上記のすべてのオプション値は、コマンドラインで指定することも可能です。

# Docker コンテナ内での実行

前提条件として、docker と docker-compose がインストールされている必要があります。Docker desktop は最もシンプルなオプションです https://www.docker.com/products/docker-desktop/

Docker コンテナ内でシステムを実行するには、上記の手順で .env ファイルを設定し、以下を実行します:

```
docker-compose up
```

# サポートされるモデル<a name="サポートされるモデル"></a>

このスクリプトは、OpenAI の全モデルと、Llama.cpp を介した Llama で動作します。デフォルトのモデルは **gpt-3.5-turbo** です。別のモデルを使用するには、OPENAI_API_MODEL で指定するか、コマンドラインを使用します。

## Llama

最新版の [Llama.cpp](https://github.com/ggerganov/llama.cpp) をダウンロードし、指示に従って作成してください。また、Llama モデルのウェイトが必要です。

- **いかなる場合においても、IPFS、マグネットリンク、またはモデルダウンロードへのその他のリンクを、このリポジトリのいかなる場所（issue、discussion または pull request を含む）でも共有しないでください。それらは即座に削除されます。**

その後、`llama/main` を llama.cpp/main に、`models` を Llama モデルのウェイトが入っているフォルダにリンクします。そして、`OPENAI_API_MODEL=llama` または `-l` 引数をつけてスクリプトを実行します。

# 警告<a name="連続使用スクリプト警告"></a>

このスクリプトは、タスク管理システムの一部として連続的に実行されるように設計されています。このスクリプトを連続的に実行すると、API の使用量が多くなることがありますので、責任を持って使用してください。さらに、このスクリプトは OpenAI と Pinecone の API が正しく設定されている必要がありますので、スクリプトを実行する前に API の設定が完了していることを確認してください。

# コントリビュート

言うまでもなく、BabyAGI はまだ初期段階にあり、その方向性とそこに到達するためのステップを決定しているところです。現在、BabyAGI が目指しているのは、「シンプル」であることです。このシンプルさを維持するために、PR を提出する際には、以下のガイドラインを遵守していただくようお願いいたします:

- 大規模なリファクタリングではなく、小規模でモジュール化された修正に重点を置く。
- 新機能を導入する際には、対応する特定のユースケースについて詳細な説明を行うこと。

@yoheinakajima (2023年4月5日)からのメモ:

> 私は GitHub/OpenSource の初心者で、今週は時間的な余裕を計画できていなかったので。現在、Baby AGI のコアをシンプルに保ち、これをプラットフォームとして拡張するためのさまざまなアプローチをサポートし、促進することに傾いています（例えば、BabyAGIxLangchain は一つの方向性です）。私は探求する価値のある様々な意見のアプローチがあると信じていますし、比較し議論するための中心的な場所を持つことに価値があると考えています。近日中にもっと更新します。

私は GitHub とオープンソースに慣れていないので、このプロジェクトを適切に管理できるようになるまで辛抱してください。昼間は VC 会社を経営しているので、PR や issue のチェックはだいたい夜、子供たちを寝かしつけた後に行うことになります（毎晩とは限りませんが）。サポートが必要な場合は、近日中にこのセクションを更新する予定です（期待、ビジョンなど）。多くの人と話し、学んでいます！

# 裏話

BabyAGI は、Twitter でシェアされたオリジナルの [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) を縮小したバージョンです。このバージョンは140行に減っています： コメント13行、空白22行、コード105行です。このリポジトリの名前は、オリジナルの自律型エージェントに対する反応から生まれたもので、作者はこれが AGI であることを意味するものではありません。

偶然にも VC である [@yoheinakajima](https://twitter.com/yoheinakajima) が愛を込めて作っています（みなさんの作っている物も見せてください！）。
