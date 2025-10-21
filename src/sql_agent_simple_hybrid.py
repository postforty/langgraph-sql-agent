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

# SQL 생성용 CodeLlama
sql_llm = OllamaLLM(
    model="codeqwen:latest",
    temperature=0
)
print("✅ CodeLlama SQL 모델 로드 완료")

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


def generate_sql_direct(english_question):
    """CodeLlama로 직접 SQL 생성"""
    try:
        print(f"🔍 SQL 생성 중: {english_question}")

        # 동적으로 스키마 정보 가져오기
        schema_info = get_database_schema()

        # 스키마 정보가 너무 부족한 경우 경고
        if "Schema information is not available" in schema_info:
            print("⚠️ 스키마 정보 없이 SQL 생성 시도 - 결과가 부정확할 수 있습니다")

        sql_prompt = f"""### Instructions:
Your task is to convert a question into a SQL query, given a MySQL database schema.
Adhere to these rules:
- **Deliberately go through the question and database schema word by word** to appropriately answer the question
- **Use Table Aliases** to prevent ambiguity. For example, `SELECT f.title, a.first_name FROM film f JOIN film_actor fa ON f.film_id = fa.film_id JOIN actor a ON fa.actor_id = a.actor_id`.
- When creating a ratio, always cast the numerator as float

### Input:
Generate a SQL query that answers the question `{english_question}`.
This query will run on a database whose schema is represented in this string:

{schema_info}

-- Key Relationships for JOINs:
-- film_actor: connects film and actor tables
-- film_category: connects film and category tables  
-- rental: connects customer, inventory, and staff
-- payment: connects customer, staff, and rental
-- inventory: connects film and store

### Response:
Based on your instructions, here is the SQL query I have generated to answer the question `{english_question}`:
```sql"""

        result = sql_llm.invoke(sql_prompt)
        sql_query = result.strip()

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


def execute_sql_and_format(sql_query):
    """SQL 실행 및 결과 포맷팅"""
    try:
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

    # 2. SQL 생성
    sql_query = generate_sql_direct(english_question)
    if not sql_query:
        return {
            'question': question,
            'english_question': english_question,
            'sql_query': None,
            'result': "SQL 생성 실패",
            'success': False
        }

    # 3. SQL 실행
    result = execute_sql_and_format(sql_query)

    return {
        'question': question,
        'english_question': english_question,
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
    print("🎯 Gemini(번역) + CodeLlama(SQL)")
    print("="*50)
    print("💡 예시 질문:")
    print("   - 영화가 몇 개 있나요?")
    print("   - 고객 수를 보여주세요")
    print("   - 영화 카테고리별 개수를 보여주세요")
    print("   - How many films are there? (영어도 가능)")
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
                print(f"SQL: {sub_result['sql_query']}")
                print(f"결과:\n{sub_result['result']}")
        else:
            # 단일 질문 결과 출력
            if result['english_question'] != result['question']:
                print(f"번역: {result['english_question']}")
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
                        print(f"SQL: {sub_result['sql_query']}")
                        print(f"결과:\n{sub_result['result']}")
                else:
                    # 단일 질문 결과 출력
                    if result['english_question'] != result['question']:
                        print(f"번역: {result['english_question']}")
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
