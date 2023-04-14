<h1 align="center">
 babyagi

</h1>

# Readme 翻译:

<kbd>[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="22">](docs/README-pt-br.md)</kbd>
<kbd>[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="22">](docs/README-ru.md)</kbd>
<kbd>[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="22">](docs/README-si.md)</kbd>
<kbd>[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="22">](docs/README-tr.md)</kbd>
<kbd>[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="22">](docs/README-ua.md)</kbd>
<kbd>[<img title="Chinese" alt="Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="22">](docs/README-cn.md)</kbd>

# 目标

此 Python 脚本是一个 AI 支持的任务管理系统示例. 该系统使用 OpenAI 和 Pinecone API 创建, 优先级排序和执行任务. 该系统背后的主要思想是基于先前任务的结果和预定义的目标创建任务. 脚本然后使用 OpenAI 的自然语言处理（NLP）能力根据目标创建新任务, 并使用 Pinecone 存储和检索任务结果以获得上下文. 这是原始的[任务驱动的自驱代理](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)（2023 年 3 月 28 日）的简化版本.

README 将涵盖以下内容:

- [脚本如何运行](#how-it-works)

- [如何使用脚本](#how-to-use)

- [支持的模型](#supported-models)

- [关于连续运行脚本的警告](#continous-script-warning)

# 这怎么玩? <a name="how-it-works"></a>

脚本通过运行一个无限循环来工作, 该循环执行以下步骤:

1. 从任务列表中提取第一个任务.
2. 将任务发送给执行代理, 该代理使用 OpenAI API 根据上下文完成任务.
3. 丰润结果并将其存储在 Pinecone 中.
4. 基于目标和前一个任务的结果创建新任务, 并根据优先级对任务列表进行排序.
   </br>

函数 execution_agent()使用 OpenAI API. 它接受两个参数：目标和任务. 然后它向 OpenAI 的 API 发送一个 prompt(提示), 该 API 返回任务的结果. Prompt 包括 AI 系统任务的描述, 目标和任务本身. 结果然后以 string 形式返回.
</br>
task_creation_agent()函数使用 OpenAI API 根据目标和前一个任务的结果创建新任务. 该函数接受 4 个参数：目标, 前一个任务的结果, 任务描述和当前任务列表. 然后它向 OpenAI 的 API 发送一个 prompt, 该 API 返回一个新任务的 string 列表. 函数然后将新任务作为字典列表返回, 其中每个字典包含任务的名称.
</br>
prioritization_agent()函数使用 OpenAI API 对任务列表进行重新排序. 该函数接受一个参数, 即当前任务的 ID. 它向 OpenAI 的 API 发送一个 prompt, 该 API 返回一个重新排序的任务列表(以数字编号).

最后, 脚本使用 Pinecone 存储和检索任务结果以获取上下文. 脚本根据 YOUR_TABLE_NAME 变量中指定的表名创建一个 Pinecone 索引. 然后 Pinecone 将任务结果与任务名称和任何其他元数据(metadata)一起存储在索引中.

# 咋用 <a name="how-to-use"></a>

要使用此脚本, 您需要按照以下步骤操作:

1. 通过 `git clone https://github.com/yoheinakajima/babyagi.git` 克隆 repository(仓库), 然后使用`cd`进入克隆的 repo.
2. 安装所需的包：`pip install -r requirements.txt`
3. 将.env.example 文件复制到.env: `cp .env.example .env`. 在这里, 您将设置以下变量.
4. 在 OPENAI_API_KEY, OPENAPI_API_MODEL 和 PINECONE_API_KEY 变量中设置您的 OpenAI 和 Pinecone API 密钥.
5. 在 PINECONE_ENVIRONMENT 变量中设置 Pinecone 环境.
6. 在 TABLE_NAME 变量中设置存储任务结果的表的名称. 7.（可选）在 OBJECTIVE 变量中设置任务管理系统的目标. 8.（可选）在 INITIAL_TASK 变量中设置系统的第一个任务.
7. 运行脚本.

上面的所有可选值也可以在命令行中指定.

# 支持的模型<a name="supported-models"></a>

此脚本适用于所有 OpenAI 模型, 以及 Llama (通过 Llama.cp). 默认模型是 gpt-3.5-turbo. 要使用不同的模型, 请通过 OPENAI_API_MODEL 指定, 或者使用命令行.

## Llama

下载最新版的[Llama.cpp](https://github.com/ggerganov/llama.cpp) 并按照说明进行编译. 您还需要 Llama 模型的权重.

- **在任何情况下, 都不要在此 repo(仓库)的任何地方（包括问题, 讨论或拉取请求中）分享 IPFS, 磁力链接或任何其他模型下载链接. 它们将立即被删除.**

然后将 `llama/main` 链接到 llama.cpp/main, 将 `models` 链接到存放 Llama 模型权重的文件夹. 接着传入参数 `OPENAI_API_MODEL=llama` 或 `-l` 运行脚本.

# 高能警告<a name="continous-script-warning"></a>

该脚本被设计为作为任务管理系统的一部分持续运行. 持续运行此脚本可能导致 API 的**使用费超高**, 请务必谨慎使用并后果自负. 此外, 脚本需要正确设置 OpenAI 和 Pinecone API, 因此请确保在运行脚本之前已经设置了 API.

# 贡献

不管咋说, BabyAGI 还处于起步阶段, 我们仍在确定其发展方向以及实现目标所需的步骤. 目前, BabyAGI 的一个关键设计目标是保持 **简单**, 以便于理解和构建. 为了保持这种简单性, 我们恳请您在提交 PR 时遵循以下准则：

- 集中于小型, 模块化的修改, 而不是大规模的重构.
- 在引入新功能时, 提供详细的描述, 说明您要解决的具体用例.

@yoheinakajima 发的的小纸条 (Apr 5th, 2023):

> 我知道 PR 的数量在不断增加, 感谢你们的耐心 - 因为我既是 GitHub/OpenSource 的新手, 又没有合理安排本周的时间. Re: 关于发展方向, 我一直在保持简单与扩展之间徘徊 - 目前倾向于保持 核心的 Baby AGI 尽量简单, 并将其作为支持和推广扩展的不同方法的平台（例如, 将 BabyAGIxLangchain 作为一个方向）. 我相信有各种有建设性的方法值得探索, 那么在专门的地方进行比较和讨论能够见证价值的. 更多更新即将到来.

我是 GitHub 和 open source 的新手, 所以请耐心等待, 因为我正在学习如何管理好这个项目. 白天我经营一家风投公司, 所以我通常会在晚上哄娃睡着之后检查 PR 和 issues - 可能不是每个晚上. 我对引入支持的想法持开放态度, 将很快更新这一部分（期望, 愿景等）. 正在与很多人交流学习 - 敬请期待更新！

# 背景故事

BabyAGI 是一个精简版本, 它的原版[Task-Driven Autonomous Agent(任务驱动的自驱代理)](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) 是在 Twitter 分享的(Mar 28, 2023). 这个版本缩减到了 140 行：13 条注释, 22 个空白行, 以及 105 行代码. Repo 的名称源于对原始自驱代理的反馈 - 作者并不是想暗示这就是 AGI.

[@yoheinakajima](https://twitter.com/yoheinakajima)用爱发电创作此 repo, 他碰巧是一位 VC(风险投资人) (很想看看你们在创造什么!)
