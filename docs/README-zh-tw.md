<h1 align="center">
 babyagi

</h1>

# Readme 翻譯

<kbd>[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="22">](docs/README-pt-br.md)</kbd>
<kbd>[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="22">](docs/README-ru.md)</kbd>
<kbd>[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="22">](docs/README-si.md)</kbd>
<kbd>[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="22">](docs/README-tr.md)</kbd>
<kbd>[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="22">](docs/README-ua.md)</kbd>
<kbd>[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="22">](docs/README-zh-tw.md)</kbd>

# 目標

這個 Python 腳本是一個 AI 驅動的任務管理系統的範例。系統使用 OpenAI 和 Pinecone API 來創建、優先排序和執行任務。這個系統的主要概念是根據先前任務的結果和預定義的目標創建任務。腳本接著使用 OpenAI 的自然語言處理（NLP）能力根據目標創建新任務，並使用 Pinecone 存儲和檢索任務結果以獲取上下文。這是原始 [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)（2023 年 3 月 28 日）的簡化版本。

- [腳本如何運作](#工作原理)
- [如何使用腳本](#如何使用)
- [支持的模型](#支持的模型)
- [連續運行腳本的警告](#警告)

此 README 將涵蓋以下內容：

# 工作原理

腳本通過運行一個無限循環來執行以下步驟：

從任務列表中提取第一個任務。
將任務發送到執行代理，該代理使用 OpenAI 的 API 根據上下文完成任務。
豐富結果並將其存儲在 Pinecone 中。
根據目標和先前任務的結果創建新任務並重新排序任務列表。
</br>
`execution_agent()` 函數是使用 OpenAI API 的地方。它需要兩個參數：

1. 目標 (objective)
2. 任務 (task)。

然後將提示發送到 OpenAI 的 API，該 API 返回任務的結果。提示包括 AI 系統任務的描述、目標和任務本身。然後將結果作為 string (字串) 返回。
</br>
`task_creation_agent()` 函數是使用 OpenAI 的 API 根據目標和先前任務的結果創建新任務的地方。該函數需要四個參數：

1. 目標 (objective)
2. 先前任務的結果 (result of the previous task)
3. 任務描述 (task description)
4. 當前任務列表 (current task list)

然後將提示發送到 OpenAI 的 API，該 API 返回一個新任務的 string 列表。然後將新任務作為一個 list of dictionaries (字典列表) 返回，其中每個字典包含任務的名稱。
</br>
`prioritization_agent()` 函數是使用 OpenAI 的 API 重新排序任務列表的地方。該函數需要一個參數，即當前任務的 ID。它將提示發送到 OpenAI 的 API，該 API 以編號列表的形式返回重新排序的任務列表。

最後，腳本使用 Pinecone 存儲和檢索任務結果以獲取上下文。腳本根據 `YOUR_TABLE_NAME` 變數中指定的表名創建一個 Pinecone 索引。然後使用 Pinecone 將任務的結果存儲在索引中，以及任務名稱和任何其他元數據。

# 如何使用

要使用腳本，您需要執行以下步驟：

1. 通過 `git clone https://github.com/yoheinakajima/babyagi.git` 複製存儲庫並 cd 進入複製的存儲庫。
2. 安裝所需的軟件包：`pip install -r requirements.txt`
3. 將 `.env.example` 文件複製到 `.env`：`cp .env.example .env`。這是您將設置以下變數的地方。
4. 在 `OPENAI_API_KEY`, `OPENAPI_API_MODEL` 和 `PINECONE_API_KEY` 變數中設置您的 OpenAI 和 Pinecone API 密鑰。
5. 在 `PINECONE_ENVIRONMENT` 變數中設置 Pinecone 環境。
6. 在 `TABLE_NAME` 變數中設置將存儲任務結果的表名。
7. （可選）在 `OBJECTIVE` 變數中設置任務管理系統的目標。
8. （可選）在 `INITIAL_TASK` 變數中設置系統的第一個任務。
9. 運行腳本。
上述所有可選值也可以在命令行上指定。

# 支持的模型

此腳本適用於所有 OpenAI 模型，以及通過 [Llama.cpp](https://github.com/ggerganov/llama.cpp) 的 Llama。默認模型是 `gpt-3.5-turbo`。要使用其他模型，通過 `OPENAI_API_MODEL` 指定，或使用命令行。

下載 Llama.cpp 的最新版本並按照說明進行製作。您還需要 Llama 模型權重。

- **在任何情況下都不要在此存儲庫中的任何地方共享 IPFS、磁力鏈接 (magnet links) 或模型下載的任何其他鏈接，包括在問題、討論或拉取請求 (PR) 中。它們將立即被刪除。**

之後將 `llama/main` 鏈接到 `llama.cpp/main`，將 `models` 鏈接到您擁有 Llama 模型權重的文件夾。然後使用 `OPENAI_API_MODEL=llama` 或 `-l` 參數運行腳本。

# 警告

此腳本旨在作為任務管理系統的一部分連續運行。連續運行此腳本可能導致高 API 使用率，因此請負起使用責任。此外，腳本要求正確設置 OpenAI 和 Pinecone API，因此在運行腳本之前請確保已設置 API。

# 貢獻

不用說，BabyAGI 仍處於起步階段，因此我們仍在確定其方向和實現的步驟。目前，對於 BabyAGI 的一個關鍵設計目標是保持 _簡單_，以便易於理解和構建。為了保持這種簡單性，當提交 PR 時，請遵循以下準則：

- 專注於小型、模塊化的修改，而不是大規模重構。
- 在引入新功能時，提供有關您正在解決的特定使用案例 (use case) 的詳細描述。

@yoheinakajima（2023 年 4 月 5 日）的一條說明：

> 我知道越來越多的 PR，感謝您的耐心 - 因為我既是 GitHub/OpenSource 的新手，又沒有妥善安排本周的時間。關於方向，我一直在簡單與擴展之間猶豫不決 - 目前傾向於保持核心 Baby AGI 簡單，並使用這個平台來支持和推廣擴展的不同方法（例如 BabyAGIxLangchain 作為一個方向）。我認為有各種有意義的方法值得探索，我認為在一個中心地方進行比較和討論具有價值。即將有更多更新。

我是 GitHub 和開源的新手，所以在我學會如何正確管理這個項目時，請耐心等待。我白天經營一家創投公司，所以晚上在孩子們入睡後我通常會檢查 PR 和問題，這可能不是每天晚上。我們正在考慮引入支持，將很快更新這部分（期望、願景等）。我正在與很多人交流並學習，請耐心等待更新！

# 背景故事

BabyAGI 是原始 [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)（2023 年 3 月 28 日）在 Twitter 上分享的精簡版本。這個版本縮減到了 140 行：13 條註釋、22 個空白和 105 個代碼。存儲庫的名字出現在對原始自主代理的反應中 - 作者並不意味著這是 AGI。

由 [@yoheinakajima](https://twitter.com/yoheinakajima) 製作，他碰巧是一位創投者（很想看到您在打造什麼！）
