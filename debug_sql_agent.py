#!/usr/bin/env python3
"""
SQL Agent 디버깅 스크립트
"""

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv(override=True)


# 1. 환경 변수 확인
print("=== 환경 변수 확인 ===")
required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST',
                 'DB_PORT', 'DB_NAME', 'GOOGLE_API_KEY']
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {'*' * len(value)}")
    else:
        print(f"❌ {var}: 설정되지 않음")

# 2. LLM 초기화 테스트
print("\n=== LLM 초기화 테스트 ===")
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    print("✅ LLM 초기화 성공")
except Exception as e:
    print(f"❌ LLM 초기화 실패: {e}")
    exit(1)

# 3. 데이터베이스 연결 테스트
print("\n=== 데이터베이스 연결 테스트 ===")
try:
    db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    db = SQLDatabase.from_uri(db_uri)
    print(f"✅ DB 연결 성공: {db.dialect}")
    print(f"✅ 테이블 목록: {db.get_usable_table_names()}")
except Exception as e:
    print(f"❌ DB 연결 실패: {e}")
    exit(1)

# 4. SQL Agent 생성 테스트
print("\n=== SQL Agent 생성 테스트 ===")
try:
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True
    )
    print("✅ SQL Agent 생성 성공")
except Exception as e:
    print(f"❌ SQL Agent 생성 실패: {e}")
    exit(1)

# 5. 간단한 쿼리 테스트
print("\n=== 간단한 쿼리 테스트 ===")
test_questions = [
    "데이터베이스에 어떤 테이블들이 있나요?",
    "actor 테이블에서 첫 3개 행을 보여주세요"
]

for question in test_questions:
    print(f"\n🔍 질문: {question}")
    try:
        result = agent_executor.invoke({"input": question})
        print(f"✅ 답변: {result.get('output', '답변 없음')}")
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

print("\n=== 디버깅 완료 ===")
