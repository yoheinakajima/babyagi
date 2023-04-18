# Translations:

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
[<img title="日本語" alt="日本語" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/jp.svg" width="22">](docs/README-ja.md)
[<img title="한국어" alt="한국어" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/kr.svg" width="22">](docs/README-ko.md)

# 목표
이 Python 스크립트는 AI 기반 작업 관리 시스템의 예시입니다. 이 시스템은 OpenAI 및 Pinecone API를 사용하여 작업을 생성하고, 우선순위를 지정하고, 실행합니다. 이 시스템의 기본 아이디어는 이전 작업의 결과와 미리 정의된 목표를 기반으로 작업을 생성한다는 것입니다. 그런 다음 스크립트는 OpenAI의 자연어 처리(NLP) 기능을 사용하여 목표에 따라 새 작업을 생성하고 Pinecone은 컨텍스트에 맞게 작업 결과를 저장 및 검색합니다. 이것은 원래의 [작업 기반 자율 에이전트](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (2023년 3월 28일)를 축소한 버전입니다.

이 README에서는 다음 내용을 다룹니다:

* [스크립트 작동 방식](#how-it-works)

* [스크립트 사용 방법](#how-to-use)

* [지원되는 모델](#supported-models)

* [스크립트 연속 실행에 대한 경고](#continuous-script-warning)
# 작동 방식<a name="how-it-works"></a>
스크립트는 다음 단계를 수행하는 무한 루프를 실행하여 작동합니다:

1. 작업 목록에서 첫 번째 작업을 가져옵니다.
2. 실행 에이전트로 작업을 전송하고, 실행 에이전트는 OpenAI의 API를 사용하여 컨텍스트에 따라 작업을 완료합니다.
3. 결과를 보강하여 Pinecone에 저장합니다.
4. 새 작업을 생성하고 목표와 이전 작업의 결과에 따라 작업 목록의 우선순위를 다시 지정합니다.
</br>
execution_agent() 함수는 OpenAI API가 사용되는 곳입니다. 이 함수는 목표와 작업이라는 두 가지 매개 변수를 받습니다. 그런 다음 OpenAI의 API에 프롬프트를 전송하여 작업의 결과를 반환합니다. prompt는 AI 시스템의 작업, 목표 및 작업 자체에 대한 설명으로 구성됩니다. 그런 다음 결과는 문자열로 반환됩니다.
</br>
task_creation_agent() 함수는 OpenAI의 API를 사용하여 목표와 이전 작업의 결과를 기반으로 새 작업을 생성하는 데 사용됩니다. 이 함수는 목표, 이전 작업의 결과, 작업 설명, 현재 작업 목록의 네 가지 매개 변수를 받습니다. 그런 다음 이 함수는 새 작업 목록을 문자열로 반환하는 OpenAI의 API에 프롬프트를 보냅니다. 그런 다음 이 함수는 새 작업을 사전 목록으로 반환하며, 각 사전에는 작업의 이름이 포함됩니다.
</br>
prioritization_agent() 함수는 작업 목록의 우선순위를 재지정하기 위해 OpenAI의 API를 사용하는 곳입니다. 이 함수는 하나의 매개변수, 즉 현재 작업의 ID를 받습니다. 이 함수는 OpenAI의 API에 프롬프트를 전송하여 우선순위가 재지정된 작업 목록을 번호가 매겨진 목록으로 반환합니다.
</br>
마지막으로, 이 스크립트는 Pinecone을 사용하여 컨텍스트에 맞는 작업 결과를 저장하고 검색합니다. 이 스크립트는 YOUR_TABLE_NAME 변수에 지정된 테이블 이름을 기반으로 Pinecone 인덱스를 생성합니다. 그런 다음 Pinecone을 사용하여 작업 결과를 작업 이름 및 추가 메타데이터와 함께 인덱스에 저장합니다.

# 사용 방법<a name="how-to-use"></a>
스크립트를 사용하려면 다음 단계를 따라야 합니다:

1. `git clone https://github.com/yoheinakajima/babyagi.git`과 `cd`를 통해 리포지토리를 복제하고 복제된 리포지토리에 저장합니다.
2. 필요한 패키지를 설치합니다: `pip install -r requirements.txt`
3. .env.example 파일을 .env에 복사합니다: `cp .env.example .env`. 여기에서 다음 변수를 설정합니다.
4. OPENAI_API_KEY, OPENAPI_API_MODEL, PINECONE_API_KEY 변수에 OpenAI 및 Pinecone API 키를 설정합니다.
5. PINECONE_ENVIRONMENT 변수에서 Pinecone 환경을 설정합니다.
6. 작업 결과가 저장될 테이블의 이름을 TABLE_NAME 변수에 설정합니다.
7. (선택 사항) OBJECTIVE 변수에 작업 관리 시스템의 목적을 설정합니다.
8. (선택 사항) 시스템의 첫 번째 작업을 INITIAL_TASK 변수에 설정합니다.
9. 스크립트를 실행합니다.

위의 모든 옵션 값은 커맨드 라인에서도 지정할 수 있습니다.

# 도커 컨테이너로 실행하기

전제 조건으로 도커와 도커-컴포즈가 설치되어 있어야 합니다. Docker 데스크톱이 가장 간단한 옵션입니다(https://www.docker.com/products/docker-desktop/).

도커 컨테이너로 시스템을 실행하려면 위의 단계에 따라 .env 파일을 설정한 다음 다음을 실행합니다:

```
docker-compose up
```

# 지원되는 모델<a name="supported-models"></a>

이 스크립트는 모든 OpenAI 모델과 Llama.cpp를 통한 Llama에서 작동합니다. 기본 모델은 **gpt-3.5-turbo**입니다. 다른 모델을 사용하려면 OPENAI_API_MODEL을 통해 지정하거나 커맨드 라인을 사용하세요.

## Llama

최신 버전의 [Llama.cpp](https://github.com/ggerganov/llama.cpp)를 다운로드하고 지침에 따라 제작하세요. 또한 Llama 모델 추가 필요합니다.

- **어떠한 경우에도 이슈, 토론 또는 풀 리퀘스트를 포함하여 이 리포지토리의 어느 곳에서도 IPFS, 마그넷 링크 또는 모델 다운로드에 대한 기타 링크를 공유해서는 안 됩니다. 즉시 삭제됩니다.**

그 후 `llama/main`을 llama.cpp/main에 연결하고 `models`을 Llama 모델 가중치가 있는 폴더에 연결합니다. 그런 다음 `OPENAI_API_MODEL=llama` 또는 `-l` 인수를 사용하여 스크립트를 실행합니다.

# 경고<a name="continous-script-warning"></a>
이 스크립트는 작업 관리 시스템의 일부로서 계속적으로 실행되도록 디자인되었습니다. 이 스크립트를 계속 실행하면 API 사용량이 높아질 수 있으므로 책임감 있게 사용하시기 바랍니다. 또한 이 스크립트를 실행하려면 OpenAI 및 Pinecone API가 올바르게 설정되어 있어야 하므로 스크립트를 실행하기 전에 API를 설정했는지 확인하세요.

# 기여
말할 필요도 없이, BabyAGI는 아직 초기 단계에 있으므로 아직 방향과 단계를 결정하고 있습니다. 현재 BabyAGI의 핵심 설계 목표는 이해하기 쉽고 구축하기 쉽도록 *단순하게* 만드는 것입니다. 이러한 단순성을 유지하기 위해 PR을 제출할 때 다음 가이드라인을 준수해 주시기 바랍니다:

* 광범위한 리팩토링보다는 소규모의 모듈식 수정에 집중하세요.
* 새로운 기능을 소개할 때는 구체적인 사용 사례에 대한 자세한 설명을 제공하세요.

[@yoheinakajima](https://twitter.com/yoheinakajima)의 메모 (Apr 5, 2023):

> PR이 점점 많아지고 있다는 것을 알고 있습니다. 저는 GitHub/오픈소스를 처음 접했고, 이번 주에는 그에 따라 시간 계획을 세우지 못했습니다. 기다리고 양해해 주셔서 감사합니다. 방향에 대해 말씀드리자면, 저는 단순하게 유지하는 것과 확장하는 것 사이에서 갈등을 겪어왔습니다. 현재는 BabyAGI의 코어를 단순하게 유지하고, 이를 플랫폼으로 삼아 이를 확장하기 위한 다양한 접근 방식을 지원하고 홍보하는 방향으로 기울고 있습니다(예: BabyAGIxLangchain이 하나의 방향입니다). 저는 탐구할 가치가 있는 다양한 의견 접근 방식이 있다고 생각하며, 이를 비교하고 토론할 수 있는 중심적인 장소를 갖는 것이 가치가 있다고 생각합니다. 곧 더 많은 업데이트가 있을 예정입니다.

저는 GitHub와 오픈소스를 처음 사용하므로 이 프로젝트를 제대로 관리하는 방법을 배우는 동안 조금만 기다려주세요. 저는 낮에는 벤처캐피털 회사를 운영하기 때문에 보통 아이들을 재운 후 밤에 PR과 이슈를 확인하고 있고, 매일 밤 확인하는 것은 아닐 수도 있습니다. 지원을 구하는 아이디어에 열려 있으며 곧 이 섹션을 업데이트할 예정입니다(기대, 비전 등). 많은 사람들과 이야기를 나누며 배우고 있으니 업데이트를 기대해주세요!

# 영감을 받은 프로젝트

출시 이후 짧은 시간 동안 BabyAGI는 많은 프로젝트에 영감을 주었습니다. [여기](inspired-projects.md)에서 모두 확인할 수 있습니다.

# 배경 스토리
BabyAGI는 트위터에 공유된 원본 [작업 기반 자율 에이전트](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)(2023년 3월 28일)의 축소 버전입니다. 이 버전은 140줄로 줄었습니다: 주석 13줄, 공백 22줄, 코드 105줄입니다. 이 리포지토리의 이름은 오리지널 자율 에이전트에 대한 반응에서 나온 것으로, 작성자가 이것이 AGI라는 것을 암시하려는 의도는 아닙니다.

벤처캐피털리스트인 [@yoheinakajima](https://twitter.com/yoheinakajima)가 애정을 담아 만들었습니다(여러분이 만들고 있는 것을 보고 싶습니다!).