# Docker Compose 사용법 - Ollama + MySQL

이 문서는 GPU 지원 Ollama와 MySQL 데이터베이스를 Docker Compose로 실행하는 방법을 설명합니다.

## 📋 사전 요구사항

### Windows (WSL2)

- Docker Desktop 설치
- WSL2 활성화
- NVIDIA GPU 드라이버 설치
- NVIDIA Container Toolkit 설치

### Linux

- Docker 및 Docker Compose 설치
- NVIDIA GPU 드라이버 설치
- NVIDIA Container Toolkit 설치

## 🚀 실행 방법

### 1. 컨테이너 시작

```bash
cd docker_compose_ollama_mysql
docker-compose up -d
```

### 2. 컨테이너 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs ollama
docker-compose logs mysql-db
```

### 3. GPU 사용 확인

```bash
# Ollama 컨테이너에서 GPU 확인
docker exec -it ollama nvidia-smi

# Ollama 로그에서 CUDA 메시지 확인
docker-compose logs ollama | grep -i cuda
```

## 🤖 Ollama 모델 관리

### 모델 다운로드

```bash
# CodeQwen 모델 다운로드 (SQL Agent용)
docker exec -it ollama ollama pull codeqwen:latest

# 또는 다른 코드 생성 모델
docker exec -it ollama ollama pull codellama:latest
```

### 모델 목록 확인

```bash
docker exec -it ollama ollama list
```

### 모델 테스트

```bash
# 대화형 테스트
docker exec -it ollama ollama run codeqwen:latest

# API 테스트
curl http://localhost:11434/api/generate -d '{
  "model": "codeqwen:latest",
  "prompt": "Generate SQL query to count all records in users table",
  "stream": false
}'
```

## 🗄️ MySQL 데이터베이스

### 데이터베이스 접속

```bash
# MySQL 클라이언트로 접속
docker exec -it mysql-db mysql -u root -psqlagent

# 또는 sqlagent 사용자로 접속
docker exec -it mysql-db mysql -u sqlagent -psqlagent sakila

# 외부에서 접속 (MySQL 클라이언트 설치 필요)
mysql -h localhost -P 3307 -u sqlagent -psqlagent sakila
```

### 기본 설정

- **호스트**: localhost
- **포트**: 3307 (외부 접속용)
- **Root 비밀번호**: sqlagent
- **사용자**: sqlagent
- **비밀번호**: sqlagent
- **데이터베이스**: sakila

## 🛠️ 관리 명령어

### 컨테이너 중지

```bash
docker-compose stop
```

### 컨테이너 재시작

```bash
docker-compose restart
```

### 컨테이너 완전 제거

```bash
docker-compose down
```

### 볼륨까지 제거 (데이터 삭제)

```bash
docker-compose down -v
```

### 로그 실시간 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f ollama
docker-compose logs -f mysql-db
```

## 📊 성능 모니터링

### GPU 사용률 모니터링

```bash
# 실시간 GPU 상태
watch -n 1 'docker exec -it ollama nvidia-smi'

# GPU 메모리 사용량
docker exec -it ollama nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### 컨테이너 리소스 사용량

```bash
docker stats ollama mysql-db
```

## 🔧 문제 해결

### GPU 인식 안됨

```bash
# NVIDIA 런타임 확인
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Docker 데몬 재시작 (Linux)
sudo systemctl restart docker

# Docker Desktop 재시작 (Windows)
```

### 모델 다운로드 실패

```bash
# 네트워크 연결 확인
docker exec -it ollama ping -c 3 ollama.ai

# 디스크 공간 확인
docker exec -it ollama df -h /root/.ollama
```

### 데이터베이스 연결 실패

```bash
# 컨테이너 상태 확인
docker-compose ps mysql-db

# 포트 확인
netstat -an | grep 3307

# 로그 확인
docker-compose logs mysql-db

# MySQL 서비스 상태 확인
docker exec -it mysql-db mysqladmin -u root -psqlagent status
```

## 📁 데이터 저장 위치

### Windows

- **Ollama 모델**: `C:/docker_data/ollama_models`
- **MySQL 데이터**: `C:/docker_data/mysql_data`

### 백업 방법

```bash
# Ollama 모델 백업
cp -r C:/docker_data/ollama_models C:/backup/ollama_models_$(date +%Y%m%d)

# MySQL 데이터 백업
docker exec mysql-db mysqldump -u root -psqlagent --all-databases > backup_$(date +%Y%m%d).sql

# 특정 데이터베이스만 백업
docker exec mysql-db mysqldump -u root -psqlagent sakila > sakila_backup_$(date +%Y%m%d).sql
```

## 🔄 업데이트

### 이미지 업데이트

```bash
# 최신 이미지 다운로드
docker-compose pull

# 컨테이너 재생성
docker-compose up -d --force-recreate
```

### 설정 변경 후 적용

```bash
# docker-compose.yml 수정 후
docker-compose down
docker-compose up -d
```

## 📝 사용 예시

### Python에서 Ollama 사용

```python
from langchain_ollama.llms import OllamaLLM

llm = OllamaLLM(
    model="codeqwen:latest",
    base_url="http://localhost:11434"
)

response = llm.invoke("Generate SQL query to select all films from sakila database")
print(response)
```

### MySQL 연결

```python
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    port=3307,
    database="sakila",
    user="sqlagent",
    password="sqlagent"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM film")
result = cursor.fetchone()
print(f"Total films: {result[0]}")
```

### 환경 변수 설정 (.env 파일)

```env
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# MySQL 데이터베이스 (Docker 설정과 일치)
DB_HOST=localhost
DB_PORT=3307
DB_USER=sqlagent
DB_PASSWORD=sqlagent
DB_NAME=sakila

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
```

## 📊 샘플 데이터 설치

### Sakila 데이터베이스 설치

```bash
# 프로젝트 루트에서 실행
docker exec -i mysql-db mysql -u root -psqlagent sakila < src/db_sample/sakila_schema_data.sql

# 설치 확인
docker exec -it mysql-db mysql -u root -psqlagent sakila -e "SHOW TABLES;"
docker exec -it mysql-db mysql -u root -psqlagent sakila -e "SELECT COUNT(*) FROM film;"
```

## ⚡ 성능 최적화 팁

1. **GPU 메모리 관리**: 큰 모델 사용 시 GPU 메모리 부족 주의
2. **모델 선택**: SQL 생성에는 `codeqwen:latest` 또는 `codellama:latest` 권장
3. **MySQL 설정**: 대용량 데이터 처리 시 `my.cnf` 튜닝 고려
4. **동시 요청**: 여러 요청 시 큐잉 고려
5. **디스크 공간**: 모델 파일과 MySQL 데이터용 충분한 디스크 공간 확보

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. Docker 및 Docker Compose 버전
2. NVIDIA 드라이버 버전
3. 컨테이너 로그
4. 시스템 리소스 사용량

## 🔗 관련 명령어

### SQL Agent 실행

```bash
# 웹 챗봇 실행 (Docker 서비스 시작 후)
cd ..  # 프로젝트 루트로 이동
uv sync
uv run python src/sql_agent_gradio_chat.py

# 브라우저에서 http://localhost:7860 접속
```

### 데이터베이스 관리

```bash
# 모든 테이블 목록
docker exec -it mysql-db mysql -u sqlagent -psqlagent sakila -e "SHOW TABLES;"

# 특정 테이블 구조 확인
docker exec -it mysql-db mysql -u sqlagent -psqlagent sakila -e "DESCRIBE film;"

# 데이터 개수 확인
docker exec -it mysql-db mysql -u sqlagent -psqlagent sakila -e "SELECT COUNT(*) FROM actor;"
```

---

**참고**:

- GPU 지원이 제대로 작동하면 Ollama의 SQL 생성 속도가 CPU 대비 10-100배 빨라집니다
- MySQL은 포트 3307로 외부 접속이 가능하므로 MySQL Workbench 등의 GUI 도구로도 접속할 수 있습니다
