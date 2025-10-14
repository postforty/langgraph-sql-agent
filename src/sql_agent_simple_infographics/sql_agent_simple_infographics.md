# SQL Agent with 인포그래픽 시스템

## 개요

이 시스템은 **SQL Agent와 인포그래픽 생성을 결합한 대화형 데이터 분석 도구**입니다. 사용자가 자연어로 질문하면 자동으로 SQL 쿼리를 생성하고 실행한 후, 결과를 시각화할 수 있습니다.

## 핵심 구성 요소

### 1. 환경 설정

- **LLM**: Google Gemini 2.5 Flash 모델 사용
- **데이터베이스**: MySQL 연결 (환경변수에서 DB 정보 로드)
- **Agent**: LangChain의 SQL Agent 생성
- **시각화**: Plotly를 사용한 인터랙티브 차트

### 2. 주요 라이브러리

```python
- langchain_community: SQL Agent 및 데이터베이스 유틸리티
- langchain_google_genai: Google Gemini LLM
- plotly: 인터랙티브 차트 생성
- pandas: 데이터 처리
- pymysql: MySQL 연결
```

## 주요 함수 설명

### `create_infographic_from_sql_query(sql_query, question)`

SQL 쿼리 결과를 시각화하는 핵심 함수

**기능:**

- SQL 쿼리를 직접 실행하고 결과를 DataFrame으로 변환
- Decimal 객체 처리를 위한 복잡한 파싱 로직 구현
- 데이터 타입에 따라 자동으로 적절한 차트 선택
- HTML 파일로 인포그래픽 저장

**차트 선택 로직:**

- **막대 차트**: 숫자 컬럼 + 카테고리 컬럼이 있는 경우
- **파이 차트**: 카테고리 데이터만 있는 경우
- **테이블**: 기타 모든 경우

### `extract_sql_from_agent_output(captured_text)`

Agent 실행 로그에서 SQL 쿼리를 추출하는 함수

**기능:**

- 정규식 패턴을 사용해 실행된 SQL 쿼리 찾기
- SELECT 문만 필터링하여 반환
- 여러 패턴을 시도하여 안정적인 추출

## 시스템 작동 방식

### 1. 질문 입력

```
❓ 질문을 입력하세요: 각 카테고리별 영화 수를 알려주세요
```

### 2. SQL Agent 실행

- 자연어 질문을 SQL 쿼리로 변환
- 데이터베이스에서 쿼리 실행
- 결과를 자연어로 설명

### 3. 결과 출력

```
✅ 답변:
카테고리별 영화 수는 다음과 같습니다:
- Action: 64편
- Comedy: 58편
- Drama: 62편
...
```

### 4. 인포그래픽 생성 (선택사항)

```
🎨 인포그래픽을 생성하시겠습니까? (y/n): y
```

### 5. HTML 파일 생성

- `infographics/` 폴더에 타임스탬프가 포함된 파일명으로 저장
- 브라우저에서 바로 열어볼 수 있는 인터랙티브 차트

## 데이터 처리 특징

### Decimal 객체 처리

MySQL에서 반환되는 Decimal 객체를 안전하게 파싱:

```python
# Decimal('123.45') → 123.45
def decimal_replacer(match):
    return match.group(1)

cleaned_result = re.sub(r"Decimal\('([^']+)'\)", decimal_replacer, result)
```

### 다양한 데이터 형태 지원

- 튜플 리스트: `[('name1', 'name2', value), ...]`
- 문자열 결과: Agent 출력을 파싱
- 정규식 대안 파싱: 복잡한 형태도 처리

### 자동 컬럼명 생성

```python
if num_cols == 2:
    columns = ['name', 'value']
elif num_cols == 3:
    columns = ['col1', 'col2', 'col3']
else:
    columns = [f'col_{i+1}' for i in range(num_cols)]
```

## 사용 예시

### 질문 예시

- "각 카테고리별 영화 수를 알려주세요"
- "고객별 총 결제 금액 상위 10명을 보여주세요"
- "가장 많이 대여된 영화 5개는?"
- "월별 매출 추이를 보여주세요"

### 생성되는 파일

```
infographics/
├── chart_20241014_143022.html    # 막대 차트
├── pie_20241014_143155.html       # 파이 차트
└── table_20241014_143301.html     # 테이블
```

## 장점

1. **사용자 친화적**: 자연어로 데이터베이스 질의 가능
2. **자동 시각화**: 데이터 타입에 맞는 차트 자동 선택
3. **인터랙티브**: Plotly 기반의 동적 차트
4. **실용적**: 실제 DB 환경의 Decimal 등 고려
5. **확장 가능**: 새로운 차트 타입 쉽게 추가 가능

## 활용 분야

- **비즈니스 인텔리전스**: 비개발자도 쉬운 데이터 탐색
- **데이터 분석**: 빠른 시각화를 통한 인사이트 발견
- **리포팅**: 자동화된 차트 생성
- **교육**: SQL 학습 도구로 활용

## 기술적 고려사항

### 복잡한 부분

1. **SQL 쿼리 추출**: Agent 출력에서 정규식으로 쿼리 파싱
2. **데이터 변환**: 다양한 형태를 DataFrame으로 안전하게 변환
3. **Decimal 처리**: MySQL 특화된 데이터 타입 처리

### 개선 가능한 부분

- 더 다양한 차트 타입 지원
- 차트 스타일 커스터마이징
- 에러 처리 강화
- 캐싱 시스템 추가
