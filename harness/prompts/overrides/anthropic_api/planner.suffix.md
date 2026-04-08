## API 직접 호출 모드 안내

이 세션에서는 Anthropic API tool_use를 통해 실행된다.

사용 가능한 도구:
- `file_read`: 파일 내용 읽기 (path 파라미터)
- `file_write`: 파일 작성 (path, content 파라미터)
- `file_search`: 파일 검색 (pattern, directory 파라미터)
- `code_search`: 코드 내용 검색 (pattern, directory, glob 파라미터)
- `shell_exec`: 쉘 명령 실행 (command 파라미터)

파일을 읽거나 쓸 때는 반드시 위 도구를 사용하라. 도구 없이 파일 경로만 언급하면 실행되지 않는다.
