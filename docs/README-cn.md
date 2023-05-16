

# 翻译：


[<img title="عربي" alt="عربي" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/sa.svg" width="30">](docs/README-ar.md)
[<img title="Français" alt="Français" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/fr.svg" width="30">](docs/README-fr.md)
[<img title="Polski" alt="Polski" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/pl.svg" width="30">](docs/README-pl.md)
[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="30">](docs/README-pt-br.md)
[<img title="Romanian" alt="Romanian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ro.svg" width="30">](docs/README-ro.md)
[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="30">](docs/README-ru.md)
[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="30">](docs/README-si.md)
[<img title="Spanish" alt="Spanish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/es.svg" width="30">](docs/README-es.md)
[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="30">](docs/README-tr.md)
[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="30">](docs/README-ua.md)
[<img title="简体中文" alt="Simplified Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="30">](docs/README-cn.md)
[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="30">](docs/README-zh-tw.md)
[<img title="日本語" alt="日本語" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/jp.svg" width="30">](docs/README-ja.md)
[<img title="한국어" alt="한국어" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/kr.svg" width="30">](docs/README-ko.md)
[<img title="Magyar" alt="Magyar" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/hu.svg" width="30">](docs/README-hu.md)
[<img title="فارسی" alt="فارسی" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ir.svg" width="30">](docs/README-fa.md)
[<img title="German" alt="German" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/de.svg" width="30">](docs/README-de.md)
[<img title="Indian" alt="Indian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/in.svg" width="30">](docs/README-in.md)


# 目标

此Python脚本是一个AI加持的任务管理系统示例。该系统使用OpenAI和诸如Chroma或Weaviate这样的向量数据库创建、优先级排序和执行任务。该系统背后的主要思想是基于先前任务的结果和预定义的目标创建任务。脚本然后使用OpenAI的自然语言处理（NLP）能力根据目标创建新任务，并使用Chroma或Weaviate为上下文存储和检索任务结果。这是原始的[任务驱动的自驱代理](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)（2023年3月28日）的简化版本。

README 将涵盖以下内容：

- [脚本如何运行](#how-it-works)

- [如何使用脚本](#how-to-use)

- [支持的模型](#supported-models)

- [关于连续运行脚本的警告](#continous-script-warning)

# 这怎么玩? <a name="how-it-works"></a>

脚本通过运行一个无限循环来执行以下步骤：

1. 从任务列表中提取第一个任务；
1. 将任务发送给执行代理，该代理使用OpenAI API根据上下文完成任务；
1. 完善结果并将其存储在Chroma或Weaviate中；
1. 基于目标和前一个任务的结果创建新任务，并根据优先级对任务列表进行排序。
</br>

<img title="worflow" alt="worflow" src="https://user-images.githubusercontent.com/21254008/235015461-543a897f-70cc-4b63-941a-2ae3c9172b11.png">


函数```execution_agent()```使用了OpenAI API。它接受两个参数：目标和任务。然后它向OpenAI的 API 发送一个 prompt（提示）以获取任务的结果。Prompt包括AI 系统任务的描述、目标和任务本身。结果以字符串的形式返回。
</br>
```task_creation_agent()```函数使用OpenAI API根据目标和前一个任务的结果创建新任务。该函数接受4个参数：目标、前一个任务的结果、任务描述和当前任务列表。然后它向OpenAI的API发送prompt，该API以字符串的形式返回新任务的列表。该函数然后将新任务作为字典列表返回，每个字典包含任务的名称。
</br>
```prioritization_agent()```函数使用OpenAI API对任务列表进行重新排序。该函数接受一个参数，即当前任务的 ID。它向OpenAI API发送prompt，该API返回一个重新排序的任务列表（以数字编号）。

最后，脚本使用Chroma或Weaviate根据上下文存储和检索任务结果。脚本根据TABLE_NAME变量指定的表名创建一个Chroma或Weaviate索引。然后Chroma或Weaviate将任务结果、任务名称和任何其他元数据（metadata）一起存储在索引中。

# 如何使用 <a name="how-to-use"></a>

要使用此脚本，您需要按照以下步骤操作：

1. 通过 `git clone https://github.com/yoheinakajima/babyagi.git` 克隆 repository（仓库），然后使用`cd`进入克隆的 repo；
1. 安装所需的包：`pip install -r requirements.txt`；
1. 将.env.example 文件复制到.env：`cp .env.example .env`。后续变量将在此文件中定义；
1. 使用OPENAI_API_KEY，OPENAPI_API_MODEL设置OpenAI的API密钥。如果需要使用Weaviate，还需要设置[此处](https://github.com/yoheinakajima/babyagi/blob/main/docs/weaviate.md)描述的变量；
1. （可选）设置TABLE_NAME为保存任务结果的表名；
1. （可选）设置OBJECTIVE为任务管理系统的目标；
1. （可选）INITIAL_TASK设置系统的初始任务；
1. 运行脚本：`python babyagi.py`

上面的所有可选值也可以在命令行中指定。

# 在Docker环境执行 <a name="running-inside-a-docker-container"></a>

作为前提，必须安装docker和docker-compose。Docker Desktop是个最简单的选择：https://www.docker.com/products/docker-desktop/。

在Docker容器里执行此系统，首先按照之前的步骤设置好`.env`文件，然后执行该命令：
```bash
docker-compose up
```


# 支持的模型<a name="supported-models"></a>

此脚本适用于所有OpenAI的模型、Llama以及Llama.cpp提供的各种变种模型. 默认模型是gpt-3.5-turbo。要使用不同的模型，请通过LLM_MODEL或者命令行指定。

## Llama

Llama的继承需要安装llama-cpp包。您还需要Llama模型的权重。

- **在任何情况下，都不要在此仓库的任何地方（包括问题，讨论或拉取请求中）分享IPFS、磁力链接或任何其他模型下载链接。它们将立即被删除。**

准备好模型以后，设置LLAMA_MODEL_PATH指向模型的目录以使用他们。方便起见，你可以把BabyAGI仓库啊的`models`链接到Llama模型权重所在的目录。然后以`LLM_MODEL=llama`或者-l参数执行脚本。

# 高能警告<a name="continous-script-warning"></a>

该脚本被设计为作为任务管理系统的一部分持续运行。持续运行此脚本可能导致API的**使用费超高**，请务必谨慎使用并后果自负。此外，脚本需要正确设置OpenAI，因此执行脚本之前需要确保API设置正确。

# 贡献

不管咋说，BabyAGI还处于起步阶段，我们仍在确定其发展方向以及实现目标所需的步骤。目前，BabyAGI的一个关键设计目标是保持**简单**，以便于理解和构建。为了保持这种简单性，我们恳请您在提交PR时遵循以下准则：

- 集中于小型。模块化的修改，而不是大规模的重构；
- 在引入新功能时，提供详细的描述说明您要解决的具体用例。

来自@yoheinakajima的提示（2023年4月5号）：

> 我知道PR的数量在不断增加，感谢你们的耐心 - 因为我既是GitHub/开源的新手，又没有合理安排本周的时间。另：关于发展方向，我一直在保持简单与扩展之间徘徊 - 目前倾向于保持核心的Baby AGI尽量简单，并将其作为支持和推广扩展的不同方法的平台（例如，将 BabyAGIxLangchain作为一个方向）。我相信有各种有建设性的方法值得探索，我也看到了在专门的地方进行比较和讨论的价值。更多的更新即将到来。

我是GitHub和开源的新手，所以请保持耐心因为我正在学习如何管理好这个项目。白天我经营一家风投公司，所以我通常会在晚上哄娃睡着之后检查PR和issues - 可能不是每个晚上。我对引入支持的想法持开放态度，将很快更新这一部分（期望，愿景等）。正在与很多人交流学习 - 敬请期待更新！

# BabyAGI Activity Report<a name="babyagi-activity-report"></a>

为了帮助BabyAGI社区得到这恶搞项目进展的通知，Blueprint AI为BabyAGI开发了一个Github活动的摘要生成器。这个简明的报告包含了BabyAGI过去7天的所有贡献的摘要（持续更新中），这样你可以简单地跟踪最新的开发情况。

请到这里查看过去7天的BabyAGI的活动报告：https://app.blueprint.ai/github/yoheinakajima/babyagi

<img title="report" alt="report" src="https://user-images.githubusercontent.com/334530/235789974-f49d3cbe-f4df-4c3d-89e9-bfb60eea6308.png">

# 受启发的项目

自从发布以来，BabyAGI受到了很多项目的启发。你可以从[这里](https://github.com/yoheinakajima/babyagi/blob/main/docs/inspired-projects.md)看到所有的项目列表。

# 背景故事

BabyAGI是Twitter上分享的（2023年3月28号）它的原版[任务驱动的自驱代理](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)的简单版本。这个版本缩减到了140行：13条注释，22个空白行，以及 105 行代码。该仓库的名称源于对原始自驱代理的反馈 - 作者并不是想暗示这就是AGI。

[@yoheinakajima](https://twitter.com/yoheinakajima)用爱发电创作BabyAGI，他碰巧是一位风险投资人（很想看看你们在创造什么！）
