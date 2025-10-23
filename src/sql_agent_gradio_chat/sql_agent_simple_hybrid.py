"""
간단한 하이브리드 SQL Agent - 직접 SQL 생성 방식
Gemini(번역) + CodeLlama(SQL생성) - Agent 없이 직접 호출
"""
import sys
import re
from datetime import datetime

from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv(override=True)

print("🤖 간단한 하이브리드 SQL Agent - 직접 생성 방식")

# 번역용 Gemini
translator_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)
print("✅ Gemini 번역 모델 로드 완료")

# SQL 생성용 Gemini
sql_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)
# SQL 생성용 CodeLlama (주석 처리)
# https://ollama.com/library/codeqwen
# sql_llm = OllamaLLM(
#     model="codeqwen:latest",
#     temperature=0
# )
print("✅ Gemini SQL 모델 로드 완료")

# MySQL 연결
db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"

try:
    db = SQLDatabase.from_uri(db_uri)
    print(f"✅ 데이터베이스 연결 성공")
    print(f"📊 테이블: {db.get_usable_table_names()}")
except Exception as e:
    print(f"❌ 데이터베이스 연결 실패: {e}")
    exit(1)


def translate_to_english(korean_question):
    """한국어 질문을 영어로 번역"""
    try:
        print(f"🌐 번역 중: {korean_question}")

        translation_prompt = f"""
Translate the following Korean question to English. 
Keep it simple and clear for database queries.
If there are multiple questions separated by commas, translate each one clearly.
Only return the English translation, nothing else.

Korean: {korean_question}
English:"""

        result = translator_llm.invoke(translation_prompt)
        english_question = result.content.strip()
        print(f"✅ 번역 완료: {english_question}")
        return english_question

    except Exception as e:
        print(f"⚠️ 번역 실패, 원문 사용: {e}")
        return korean_question


def split_multiple_questions(question):
    """복수 질문을 개별 질문으로 분리"""
    # 쉼표나 "그리고"로 구분된 질문들을 분리
    separators = [',', '그리고', 'and', '또한', 'also']

    questions = [question]
    for sep in separators:
        new_questions = []
        for q in questions:
            if sep in q:
                parts = q.split(sep)
                new_questions.extend([part.strip()
                                     for part in parts if part.strip()])
            else:
                new_questions.append(q)
        questions = new_questions

    # 중복 제거 및 빈 문자열 제거
    questions = list(set([q for q in questions if q and len(q) > 3]))

    return questions if len(questions) > 1 else [question]


def is_korean(text):
    """텍스트에 한글이 포함되어 있는지 확인"""
    return any('\uac00' <= char <= '\ud7af' for char in text)


def get_database_schema():
    """데이터베이스에서 실제 스키마 정보 가져오기"""
    try:
        # 실제 데이터베이스 스키마 정보 가져오기
        schema_info = db.get_table_info()
        return schema_info
    except Exception as e:
        print(f"⚠️ 스키마 정보 가져오기 실패: {e}")

        # 최소한의 fallback - 테이블 목록만 활용
        try:
            table_names = db.get_usable_table_names()
            if table_names:
                fallback_schema = f"""
Available tables: {', '.join(table_names)}

Note: Detailed schema information is not available. 
Please use basic table and column names commonly found in databases.
Common patterns:
- Most tables have an 'id' or '[table_name]_id' as primary key
- Look for common column names like 'name', 'title', 'date', 'amount', etc.
"""
                print(f"📋 사용 가능한 테이블: {table_names}")
                return fallback_schema
        except Exception as e2:
            print(f"⚠️ 테이블 목록도 가져올 수 없음: {e2}")

        # 완전 실패시 - 스키마 없이 진행
        return """
Schema information is not available. 
Please generate SQL queries based on common database patterns and table/column naming conventions.
"""


def detect_query_type(english_question):
    """질문에서 SQL 쿼리 타입 감지"""
    question_lower = english_question.lower()

    # INSERT 키워드 감지
    insert_keywords = ['add', 'insert', 'create', 'register', '추가', '등록', '생성']
    if any(keyword in question_lower for keyword in insert_keywords):
        return 'INSERT'

    # UPDATE 키워드 감지
    update_keywords = ['update', 'modify',
                       'change', 'edit', '수정', '변경', '업데이트']
    if any(keyword in question_lower for keyword in update_keywords):
        return 'UPDATE'

    # DELETE 키워드 감지
    delete_keywords = ['delete', 'remove', 'drop', '삭제', '제거']
    if any(keyword in question_lower for keyword in delete_keywords):
        return 'DELETE'

    # 기본값은 SELECT
    return 'SELECT'


def generate_sql_direct(english_question):
    """CodeLlama로 직접 SQL 생성"""
    try:
        print(f"🔍 SQL 생성 중: {english_question}")

        # 쿼리 타입 감지
        query_type = detect_query_type(english_question)
        print(f"🎯 감지된 쿼리 타입: {query_type}")

        # 동적으로 스키마 정보 가져오기
        schema_info = get_database_schema()

        # 스키마 정보가 너무 부족한 경우 경고
        if "Schema information is not available" in schema_info:
            print("⚠️ 스키마 정보 없이 SQL 생성 시도 - 결과가 부정확할 수 있습니다")

        # 쿼리 타입별 프롬프트 생성
        if query_type == 'SELECT':
            sql_prompt = f"""### Instructions:
Your task is to convert a question into a SQL SELECT query, given a MySQL database schema.
Adhere to these rules:
- **Deliberately go through the question and database schema word by word** to appropriately answer the question
- **Use Table Aliases** to prevent ambiguity. For example, `SELECT f.title, a.first_name FROM film f JOIN film_actor fa ON f.film_id = fa.film_id JOIN actor a ON fa.actor_id = a.actor_id`.
- When creating a ratio, always cast the numerator as float

### Input:
Generate a SQL SELECT query that answers the question `{english_question}`.
This query will run on a database whose schema is represented in this string:

{schema_info}

-- Key Relationships for JOINs:
-- film_actor: connects film and actor tables
-- film_category: connects film and category tables  
-- rental: connects customer, inventory, and staff
-- payment: connects customer, staff, and rental
-- inventory: connects film and store

### Response:
Based on your instructions, here is the SQL SELECT query I have generated to answer the question `{english_question}`:
```sql"""

        elif query_type == 'INSERT':
            sql_prompt = f"""### Instructions:
Your task is to convert a request into a SQL INSERT query, given a MySQL database schema.
Adhere to these rules:
- **Deliberately go through the request and database schema word by word** to create appropriate INSERT statement
- **Use realistic sample data** that fits the schema constraints
- **Include all required columns** based on the schema
- **Use proper data types** (strings in quotes, numbers without quotes, dates in proper format)

### Input:
Generate a SQL INSERT query for the request `{english_question}`.
This query will be based on a database whose schema is represented in this string:

{schema_info}

### Response:
Based on your instructions, here is the SQL INSERT query I have generated for the request `{english_question}`:
```sql"""

        elif query_type == 'UPDATE':
            sql_prompt = f"""### Instructions:
Your task is to convert a request into a SQL UPDATE query, given a MySQL database schema.
Adhere to these rules:
- **Deliberately go through the request and database schema word by word** to create appropriate UPDATE statement
- **Include proper WHERE clause** to target specific records
- **Use realistic sample data** that fits the schema constraints
- **Use proper data types** (strings in quotes, numbers without quotes, dates in proper format)

### Input:
Generate a SQL UPDATE query for the request `{english_question}`.
This query will be based on a database whose schema is represented in this string:

{schema_info}

### Response:
Based on your instructions, here is the SQL UPDATE query I have generated for the request `{english_question}`:
```sql"""

        elif query_type == 'DELETE':
            sql_prompt = f"""### Instructions:
Your task is to convert a request into a SQL DELETE query, given a MySQL database schema.
Adhere to these rules:
- **Deliberately go through the request and database schema word by word** to create appropriate DELETE statement
- **Include proper WHERE clause** to target specific records (NEVER create DELETE without WHERE unless explicitly requested)
- **Be careful with foreign key constraints** - consider the impact on related tables

### Input:
Generate a SQL DELETE query for the request `{english_question}`.
This query will be based on a database whose schema is represented in this string:

{schema_info}

### Response:
Based on your instructions, here is the SQL DELETE query I have generated for the request `{english_question}`:
```sql"""

        result = sql_llm.invoke(sql_prompt)
        # sql_query = result.strip() # Ollama 모델
        sql_query = result.content.strip()  # Gemini 모델

        # SQLCoder 형식 정리 - 더 강력한 정리 로직
        # 1. 코드 블록 마커 제거
        sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'^```\s*', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'\s*```\s*$', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'```', '', sql_query)  # 남은 모든 ``` 제거

        # 2. 불필요한 설명 제거
        lines = sql_query.split('\n')
        sql_lines = []
        for line in lines:
            line = line.strip()
            # SQL 쿼리 라인만 유지
            if (line and
                not line.startswith('--') and
                not line.lower().startswith('based on') and
                not line.lower().startswith('here is') and
                not line.lower().startswith('the sql') and
                    not line.lower().startswith('this query')):
                sql_lines.append(line)

        sql_query = '\n'.join(sql_lines).strip()

        # 3. 세미콜론으로 끝나도록 보장
        if sql_query and not sql_query.endswith(';'):
            sql_query += ';'

        print(f"✅ SQL 생성 완료: {sql_query[:50]}...")
        return sql_query

    except Exception as e:
        print(f"❌ SQL 생성 실패: {e}")
        return None


def execute_sql_and_format(sql_query, query_type='SELECT'):
    """SQL 실행 및 결과 포맷팅 - SELECT만 실행, 나머지는 쿼리만 표시"""
    try:
        if query_type == 'SELECT':
            print(f"🔍 SQL 실행: {sql_query}")
            result = db.run(sql_query)
            print(f"✅ 실행 성공")

            # 결과를 읽기 쉽게 포맷팅
            if isinstance(result, str):
                return result
            elif isinstance(result, list) and result:
                if isinstance(result[0], tuple):
                    # 튜플 리스트를 테이블 형태로 변환
                    formatted_result = []
                    for row in result[:10]:  # 상위 10개만
                        formatted_result.append(
                            " | ".join(str(item) for item in row))
                    return "\n".join(formatted_result)

            return str(result)

        else:
            # INSERT, UPDATE, DELETE는 실행하지 않고 쿼리만 표시
            print(f"⚠️ {query_type} 쿼리는 실행하지 않습니다 (안전을 위해)")
            return f"✅ {query_type} 쿼리가 생성되었습니다.\n실제 실행을 원하시면 직접 데이터베이스에서 실행해주세요.\n\n생성된 쿼리:\n{sql_query}"

    except Exception as e:
        print(f"❌ SQL 실행 실패: {e}")
        return f"오류: {e}"


def process_single_question(question):
    """단일 질문 처리"""
    print(f"\n🔍 질문 처리: {question}")

    # 1. 번역 (필요시)
    if is_korean(question):
        english_question = translate_to_english(question)
    else:
        english_question = question
        print(f"🔤 영어 질문 감지: {english_question}")

    # 2. 쿼리 타입 감지
    query_type = detect_query_type(english_question)

    # 3. SQL 생성
    sql_query = generate_sql_direct(english_question)
    if not sql_query:
        return {
            'question': question,
            'english_question': english_question,
            'query_type': query_type,
            'sql_query': None,
            'result': "SQL 생성 실패",
            'success': False
        }

    # 4. SQL 실행 (SELECT만 실행, 나머지는 쿼리만 표시)
    result = execute_sql_and_format(sql_query, query_type)

    return {
        'question': question,
        'english_question': english_question,
        'query_type': query_type,
        'sql_query': sql_query,
        'result': result,
        'success': True
    }


def process_question(question):
    """질문 처리 - 복수 질문 지원"""
    # 복수 질문 분리
    questions = split_multiple_questions(question)

    if len(questions) == 1:
        return process_single_question(questions[0])

    # 복수 질문 처리
    print(f"\n🔍 복수 질문 감지: {len(questions)}개")
    results = []

    for i, q in enumerate(questions, 1):
        print(f"\n--- 질문 {i}/{len(questions)} ---")
        result = process_single_question(q)
        results.append(result)

    return {
        'question': question,
        'multiple_questions': True,
        'results': results,
        'success': all(r['success'] for r in results)
    }


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 간단한 하이브리드 SQL Agent")
    print("🎯 Gemini(번역) + Gemini(SQL)")
    print("="*50)
    print("💡 예시 질문:")
    print("   📊 SELECT: 영화가 몇 개 있나요? / 고객 수를 보여주세요")
    print("   ➕ INSERT: 새로운 영화를 추가해주세요 / Add a new customer")
    print("   ✏️ UPDATE: 영화 제목을 수정해주세요 / Update customer information")
    print("   🗑️ DELETE: 영화를 삭제해주세요 / Remove old records")
    print("   🌐 영어도 가능: How many films are there?")
    print("-"*50)

    # 명령행 인수가 있으면 해당 질문 처리
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        result = process_question(question)

        print(f"\n📊 결과:")

        if result.get('multiple_questions'):
            # 복수 질문 결과 출력
            for i, sub_result in enumerate(result['results'], 1):
                print(f"\n--- 결과 {i} ---")
                if sub_result['english_question'] != sub_result['question']:
                    print(f"번역: {sub_result['english_question']}")
                print(f"쿼리 타입: {sub_result.get('query_type', 'SELECT')}")
                print(f"SQL: {sub_result['sql_query']}")
                print(f"결과:\n{sub_result['result']}")
        else:
            # 단일 질문 결과 출력
            if result['english_question'] != result['question']:
                print(f"번역: {result['english_question']}")
            print(f"쿼리 타입: {result.get('query_type', 'SELECT')}")
            print(f"SQL: {result['sql_query']}")
            print(f"결과:\n{result['result']}")

    else:
        # 대화형 모드
        while True:
            try:
                question = input("\n❓ 질문 (quit=종료): ").strip()

                if question.lower() in ['quit', 'q', 'exit']:
                    break

                if not question:
                    continue

                result = process_question(question)

                print(f"\n📊 결과:")

                if result.get('multiple_questions'):
                    # 복수 질문 결과 출력
                    for i, sub_result in enumerate(result['results'], 1):
                        print(f"\n--- 결과 {i} ---")
                        if sub_result['english_question'] != sub_result['question']:
                            print(f"번역: {sub_result['english_question']}")
                        print(
                            f"쿼리 타입: {sub_result.get('query_type', 'SELECT')}")
                        print(f"SQL: {sub_result['sql_query']}")
                        print(f"결과:\n{sub_result['result']}")
                else:
                    # 단일 질문 결과 출력
                    if result['english_question'] != result['question']:
                        print(f"번역: {result['english_question']}")
                    print(f"쿼리 타입: {result.get('query_type', 'SELECT')}")
                    print(f"SQL: {result['sql_query']}")
                    print(f"결과:\n{result['result']}")

                print("-"*50)

            except KeyboardInterrupt:
                print("\n👋 종료")
                break
            except EOFError:
                print("\n⚠️ 입력 스트림 종료됨. 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
                if "EOF" in str(e):
                    print("⚠️ 입력 오류가 반복됩니다. 프로그램을 종료합니다.")
                    break
