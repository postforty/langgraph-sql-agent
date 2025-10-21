"""
SQL Agent Gradio 챗봇
Gemini(번역) + CodeLlama(SQL생성) - 웹 인터페이스
"""
import gradio as gr
import sys
import os
from datetime import datetime

# 기존 SQL Agent 모듈 import
from sql_agent_simple_hybrid import (
    process_question,
    db,
    translator_llm,
    sql_llm
)


def format_sql_result(result):
    """SQL 결과를 Gradio용으로 포맷팅"""
    if result.get('multiple_questions'):
        # 복수 질문 처리
        response = "🔍 **복수 질문 처리 결과**\n\n"
        for i, sub_result in enumerate(result['results'], 1):
            response += f"### 질문 {i}: {sub_result['question']}\n"

            if sub_result['english_question'] != sub_result['question']:
                response += f"**번역**: {sub_result['english_question']}\n"

            response += f"**쿼리 타입**: {sub_result.get('query_type', 'SELECT')}\n"
            response += f"**SQL**:\n```sql\n{sub_result['sql_query']}\n```\n"
            response += f"**결과**:\n```\n{sub_result['result']}\n```\n\n"
            response += "---\n\n"
    else:
        # 단일 질문 처리
        response = f"🎯 **질문**: {result['question']}\n\n"

        if result['english_question'] != result['question']:
            response += f"🌐 **번역**: {result['english_question']}\n\n"

        query_type = result.get('query_type', 'SELECT')
        type_emoji = {
            'SELECT': '📊',
            'INSERT': '➕',
            'UPDATE': '✏️',
            'DELETE': '🗑️'
        }

        response += f"{type_emoji.get(query_type, '📊')} **쿼리 타입**: {query_type}\n\n"
        response += f"**SQL**:\n```sql\n{result['sql_query']}\n```\n\n"

        if query_type != 'SELECT':
            response += "⚠️ **안전 모드**: INSERT/UPDATE/DELETE 쿼리는 실행되지 않습니다.\n\n"

        response += f"**결과**:\n```\n{result['result']}\n```"

    return response


def chat_with_sql_agent(message, history):
    """Gradio 챗봇 메인 함수"""
    try:
        if not message.strip():
            return "❓ 질문을 입력해주세요."

        # SQL Agent로 질문 처리
        result = process_question(message)

        if not result['success']:
            return f"❌ 처리 실패: {result.get('result', '알 수 없는 오류')}"

        # 결과 포맷팅
        formatted_response = format_sql_result(result)
        return formatted_response

    except Exception as e:
        return f"❌ 오류가 발생했습니다: {str(e)}"


def get_database_info():
    """데이터베이스 정보 표시"""
    try:
        tables = db.get_usable_table_names()
        return f"📊 **연결된 데이터베이스**\n\n**테이블**: {', '.join(tables)}"
    except Exception as e:
        return f"❌ 데이터베이스 정보를 가져올 수 없습니다: {e}"

# Gradio 인터페이스 생성


def create_gradio_interface():
    """Gradio 인터페이스 생성"""

    # 예시 질문들
    examples = [
        "영화가 몇 개 있나요?",
        "고객 수를 보여주세요",
        "영화 카테고리별 개수를 알려주세요",
        "새로운 영화를 추가해주세요",
        "영화 제목을 수정해주세요",
        "오래된 데이터를 삭제해주세요",
        "How many films are there?",
        "Show me the top 5 customers"
    ]

    # 챗봇 인터페이스
    demo = gr.ChatInterface(
        fn=chat_with_sql_agent,
        title="🤖 SQL Agent 챗봇",
        description="""
        **자연어로 질문하면 SQL 쿼리를 생성하고 실행합니다**
        
        🔹 **지원 기능**: SELECT, INSERT, UPDATE, DELETE 쿼리 생성
        🔹 **언어 지원**: 한국어, 영어 모두 가능
        🔹 **안전 모드**: SELECT만 실행, 나머지는 쿼리만 생성
        
        💡 **사용법**: 아래 예시를 참고하거나 자유롭게 질문해보세요!
        """,
        examples=examples,
        cache_examples=False,
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            font-size: 14px !important;
        }
        """,
        additional_inputs=[],
        additional_inputs_accordion="⚙️ 설정"
    )

    return demo


def main():
    """메인 함수"""
    print("🚀 SQL Agent Gradio 챗봇 시작")
    print("="*50)

    # 데이터베이스 연결 확인
    try:
        tables = db.get_usable_table_names()
        print(f"✅ 데이터베이스 연결 성공")
        print(f"📊 사용 가능한 테이블: {tables}")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("⚠️ 데이터베이스 연결을 확인해주세요.")
        return

    # Gradio 인터페이스 생성 및 실행
    demo = create_gradio_interface()

    # 실행 옵션
    launch_options = {
        "share": False,  # 공개 링크 생성 여부
        "server_name": "0.0.0.0",  # 모든 IP에서 접근 가능
        "server_port": 7860,  # 포트 번호
        "show_error": True,  # 에러 표시
        "quiet": False  # 로그 표시
    }

    print("\n🌐 웹 인터페이스 시작 중...")
    print(f"📍 로컬 주소: http://localhost:{launch_options['server_port']}")

    # 공개 링크 옵션
    if len(sys.argv) > 1 and sys.argv[1] == "--share":
        launch_options["share"] = True
        print("🔗 공개 링크도 생성됩니다...")

    try:
        demo.launch(**launch_options)
    except KeyboardInterrupt:
        print("\n👋 서버 종료")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")


if __name__ == "__main__":
    main()
