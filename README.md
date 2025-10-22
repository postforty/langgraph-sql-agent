# SQL Agent 프로젝트

자연어로 질문하면 SQL 쿼리를 생성하고 실행하는 AI 에이전트입니다.

## 🚀 주요 기능

- **🌐 웹 챗봇**: Gradio 기반의 직관적한 채팅 인터페이스
- **🔄 하이브리드 모델**: Gemini(번역) + CodeLlama(SQL생성)
- **📊 다양한 쿼리**: SELECT, INSERT, UPDATE, DELETE 지원
- **🛡️ 안전 모드**: SELECT만 실행, 나머지는 쿼리만 생성
- **🌍 다국어**: 한국어, 영어 모두 지원

## 📋 요구사항

### 방법 1: Docker Compose 사용 (추천)

Docker Compose를 사용하면 Ollama와 데이터베이스를 쉽게 설정할 수 있습니다.

```bash
# 1. Docker Compose로 서비스 시작
cd docker_compose_ollama_mysql
docker-compose up -d

# 2. Ollama 모델 설치
docker exec -it ollama ollama pull codeqwen:latest

# 3. 환경 변수 설정 (.env 파일)
GOOGLE_API_KEY=your_gemini_api_key
DB_HOST=localhost
DB_PORT=3307
DB_USER=sqlagent
DB_PASSWORD=sqlagent
DB_NAME=sakila
```

**📖 자세한 Docker 사용법**: [`docker_compose_ollama_mysql/docker-compose.md`](docker_compose_ollama_mysql/docker-compose.md) 참조

### 방법 2: 로컬 설치

#### 1. uv 설치

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```env
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# MySQL 데이터베이스
DB_HOST=localhost
DB_PORT=3307
DB_USER=sqlagent
DB_PASSWORD=sqlagent
DB_NAME=sakila
```

#### 3. Ollama 모델 설치

```bash
# Ollama 설치 후
ollama pull codeqwen:latest
```

## 🎯 사용법

### 웹 챗봇 실행 (추천)

```bash
# 1. 의존성 설치 및 가상환경 생성
uv sync

# 2. Gradio 웹 챗봇 실행
uv run python src/sql_agent_gradio_chat.py

# 3. 브라우저에서 http://localhost:7860 접속
```

### 명령행에서 직접 실행

```bash
# 단일 질문
uv run python src/sql_agent_simple_hybrid.py "영화가 몇 개 있나요?"

# 대화형 모드
uv run python src/sql_agent_simple_hybrid.py
```

## 💡 예시 질문 (Sakila 데이터베이스 기준)

### 📊 SELECT 쿼리

**기본 통계**

- "영화가 몇 개 있나요?"
- "배우 수를 보여주세요"
- "고객이 몇 명인가요?"
- "How many films are there?"

**상세 분석**

- "카테고리별 영화 개수를 알려주세요"
- "가장 대여가 많은 영화 10편을 보여주세요"
- "매장별 고객 수를 알려주세요"
- "배우별 출연 영화 수를 보여주세요"

**복합 조회**

- "액션 영화에 출연한 배우들을 보여주세요"
- "2005년에 가입한 고객들의 대여 현황을 알려주세요"
- "가장 수익이 높은 영화 카테고리는?"

### ➕ INSERT 쿼리

- "새로운 영화를 추가해주세요"
- "고객 정보를 등록해주세요"
- "새로운 배우를 추가해주세요"
- "Add a new customer"

### ✏️ UPDATE 쿼리

- "영화 제목을 수정해주세요"
- "고객 이메일을 업데이트해주세요"
- "배우 이름을 변경해주세요"
- "Update customer information"

### 🗑️ DELETE 쿼리

- "비활성 고객을 삭제해주세요"
- "오래된 대여 기록을 제거해주세요"
- "중복된 데이터를 삭제해주세요"
- "Remove old records"

## 🔧 고급 설정

### 공개 링크로 실행

```bash
# 외부에서 접근 가능한 공개 링크 생성
uv run python src/sql_agent_gradio_chat.py --share
```

### 포트 변경

`src/sql_agent_gradio_chat.py`에서 포트 번호 수정:

```python
"server_port": 7860,  # 원하는 포트로 변경
```

## 🛡️ 보안 주의사항

- **INSERT/UPDATE/DELETE 쿼리는 실행되지 않습니다** (안전을 위해)
- 실제 데이터 조작이 필요한 경우 생성된 쿼리를 직접 데이터베이스에서 실행하세요
- 프로덕션 환경에서는 적절한 인증 및 권한 관리를 구현하세요

## 📊 샘플 데이터베이스 (Sakila)

프로젝트에는 테스트용 **Sakila** 데이터베이스 스키마와 데이터가 포함되어 있습니다(src\db_sample\sakila_schema_data.sql).

### 데이터베이스 구조

**주요 테이블들:**

- `actor` - 배우 정보 (200명)
- `film` - 영화 정보 (1000편)
- `customer` - 고객 정보 (599명)
- `rental` - 대여 기록
- `payment` - 결제 정보
- `category` - 영화 카테고리
- `language` - 언어 정보
- `store` - 매장 정보
- `staff` - 직원 정보
- `inventory` - 재고 관리

### 샘플 데이터 설치

Docker Compose를 사용하는 경우 아래 명령어를 사용하세요.

```bash
# 권장 방법: root 사용자로 실행 (SUPER 권한 필요한 구문 때문)
docker exec -i mysql-db mysql -u root -psqlagent sakila < src/db_sample/sakila_schema_data.sql

# 또는 Docker Compose 사용 (docker_compose_ollama_mysql 디렉토리에서 실행)
cd docker_compose_ollama_mysql
docker-compose exec mysql-db mysql -u root -psqlagent sakila < ../src/db_sample/sakila_schema_data.sql
```

**명령어 설명**:

```bash
docker exec -i mysql-db mysql -u root -psqlagent sakila < src/db_sample/sakila_schema_data.sql
```

- `docker exec`: 실행 중인 Docker 컨테이너에서 명령어 실행
- `-i`: 표준 입력(stdin)을 열어둠 (SQL 파일 내용을 전달하기 위해)
- `mysql-db`: 대상 MySQL 컨테이너 이름
- `mysql`: MySQL 클라이언트 실행
- `-u root`: **root 사용자** 사용 (SUPER 권한 필요)
- `-psqlagent`: 비밀번호 지정 (**공백 없이** 붙여서 작성)
- `sakila`: 대상 데이터베이스명
- `< src/db_sample/sakila_schema_data.sql`: SQL 파일을 표준 입력으로 전달

**중요**:

- SQL 파일에 DEFINER 구문이 있어 SUPER 권한이 필요하므로 `root` 사용자를 사용합니다

**문제 해결**:

- `ERROR 1227: Access denied; you need SUPER privilege` 오류 발생 시:
  - **해결책**: `root` 사용자로 실행 (위 명령어 참조)
  - **원인**: SQL 파일에 DEFINER나 특별한 권한이 필요한 구문이 포함되어 있음
- `ERROR 1049 (42000): Unknown database 'sakila'` 오류가 발생하면:
  - Docker Compose가 제대로 실행되었는지 확인: `docker-compose ps`
  - MySQL 초기화 로그 확인: `docker-compose logs mysql-db`
- 데이터 설치 확인:

  ```bash
  # 테이블 목록 확인
  docker exec -it mysql-db mysql -u root -psqlagent sakila -e "SHOW TABLES;"

  # 데이터 개수 확인
  docker exec -it mysql-db mysql -u root -psqlagent sakila -e "SELECT COUNT(*) FROM film;"
  ```

**참고**:

- 컨테이너 이름: `mysql-db`
- 사용자명: `sqlagent`
- 비밀번호: `sqlagent`
- 데이터베이스: `sakila`

### 예시 질문들

이 데이터베이스로 다음과 같은 질문들을 테스트할 수 있습니다:

**📊 기본 조회**

- "영화가 몇 개 있나요?"
- "배우 수를 알려주세요"
- "고객이 몇 명인가요?"

**🔍 상세 분석**

- "카테고리별 영화 개수를 보여주세요"
- "가장 인기 있는 배우 10명을 알려주세요"
- "매장별 매출을 보여주세요"

**➕ 데이터 조작 (쿼리만 생성)**

- "새로운 영화를 추가해주세요"
- "고객 정보를 수정해주세요"
- "오래된 대여 기록을 삭제해주세요"

## 📁 프로젝트 구조

```
├── src/
│   ├── sql_agent_simple_hybrid.py    # 핵심 SQL Agent 로직
│   ├── sql_agent_gradio_chat.py      # Gradio 웹 인터페이스
│   └── db_sample/                    # 샘플 데이터베이스
│       └── sakila_schema_data.sql    # 스키마 + 데이터
├── docker_compose_ollama_mysql/      # Docker Compose 설정
│   ├── docker-compose.yml            # Docker 서비스 정의
│   └── docker-compose.md             # Docker 사용법 가이드
├── pyproject.toml                    # uv 프로젝트 설정
├── .env                              # 환경 변수 (생성 필요)
└── README.md                         # 이 파일
```

## 🐛 문제 해결

### 1. 데이터베이스 연결 실패

- `.env` 파일의 데이터베이스 설정 확인
- MySQL 서버 실행 상태 확인
- 방화벽 및 포트 설정 확인

### 2. Ollama 모델 오류

```bash
# 모델 재설치
ollama pull codeqwen:latest

# Ollama 서비스 재시작
ollama serve
```

### 3. Docker 관련 오류

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs ollama
docker-compose logs mysql-db

# 서비스 재시작
docker-compose restart

# GPU 사용 확인 (GPU 지원 시)
docker exec -it ollama nvidia-smi
```

### 4. uv 관련 오류

```bash
# 가상환경 재생성
uv sync --reinstall

# 캐시 정리
uv cache clean
```

### 5. Gradio 실행 오류

```bash
# 의존성 재설치
uv sync

# 포트 충돌 시 다른 포트 사용
# src/sql_agent_gradio_chat.py에서 포트 번호 변경
```

## 🚀 빠른 시작

### Docker Compose 사용 (추천)

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd sql-agent

# 2. Docker 서비스 시작
cd docker_compose_ollama_mysql
docker-compose up -d

# 3. Ollama 모델 설치
docker exec -it ollama ollama pull codeqwen:latest

# 4. 환경 변수 설정
# .env 파일 생성 후 MySQL Docker 설정값 입력:
# DB_HOST=localhost, DB_PORT=3307, DB_USER=sqlagent, DB_PASSWORD=sqlagent, DB_NAME=sakila

# 5. 웹 챗봇 실행
cd ..
uv sync
uv run python src/sql_agent_gradio_chat.py

# 6. 브라우저에서 http://localhost:7860 접속
```

### 로컬 설치 사용

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd sql-agent

# 2. 환경 설정
cp .env.example .env  # .env 파일 생성 후 설정값 입력

# 3. Ollama 모델 설치
ollama pull codeqwen:latest

# 4. 웹 챗봇 실행
uv sync
uv run python src/sql_agent_gradio_chat.py

# 5. 브라우저에서 http://localhost:7860 접속
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. uv가 올바르게 설치되었는지
2. 환경 변수가 올바르게 설정되었는지
3. 데이터베이스와 Ollama가 실행 중인지
4. 필요한 모든 의존성이 설치되었는지 (`uv sync`)

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

```
MIT License

Copyright (c) 2024 SQL Agent Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 🤝 기여하기

이 프로젝트에 기여를 환영합니다! 다음과 같은 방법으로 참여할 수 있습니다:

- 🐛 버그 리포트
- 💡 새로운 기능 제안
- 📝 문서 개선
- 🔧 코드 기여

### 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 기반으로 합니다:

- **LangChain** - AI 애플리케이션 개발 프레임워크
- **Gradio** - 머신러닝 모델 웹 인터페이스
- **Ollama** - 로컬 LLM 실행 플랫폼
- **Google Gemini** - 다국어 번역 지원
- **Sakila Database** - MySQL 샘플 데이터베이스

---

**⭐ 이 프로젝트가 도움이 되었다면 GitHub에서 스타를 눌러주세요!**
