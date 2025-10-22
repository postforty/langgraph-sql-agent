# Docker Compose 사용법 - Ollama + PGVector

이 문서는 GPU 지원 Ollama와 PGVector 데이터베이스를 Docker Compose로 실행하는 방법을 설명합니다.

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
cd docker_compose_ollama_pgvector
docker-compose up -d
```

### 2. 컨테이너 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs ollama
docker-compose logs pgvector-db
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
# Gemma3 모델 다운로드
docker exec -it ollama ollama pull gemma3:latest
```

### 모델 목록 확인

```bash
docker exec -it ollama ollama list
```

### 모델 테스트

```bash
# 대화형 테스트
docker exec -it ollama ollama run gemma2:latest

# API 테스트
curl http://localhost:11434/api/generate -d '{
  "model": "gemma2:latest",
  "prompt": "Hello, world!",
  "stream": false
}'
```

## 🗄️ PGVector 데이터베이스

### 데이터베이스 접속

```bash
# psql로 접속
docker exec -it pgvector-db psql -U langchain -d langchain_db

# 또는 외부에서 접속
psql -h localhost -p 5432 -U langchain -d langchain_db
```

### 기본 설정

- **호스트**: localhost
- **포트**: 5432
- **사용자**: langchain
- **비밀번호**: langchain
- **데이터베이스**: langchain_db

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
docker-compose logs -f pgvector-db
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
docker stats ollama pgvector-db
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
docker-compose ps pgvector-db

# 포트 확인
netstat -an | grep 5432

# 로그 확인
docker-compose logs pgvector-db
```

## 📁 데이터 저장 위치

### Windows

- **Ollama 모델**: `C:/docker_data/ollama_models`
- **PGVector 데이터**: `C:/docker_data/pgvector_data`

### 백업 방법

```bash
# Ollama 모델 백업
cp -r C:/docker_data/ollama_models C:/backup/ollama_models_$(date +%Y%m%d)

# PGVector 데이터 백업
docker exec pgvector-db pg_dump -U langchain langchain_db > backup_$(date +%Y%m%d).sql
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
    model="gemma2:latest",
    base_url="http://localhost:11434"
)

response = llm.invoke("Hello, world!")
print(response)
```

### PGVector 연결

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="langchain_db",
    user="langchain",
    password="langchain"
)
```

## ⚡ 성능 최적화 팁

1. **GPU 메모리 관리**: 큰 모델 사용 시 GPU 메모리 부족 주의
2. **모델 선택**: 용도에 맞는 적절한 크기의 모델 선택
3. **동시 요청**: 여러 요청 시 큐잉 고려
4. **디스크 공간**: 모델 파일은 용량이 크므로 충분한 디스크 공간 확보

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. Docker 및 Docker Compose 버전
2. NVIDIA 드라이버 버전
3. 컨테이너 로그
4. 시스템 리소스 사용량

---

**참고**: GPU 지원이 제대로 작동하면 Ollama의 추론 속도가 CPU 대비 10-100배 빨라집니다.
