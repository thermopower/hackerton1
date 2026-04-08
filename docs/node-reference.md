# MISO 워크플로우 노드 타입 레퍼런스

> 출처: https://miso-52g.gitbook.io/miso-manual/manual/workflow/node-definition  
> ex/ 폴더의 실제 YAML 파일 스키마 병합.  
> YAML 작성 시 이 문서를 기준으로 삼는다.

---

## 전체 노드 목록 (17개)

| 분류 | 타입 | 한국어명 | 설명 |
|------|------|---------|------|
| 기본 | `start` | 시작 | 워크플로우 진입점, 사용자 입력 변수 정의 |
| 기본 | `end` | 끝/답변 | 워크플로우 종료, 결과 반환 |
| AI | `llm` | LLM | AI 모델 호출, 텍스트 생성/분석 |
| AI | `question-classifier` | 의도 분류 | AI가 자연어 의도를 분류하여 분기 |
| AI | `parameter-extractor` | 변수 추출 | 텍스트에서 구조화 데이터 추출 |
| 지식 | `knowledge-retrieval` | 지식 검색 | Knowledge Base 문서 검색 |
| 지식 | `knowledge-add` | 지식 추가 | 실행 중 새 지식 동적 추가 |
| 지식 | `knowledge-indexing` | 인덱싱 확인 | 지식 인덱싱 상태 확인 |
| 흐름 | `if-else` | 조건 | 조건에 따른 분기 (AI 미사용, 비용 없음) |
| 흐름 | `iteration` | 반복 | 배열 항목마다 동일 처리 반복 |
| 흐름 | `loop` | 루프 | 조건 충족까지 구간 반복 |
| 데이터 | `code` | 코드 | Python3/JavaScript 코드 실행 |
| 데이터 | `template-transform` | 템플릿 | Jinja2 템플릿으로 텍스트 포맷팅 |
| 데이터 | `assigner` | 변수 할당 | 대화/루프 변수 값 직접 수정 |
| 데이터 | `variable-aggregator` | 변수 집계기 | 분기된 경로 결과를 하나로 통합 |
| 데이터 | `document-extractor` | 문서 추출기 | 업로드 파일에서 텍스트 추출 |
| 데이터 | `http-request` | API 요청 | 외부 HTTP API 호출 |

---

## 공통 YAML 필드 (모든 노드)

```yaml
id: <고유 식별자>
type: custom
position:
  x: <숫자>
  y: <숫자>
data:
  type: <노드타입>
  title: <표시 이름>
  desc: <설명>
  selected: false
  _connectedSourceHandleIds: [source]   # 이 노드에서 나가는 핸들 ID
  _connectedTargetHandleIds: [target]   # 이 노드로 들어오는 핸들 ID
  _inParallelHovering: false
  _isEntering: false
```

---

## 1. start (시작)

```yaml
data:
  type: start
  title: 시작
  variables:
    - variable: <변수명>          # 영문 스네이크케이스
      label: <화면 표시명>
      type: text-input            # text-input | paragraph | select | number | file
      required: true
      max_length: 256
      options: []                 # select 타입일 때 선택지
      # file 타입 추가 필드:
      allowed_file_types: [image, document, audio, video]
      allowed_file_extensions: [.PDF, .DOCX, .JPG, .PNG]
      allowed_file_upload_methods: [local_file, remote_url]
```

**변수 참조**: `{{#start.변수명#}}` 또는 value_selector `[start, 변수명]`

---

## 2. end (끝/답변)

```yaml
data:
  type: end
  title: 종료
  outputs:
    - variable: <출력변수명>
      value_selector:
        - <소스노드ID>
        - <소스변수명>
```

---

## 3. llm (LLM)

```yaml
data:
  type: llm
  title: <노드 이름>
  model:
    provider: bedrock
    name: us.anthropic.claude-haiku-4-5-20251001-v1:0
    # 모델 선택 기준:
    # 단순(분류/짧은 답변): claude-haiku-4-5-20251001-v1:0
    # 균형(요약/추론):       claude-sonnet-4-5-20250929-v1:0
    mode: chat
    completion_params:
      max_tokens: 4096         # 최대 64000
      temperature: 0           # 0.0~1.0. 낮을수록 일관적
  prompt_template:
    - role: system
      text: <시스템 프롬프트>
    - role: user
      text: '변수 참조: {{#노드ID.변수명#}}'
  context:
    enabled: false             # knowledge-retrieval 결과 주입 시 true
    variable_selector:
      - <knowledge-retrieval 노드ID>
      - result
  variables: []
  vision:
    enabled: false
```

**출력**: `text` (생성된 텍스트), `usage` (토큰 사용량)  
**참조**: `{{#노드ID.text#}}`

---

## 4. question-classifier (의도 분류)

AI 모델이 자연어 텍스트 의미를 판단해 분기. if-else보다 유연하나 토큰 비용 발생.

```yaml
data:
  type: question-classifier
  title: <노드 이름>
  model:
    provider: bedrock
    name: us.anthropic.claude-haiku-4-5-20251001-v1:0
    mode: chat
    completion_params:
      max_tokens: 512
  query_variable_selector:
    - <소스노드ID>
    - <변수명>             # 분류할 텍스트 (보통 start.query)
  classes:
    - id: <클래스ID_1>
      name: <카테고리명1>
    - id: <클래스ID_2>
      name: <카테고리명2>
  instruction: <분류 지침 (선택)>
  vision:
    enabled: false
  _connectedSourceHandleIds:
    - <클래스ID_1>
    - <클래스ID_2>
```

**출력**: `class_name` (분류된 카테고리명)  
**엣지**: 각 클래스 ID를 sourceHandle로 사용

---

## 5. parameter-extractor (변수 추출)

```yaml
data:
  type: parameter-extractor
  title: <노드 이름>
  model:
    provider: bedrock
    name: us.anthropic.claude-haiku-4-5-20251001-v1:0
    mode: chat
    completion_params:
      max_tokens: 4096
  instruction: <추출 지시문>
  parameters:
    - name: <파라미터명>
      type: string             # string | number | boolean | array[string]
      description: <설명>
      required: true
  query:
    - - <소스노드ID>
      - <변수명>
  reasoning_mode: function_call
  vision:
    enabled: false
```

**출력 참조**: `{{#노드ID.파라미터명#}}`

---

## 6. knowledge-retrieval (지식 검색)

```yaml
data:
  type: knowledge-retrieval
  title: <노드 이름>
  query_variable_selector:
    - <소스노드ID>
    - <변수명>
  dataset_ids:
    - <Knowledge Base UUID>
  dataset_retrieval_configs:
    - dataset_id: <UUID>
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
  retrieval_mode: multiple
  multiple_retrieval_config:
    top_k: 4
    reranking_enable: false
    weights:
      keyword_setting:
        keyword_weight: 0.3
      vector_setting:
        vector_weight: 0.7
        embedding_model_name: cohere.embed-multilingual-v3
        embedding_provider_name: bedrock
```

**결과 사용**: LLM 노드의 `context.variable_selector: [노드ID, result]`  
**⚠️ dataset UUID는 Dify/MISO 서버에 실제 등록된 값이 필요**

---

## 7. if-else (조건)

AI 미사용. 명시적 규칙으로 분기. 비용 없음, 결과 일관적.

```yaml
data:
  type: if-else
  title: <노드 이름>
  cases:
    - case_id: <분기ID>           # 핸들 ID와 일치 (예: is_anomaly)
      conditions:
        - variable_selector:
            - <소스노드ID>
            - <변수명>
          comparison_operator: is    # is | is not | contains | not contains
                                     # = | ≠ | > | < | ≥ | ≤
                                     # empty | not empty | starts with | ends with
          value: 'true'
      logical_operator: and          # and | or
  _targetBranches:
    - id: <분기ID>
      name: IF
    - id: 'false'
      name: ELSE
  _connectedSourceHandleIds:
    - <분기ID>
    - 'false'
```

**엣지**: 각 분기 핸들 ID를 sourceHandle로 사용

---

## 8. iteration (반복)

배열의 각 항목에 동일한 처리를 반복. 내부에 노드 그래프를 포함.

```yaml
data:
  type: iteration
  title: <노드 이름>
  iterator_selector:
    - <소스노드ID>
    - <배열변수명>             # 문자열/숫자/객체/파일 배열
  output_selector:
    - <내부노드ID>
    - <출력변수명>             # 각 반복의 결과값
  output_type: string          # string | number | object | array[string] 등
  is_parallel: false           # true: 병렬 실행
  parallel_nums: 5             # 병렬 시 동시 실행 수 (1~10)
  error_handle_mode: continue  # continue | terminate | remove_abnormal_output
  # 내부 노드들은 별도 nodes 배열에 정의
  # 내부에서 item (현재값), index (현재 순서, 0부터) 변수 사용 가능
```

**출력**: `output` (각 반복 결과의 배열)

---

## 9. loop (루프)

조건 충족까지 구간 반복. 배열 불필요.

```yaml
data:
  type: loop
  title: <노드 이름>
  max_loop_count: 10           # 최대 반복 횟수 (1~100, 기본 10)
  break_conditions:
    - variable_selector:
        - <루프변수명>
      comparison_operator: '='
      value: 'done'
    logical_operator: and
  loop_variables:
    - variable: <루프변수명>
      value_selector:
        - <소스노드ID>
        - <변수명>
```

**출력**: 루프 변수들의 최종값, `loop_round` (실제 반복 횟수)  
**제한**: 최대 실행 시간 5분

---

## 10. code (코드)

```yaml
data:
  type: code
  title: <노드 이름>
  code_language: python3       # python3 | javascript
  code: |
    def main(<입력변수1>, <입력변수2>):
        # 처리 로직
        return {
            '<출력키1>': <값>,
            '<출력키2>': <값>
        }
  variables:
    - variable: <입력변수명>   # main() 파라미터명과 일치
      value_selector:
        - <소스노드ID>
        - <소스변수명>
  outputs:
    <출력키1>:
      type: string             # string | number | object | array[string] 등
    <출력키2>:
      type: number
```

**제한**: 실행시간 60초, 문자열 배열 100개, 숫자 배열 1000개

---

## 11. template-transform (템플릿)

Jinja2 문법으로 텍스트를 조합.

```yaml
data:
  type: template-transform
  title: <노드 이름>
  template: |
    텍스트 내용
    {{ 변수명 }}
    {% if 조건 %}분기 내용{% endif %}
    {% for item in 배열 %}{{ item }}{% endfor %}
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

## 12. assigner (변수 할당)

대화 변수 또는 루프 변수의 값을 직접 수정. 루프 노드와 주로 함께 사용.

```yaml
data:
  type: assigner
  title: <노드 이름>
  instructions:
    - assigned_variable_selector:
        - <변수명>              # 대화 변수 또는 루프 변수
      operation: over-write    # over-write | set | append | clear
      value:
        type: variable         # variable | constant
        value:
          - <소스노드ID>
          - <소스변수명>
```

**출력 없음**: 변수를 수정할 뿐 새 출력 변수 생성 안 함

---

## 13. variable-aggregator (변수 집계기)

분기 후 여러 경로의 결과를 하나로 통합.

```yaml
data:
  type: variable-aggregator
  title: <노드 이름>
  variables:
    - - <분기노드A ID>
      - <출력변수명>
    - - <분기노드B ID>
      - <출력변수명>
  output_type: string          # 통합 결과 타입
  advanced_settings:
    group_enabled: false
```

**출력**: `output` (실행된 분기의 결과값)

---

## 14. document-extractor (문서 추출기)

업로드 파일에서 텍스트 추출. PDF, Word, Excel, PowerPoint 등 20개 이상 형식 지원.

```yaml
data:
  type: document-extractor
  title: <노드 이름>
  variable_selector:
    - <소스노드ID>
    - <파일변수명>             # file 또는 array[file] 타입
  is_array_file: false         # 파일 배열 입력 시 true
```

**출력**: `text` (추출된 텍스트. 단일 파일이면 string, 복수면 array[string])  
**제한**: 이미지/이미지 속 텍스트 미지원

---

## 15. knowledge-add (지식 추가)

워크플로우 실행 중 Knowledge Base에 새 내용을 동적으로 추가.

```yaml
data:
  type: knowledge-add
  title: <노드 이름>
  dataset_id: <Knowledge Base UUID>    # 기존 지식 선택 (없으면 새로 생성)
  dataset_name: <지식 이름>            # 새 지식 생성 시 이름
  dataset_description: <설명>          # 새 지식 생성 시 설명
  text_variable_selector:
    - <소스노드ID>
    - <텍스트변수명>                   # 추가할 텍스트 내용
  content_filename: content.txt        # 저장 파일명 (기본값)
  append_to_existing: false            # true: 같은 파일명 문서에 이어붙이기
  file_variable_selector:              # 파일로 추가할 경우 (텍스트 대신)
    - <소스노드ID>
    - <파일변수명>
```

**출력**:
- `status`: `processing` / `completed` / `skipped`
- `dataset_id`: 지식 고유 ID
- `dataset_name`: 지식명
- `document_ids`: 추가된 문서 ID 목록 (array)
- `message`: 처리 결과 메시지

---

## 16. knowledge-indexing (인덱싱 상태 확인)

knowledge-add 후 인덱싱 완료 여부를 확인. 루프 노드와 조합해 완료까지 대기 가능.

```yaml
data:
  type: knowledge-indexing
  title: <노드 이름>
  # 아래 셋 중 하나 이상 지정
  dataset_id_selector:
    - <knowledge-add 노드ID>
    - dataset_id
  batch_id_selector:              # 같은 시점에 추가된 문서 묶음 ID
    - <소스노드ID>
    - <배치ID변수>
  document_ids_selector:          # 개별 문서 ID 목록
    - <knowledge-add 노드ID>
    - document_ids
```

**출력**:
- `status`: `completed` / `processing` / `partial` / `error`
- `json`: 상세 인덱싱 상태 데이터 (array)
- `text`: 상태 요약 메시지

**⚠️ 사용 패턴**: knowledge-add → code(document_ids 추출) → knowledge-indexing → loop(완료까지 반복)

---

## 17. http-request (API 요청)

외부 HTTP API 호출.

```yaml
data:
  type: http-request
  title: <노드 이름>
  method: GET                  # GET | POST | PUT | PATCH | DELETE | HEAD
  url: 'https://api.example.com/endpoint/{{#start.변수명#}}'
  headers:
    - key: Authorization
      type: variable           # variable | constant
      value: '{{#start.api_key#}}'
    - key: Content-Type
      type: constant
      value: application/json
  params:
    - key: query
      type: variable
      value:
        - <소스노드ID>
        - <변수명>
  body:
    type: json                 # json | form-data | x-www-form-urlencoded | raw-text | none
    data:
      - key: message
        type: variable
        value:
          - <소스노드ID>
          - <변수명>
  timeout:
    connect: 10                # 연결 대기 (0~300초)
    read: 60                   # 수신 대기 (0~120초)
    write: 20                  # 송신 대기 (0~60초)
```

**출력**: `body` (응답 내용), `status_code`, `headers`, `files`  
**⚠️ status_code가 200이 아니어도 자동 오류 중단 안 됨 → if-else로 검증 필수**

---

## 16. interrupt (인터럽트)

워크플로우를 일시 정지하고 사용자 입력 대기. **챗플로우 전용**, 관리자 활성화 필요.

```yaml
data:
  type: interrupt
  title: <노드 이름>
  interrupt_type: approval     # approval | form | branch-selection
  timeout: 1440                # 분 단위 (1~1440, 기본 1440)
  # approval 타입:
  #   출력: approved(Boolean), comment(String)
  # form 타입:
  #   fields: 폼 필드 정의
  # branch-selection 타입:
  #   출력: selected_branch(String)
```

---

## 엣지 스키마

```yaml
- id: <소스ID>-source-<타겟ID>-target
  source: <소스노드ID>
  sourceHandle: source           # 분기 노드는 분기 핸들 ID
  target: <타겟노드ID>
  targetHandle: target
  type: custom
  selected: false
  data:
    sourceType: <소스 노드타입>
    targetType: <타겟 노드타입>
```

---

## 전체 YAML 최상위 구조

```yaml
app:
  name: <앱 이름>
  description: <한 줄 설명>
  mode: workflow
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
    edges: []
    nodes: []
    viewport:
      x: 0
      y: 0
      zoom: 1.0
```

---

## 노드 ID 명명 관례

| 타입 | ID 패턴 |
|------|---------|
| start | `start` |
| end | `end` |
| llm | `llm_1`, `llm_2` |
| code | `code_1` |
| if-else | `if_else_1` |
| template-transform | `template_1` |
| parameter-extractor | `param_extract_1` |
| knowledge-retrieval | `knowledge_1` |
| question-classifier | `classifier_1` |
| variable-aggregator | `aggregator_1` |
| document-extractor | `doc_extractor_1` |
| http-request | `http_1` |
| iteration | `iteration_1` |
| loop | `loop_1` |
| assigner | `assigner_1` |

---

## 변수 참조 형식 요약

| 상황 | 형식 |
|------|------|
| LLM prompt_template / http-request url 안에서 | `{{#노드ID.변수명#}}` |
| template-transform template 안에서 | `{{ 변수명 }}` (variables에 바인딩 필요) |
| value_selector (YAML 구조) | `[노드ID, 변수명]` |
| LLM context 참조 | `{{#context#}}` |
| iteration 내부 현재 항목 | `item`, `index` |
