# Dify 워크플로우 노드 타입 레퍼런스

> ex/ 폴더의 실제 YAML 파일에서 추출한 노드 스키마.
> YAML 작성 시 이 문서를 기준으로 삼는다.

---

## 공통 필드 (모든 노드 공통)

```yaml
id: <고유 식별자>          # 노드 ID. 엣지 source/target 참조에 사용.
type: custom               # 항상 "custom"
position:
  x: <숫자>
  y: <숫자>
data:
  type: <노드타입>         # 아래 타입 목록 참조
  title: <표시 이름>
  desc: <설명>
  selected: false
  _connectedSourceHandleIds: [source]   # 또는 분기 핸들 ID 목록
  _connectedTargetHandleIds: [target]   # 또는 []
  _inParallelHovering: false
  _isEntering: false
```

---

## 노드 타입

### 1. start (시작)

워크플로우 진입점. 사용자 입력 변수를 정의한다.

```yaml
data:
  type: start
  title: 시작
  desc: ''
  variables:
    - variable: <변수명>       # 변수 ID (영문, 스네이크케이스)
      label: <화면 표시명>
      type: text-input         # text-input | paragraph | select | number | file
      required: true
      max_length: 256          # text-input/paragraph에 적용
      options: []              # select 타입일 때 선택지 목록
      # file 타입 추가 필드:
      allowed_file_types:
        - image                # image | document | audio | video
      allowed_file_extensions:
        - .JPG
        - .PNG
        - .PDF
      allowed_file_upload_methods:
        - local_file
        - remote_url
```

**변수 참조 방법**: 다른 노드에서 `{{#start.변수명#}}` 또는 value_selector `[start, 변수명]`

---

### 2. end (종료)

워크플로우 출력. 반환할 변수를 나열한다.

```yaml
data:
  type: end
  title: 종료
  desc: ''
  outputs:
    - variable: <출력변수명>
      value_selector:
        - <소스노드ID>
        - <소스변수명>
```

outputs가 없으면 빈 배열 `[]`로 설정한다.

---

### 3. llm (LLM 호출)

Claude 등 언어 모델을 호출한다.

```yaml
data:
  type: llm
  title: <노드 이름>
  desc: ''
  model:
    provider: bedrock          # bedrock | openai | anthropic
    name: us.anthropic.claude-haiku-4-5-20251001-v1:0
    # 주요 모델명:
    # us.anthropic.claude-haiku-4-5-20251001-v1:0   (빠르고 저렴)
    # us.anthropic.claude-sonnet-4-5-20250929-v1:0  (균형)
    mode: chat
    completion_params:
      max_tokens: 4096         # 최대 64000
      temperature: 0           # 0.0 ~ 1.0
  prompt_template:
    - role: system
      text: <시스템 프롬프트>
    - role: user
      text: '<사용자 프롬프트>
        변수 참조: {{#노드ID.변수명#}}
        지식 참조: {{#context#}}'
  context:
    enabled: false             # knowledge-retrieval 결과 주입 시 true
    variable_selector:
      - <knowledge-retrieval 노드ID>
      - result
  variables: []                # 추가 변수 바인딩 (보통 비워둠)
  vision:
    enabled: false             # 이미지 입력 활성화 시 true
```

---

### 4. code (코드 실행)

Python3 코드를 실행하여 데이터를 가공한다.

```yaml
data:
  type: code
  title: <노드 이름>
  desc: ''
  code_language: python3
  code: |
    def main(<입력변수1>, <입력변수2>):
        # 로직
        return {
            '<출력키1>': <값>,
            '<출력키2>': <값>
        }
  variables:
    - variable: <입력변수명>   # main() 파라미터명과 일치해야 함
      value_selector:
        - <소스노드ID>
        - <소스변수명>
  outputs:
    <출력키1>:
      type: string             # string | number | array[string] | object
    <출력키2>:
      type: number
```

**주의**: `code` 필드의 문자열은 YAML 멀티라인 또는 이스케이프 처리 필요.

---

### 5. if-else (조건 분기)

조건에 따라 분기한다.

```yaml
data:
  type: if-else
  title: <노드 이름>
  desc: ''
  cases:
    - case_id: <분기ID>        # 핸들 ID와 일치해야 함 (예: anomaly_detected)
      conditions:
        - variable_selector:
            - <소스노드ID>
            - <변수명>
          comparison_operator: is   # is | is not | contains | not contains
                                    # = | ≠ | > | < | ≥ | ≤
          value: 'true'             # 비교값 (문자열)
      logical_operator: and         # and | or
  _targetBranches:
    - id: <분기ID>
      name: IF
    - id: 'false'
      name: ELSE
  _connectedSourceHandleIds:
    - <분기ID>
    - 'false'
```

**엣지 연결**: 각 분기 핸들 ID를 sourceHandle로 사용.

---

### 6. template-transform (템플릿 변환)

Jinja2 템플릿으로 텍스트를 포맷팅한다.

```yaml
data:
  type: template-transform
  title: <노드 이름>
  desc: ''
  template: |
    텍스트 내용
    {{ 변수명 }}
    {% if 조건 %}분기{% endif %}
  variables:
    - variable: <변수명>       # template에서 {{ 변수명 }}으로 참조
      value_selector:
        - <소스노드ID>
        - <소스변수명>
  outputs:
    output:
      type: string
      children: null
```

---

### 7. parameter-extractor (파라미터 추출)

LLM으로 비정형 텍스트에서 구조화된 데이터를 추출한다.

```yaml
data:
  type: parameter-extractor
  title: <노드 이름>
  desc: ''
  model:
    provider: bedrock
    name: us.anthropic.claude-haiku-4-5-20251001-v1:0
    mode: chat
    completion_params:
      max_tokens: 4096
  instruction: <추출 지시문>
  parameters:
    - name: <파라미터명>       # 추출할 필드명
      type: string             # string | number | boolean | array[string]
      description: <설명>
      required: true
  query:                       # 입력 컨텍스트 (value_selector 배열의 배열)
    - - <소스노드ID>
      - <변수명>
  reasoning_mode: function_call  # function_call 권장
  vision:
    enabled: false
```

**출력 참조**: `{{#노드ID.파라미터명#}}`

---

### 8. knowledge-retrieval (지식 검색)

등록된 Knowledge Base에서 관련 문서를 검색한다.

```yaml
data:
  type: knowledge-retrieval
  title: <노드 이름>
  desc: ''
  query_variable_selector:
    - <소스노드ID>
    - <쿼리변수명>
  dataset_ids:
    - <Knowledge Base UUID>
  dataset_retrieval_configs:
    - dataset_id: <Knowledge Base UUID>
      dataset_name: <데이터셋 이름>
      indexing_technique: high_quality
      provider: bedrock
      retrieval_model:
        search_method: hybrid_search   # semantic_search | full_text_search | hybrid_search
        top_k: 3
        score_threshold: 0.5
        score_threshold_enabled: false
        reranking_enable: true
        reranking_mode: reranking_model
        reranking_model:
          reranking_provider_name: bedrock
          reranking_model_name: cohere.rerank-v3-5:0
        weights: null
        reasoning_effort: null
  retrieval_mode: multiple           # single | multiple
  multiple_retrieval_config:
    reranking_enable: false
    reranking_mode: reranking_model
    score_threshold: null
    top_k: 4
    weights:
      keyword_setting:
        keyword_weight: 0.3
      vector_setting:
        vector_weight: 0.7
        embedding_model_name: cohere.embed-multilingual-v3
        embedding_provider_name: bedrock
```

**결과 참조**: LLM 노드의 `context.variable_selector: [노드ID, result]`로 주입

---

### 9. tool (내장 도구)

Dify 내장 도구를 호출한다.

```yaml
data:
  type: tool
  title: <노드 이름>
  desc: ''
  provider_type: builtin
  provider_id: <도구제공자ID>    # 예: chart
  provider_name: <도구제공자명>  # 예: chart
  tool_name: <도구명>            # 예: line_chart, bar_chart
  tool_label: <표시명>           # 예: Line Chart
  tool_configurations: {}
  tool_parameters:
    <파라미터명>:
      type: mixed                # mixed | variable | constant
      value: '{{#노드ID.변수명#}}'
```

**주요 내장 도구:**
- `chart / line_chart` — 라인 차트 (x_axis, data 파라미터)
- `chart / bar_chart` — 바 차트
- `http_request` — HTTP 요청

---

## 엣지 (Edges) 스키마

```yaml
edges:
  - id: <소스노드ID>-source-<타겟노드ID>-target   # 관례적 명명
    source: <소스노드ID>
    sourceHandle: source                           # 분기 노드는 분기 핸들 ID
    target: <타겟노드ID>
    targetHandle: target
    type: custom
    selected: false
    data:
      sourceType: <소스노드 타입>                  # 예: start, llm, code
      targetType: <타겟노드 타입>
```

---

## 전체 YAML 최상위 구조

```yaml
app:
  name: <앱 이름>
  description: <한 줄 설명>
  mode: workflow                 # workflow 고정
  icon: 🤖
  icon_background: '#7C3AED'
  memory_config: null
  use_icon_as_answer_icon: false
kind: app
version: 0.1.5
workflow:
  conversation_variables: []
  environment_variables: []
  features:
    file_upload:
      allowed_file_extensions: [.JPG, .JPEG, .PNG, .GIF, .WEBP, .SVG]
      allowed_file_types: [image]
      allowed_file_upload_methods: [local_file, remote_url]
      enabled: false
      image:
        enabled: false
      number_limits: 10
    sensitive_word_avoidance:
      enabled: false
    text_to_speech:
      enabled: false
      language: ''
      voice: ''
  graph:
    edges: []     # 엣지 목록
    nodes: []     # 노드 목록
    viewport:
      x: 0
      y: 0
      zoom: 1.0
```

---

## 노드 ID 명명 관례

| 노드 타입 | ID 패턴 예시 |
|---|---|
| start | `start` |
| end | `end` |
| llm | `llm_1`, `llm_2` |
| code | `code_1` |
| if-else | `if_else_1` |
| template-transform | `template_1`, `template_result` |
| parameter-extractor | `param_extract_1` |
| knowledge-retrieval | `knowledge_1` |
| tool | `tool_1` |

---

## 변수 참조 형식 요약

| 상황 | 형식 |
|---|---|
| LLM prompt_template 안에서 | `{{#노드ID.변수명#}}` |
| template-transform template 안에서 | `{{ 변수명 }}` (variables에 바인딩 필요) |
| tool_parameters value 안에서 | `{{#노드ID.변수명#}}` |
| value_selector (YAML 구조) | `[노드ID, 변수명]` |
| LLM context 참조 | `{{#context#}}` |
