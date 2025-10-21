# SQL Agent Gradio 챗봇

자연어로 질문하면 SQL 쿼리를 생성하고 실행하는 웹 기반 챗봇입니다.

## 🚀 주요 기능

- **🌐 웹 인터페이스**: Gradio 기반의 직관적인 채팅 UI
- **🔄 하이브리드 모델**: Gemini(번역) + CodeLlama(SQL생성)
- **📊 다양한 쿼리**: SELECT, INSERT, UPDATE, DELETE 지원
- **🛡️ 안전 모드**: SELECT만 실행, 나머지는 쿼리만 생성
- **🌍 다국어**: 한국어, 영어 모두 지원

## 📋 요구사항

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env 파일)

```env
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# MySQL 데이터베이스
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
```

### 3. Ollama 모델 설치

```bash
# CodeQwen 모델 설치 (SQL 생성용)
ollama pull codeqwen:latest
```

## 🎯 사용법

### 1. 웹 챗봇 실행

```bash
# 로컬에서만 실행
python run_gradio_chat.py

# 공개 링크와 함께 실행
python run_gradio_chat.py --share
```

### 2. 명령행에서 직접 실행

```bash
# 단일 질문
python src/sql_agent_simple_hybrid.py "영화가 몇 개 있나요?"

# 대화형 모드
python src/sql_agent_simple_hybrid.py
```

## 💡 예시 질문

### 📊 SELECT 쿼리

- "영화가 몇 개 있나요?"
- "고객 수를 보여주세요"
- "영화 카테고리별 개수를 알려주세요"
- "How many films are there?"

### ➕ INSERT 쿼리

- "새로운 영화를 추가해주세요"
- "고객 정보를 등록해주세요"
- "Add a new customer"

### ✏️ UPDATE 쿼리

- "영화 제목을 수정해주세요"
- "고객 정보를 업데이트해주세요"
- "Update customer information"

### 🗑️ DELETE 쿼리

- "오래된 영화를 삭제해주세요"
- "불필요한 데이터를 제거해주세요"
- "Remove old records"

## 🔧 설정

### 포트 변경

`src/sql_agent_gradio_chat.py`에서 포트 번호 수정:

```python
"server_port": 7860,  # 원하는 포트로 변경
```

### 공개 링크 기본 활성화

```python
"share": True,  # 항상 공개 링크 생성
```

## 🛡️ 보안 주의사항

- **INSERT/UPDATE/DELETE 쿼리는 실행되지 않습니다** (안전을 위해)
- 실제 데이터 조작이 필요한 경우 생성된 쿼리를 직접 데이터베이스에서 실행하세요
- 프로덕션 환경에서는 적절한 인증 및 권한 관리를 구현하세요

## 📁 파일 구조

```
├── src/
│   ├── sql_agent_simple_hybrid.py    # 핵심 SQL Agent 로직
│   └── sql_agent_gradio_chat.py      # Gradio 웹 인터페이스
├── run_gradio_chat.py                # 실행 스크립트
├── requirements.txt                  # Python 의존성
├── .env                             # 환경 변수 (생성 필요)
└── README_gradio.md                 # 이 파일
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

### 3. Gradio 실행 오류

```bash
# 의존성 재설치
pip install --upgrade gradio

# 포트 충돌 시 다른 포트 사용
python run_gradio_chat.py
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. 모든 의존성이 설치되었는지
2. 환경 변수가 올바르게 설정되었는지
3. 데이터베이스와 Ollama가 실행 중인지
