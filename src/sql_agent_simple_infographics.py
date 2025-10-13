"""
간단하고 확실한 SQL Agent with 인포그래픽
"""
import sys
from io import StringIO
import re
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv(override=True)


# LLM 설정
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# MySQL 연결 설정
db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    db = SQLDatabase.from_uri(db_uri)
    print(f"✅ 데이터베이스 연결 성공")
    print(f"📊 사용 가능한 테이블: {db.get_usable_table_names()}")
except Exception as e:
    print(f"❌ 데이터베이스 연결 실패: {e}")
    exit(1)

# SQL Agent 생성
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=True
)

# 인포그래픽 디렉토리 생성
infographic_dir = "infographics"
if not os.path.exists(infographic_dir):
    os.makedirs(infographic_dir)


def create_infographic_from_sql_query(sql_query, question):
    """
    SQL 쿼리를 직접 실행하고 인포그래픽 생성
    """
    try:
        print(f"\n🔍 === 인포그래픽 생성 시작 ===")
        print(f"📝 SQL 쿼리: {sql_query}")

        # SQL 쿼리 직접 실행
        result = db.run(sql_query)
        print(f"🔍 쿼리 결과 타입: {type(result)}")
        print(f"🔍 쿼리 결과: {result}")

        # DataFrame 변환
        df = None

        if isinstance(result, list) and result:
            if isinstance(result[0], tuple):
                # 컬럼 수에 따라 적절한 컬럼명 생성
                num_cols = len(result[0])
                if num_cols == 2:
                    columns = ['name', 'value']
                elif num_cols == 3:
                    columns = ['col1', 'col2', 'col3']
                else:
                    columns = [f'col_{i+1}' for i in range(num_cols)]

                df = pd.DataFrame(result, columns=columns)
                print(f"✅ DataFrame 생성 성공: {df.shape}")
                print(f"📊 데이터 미리보기:\\n{df.head()}")

        elif isinstance(result, str):
            # 문자열 결과 파싱 (Decimal 객체 처리 포함)
            print("📝 문자열 결과 파싱 중...")
            try:
                # Decimal 객체를 처리하기 위한 안전한 파싱
                import re
                from decimal import Decimal

                # Decimal('123.45') 패턴을 숫자로 변환
                def decimal_replacer(match):
                    return match.group(1)

                # Decimal 객체를 숫자 문자열로 변환
                cleaned_result = re.sub(
                    r"Decimal\('([^']+)'\)", decimal_replacer, result)
                print(f"🔧 Decimal 처리 후: {cleaned_result[:200]}...")

                import ast
                parsed_result = ast.literal_eval(cleaned_result)

                if isinstance(parsed_result, list) and parsed_result:
                    if isinstance(parsed_result[0], tuple):
                        num_cols = len(parsed_result[0])
                        if num_cols == 2:
                            columns = ['name', 'value']
                        elif num_cols == 3:
                            columns = ['col1', 'col2', 'col3']
                        else:
                            columns = [f'col_{i+1}' for i in range(num_cols)]

                        df = pd.DataFrame(parsed_result, columns=columns)
                        print(f"✅ 문자열 파싱으로 DataFrame 생성 성공: {df.shape}")
                        print(f"📊 데이터 미리보기:\\n{df.head()}")

            except Exception as e:
                print(f"⚠️ 문자열 파싱 실패: {e}")
                # 대안: 정규식으로 직접 파싱 시도
                print("🔄 대안 파싱 방법 시도 중...")
                try:
                    import re
                    # 튜플 패턴 찾기: ('값1', '값2', 숫자)
                    pattern = r"\('([^']+)',\s*'([^']+)',\s*(?:Decimal\('([^']+)'\)|(\d+(?:\.\d+)?))\)"
                    matches = re.findall(pattern, result)

                    if matches:
                        data = []
                        for match in matches:
                            # match는 (name1, name2, decimal_value, regular_number) 형태
                            name1, name2, decimal_val, regular_val = match
                            value = float(decimal_val) if decimal_val else float(
                                regular_val)
                            data.append((name1, name2, value))

                        if data:
                            df = pd.DataFrame(
                                data, columns=['col1', 'col2', 'col3'])
                            print(f"✅ 정규식 파싱으로 DataFrame 생성 성공: {df.shape}")
                            print(f"📊 데이터 미리보기:\\n{df.head()}")

                except Exception as e2:
                    print(f"⚠️ 대안 파싱도 실패: {e2}")

        if df is None or df.empty:
            print("⚠️ DataFrame 생성 실패")
            return None

        # 숫자 컬럼 변환
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass

        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 데이터 타입 분석
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=['object']).columns.tolist()

        print(f"📊 숫자 컬럼: {numeric_cols}")
        print(f"📊 카테고리 컬럼: {categorical_cols}")

        # 차트 생성
        filename = None

        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # 3개 컬럼인 경우 (이름1, 이름2, 값) 처리
            if len(df.columns) == 3 and len(categorical_cols) == 2:
                # 이름 합치기 (예: "KARL SEAL")
                df['full_name'] = df[categorical_cols[0]] + \
                    ' ' + df[categorical_cols[1]]
                x_col = 'full_name'
                y_col = numeric_cols[0]
            else:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]

            # 막대 차트
            fig = px.bar(
                df.head(15),  # 상위 15개만
                x=x_col,
                y=y_col,
                title=question,
                color=y_col,
                color_continuous_scale='viridis'
            )

            fig.update_layout(
                title_font_size=16,
                height=600,
                margin=dict(t=100, b=100, l=50, r=50)
            )

            fig.update_xaxes(tickangle=45)

            filename = f'{infographic_dir}/chart_{timestamp}.html'
            fig.write_html(filename)
            chart_type = "막대 차트"

        elif len(categorical_cols) >= 1:
            # 파이 차트
            value_counts = df[categorical_cols[0]].value_counts().head(10)

            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=question
            )

            fig.update_layout(
                title_font_size=16,
                height=600
            )

            filename = f'{infographic_dir}/pie_{timestamp}.html'
            fig.write_html(filename)
            chart_type = "파이 차트"

        else:
            # 테이블
            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color='paleturquoise',
                    align='left'
                ),
                cells=dict(
                    values=[df[col] for col in df.columns],
                    fill_color='lavender',
                    align='left'
                )
            )])

            fig.update_layout(
                title=question,
                title_font_size=16,
                height=min(600, 50 + len(df) * 25)
            )

            filename = f'{infographic_dir}/table_{timestamp}.html'
            fig.write_html(filename)
            chart_type = "테이블"

        if filename:
            print(f"\\n📊 인포그래픽 생성 완료!")
            print(f"📁 파일: {filename}")
            print(f"📈 타입: {chart_type}")
            print(f"📋 크기: {len(df)}행 x {len(df.columns)}열")

        return filename

    except Exception as e:
        print(f"❌ 인포그래픽 생성 오류: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return None


def extract_sql_from_agent_output(captured_text):
    """Agent 출력에서 SQL 쿼리 추출"""
    patterns = [
        r"Invoking: `sql_db_query` with `\\{'query': '([^']+)'\\}`",
        r'query.*?["\']([^"\']*SELECT[^"\']*)["\']',
        r'SELECT[^;]+(?:;|$)'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, captured_text, re.DOTALL | re.IGNORECASE)
        if matches:
            # SELECT로 시작하는 쿼리만 반환
            for match in matches:
                if match.strip().upper().startswith('SELECT'):
                    return match.strip()

    return None


print("✅ 간단한 SQL Agent with 인포그래픽이 준비되었습니다!")

# 메인 대화 루프
print("=" * 60)
print("🤖 SQL Agent와 대화하기 (간단한 인포그래픽)")
print("=" * 60)
print("💡 예시 질문:")
print("   - 각 카테고리별 영화 수를 알려주세요")
print("   - 고객별 총 결제 금액 상위 10명을 보여주세요")
print("   - 가장 많이 대여된 영화 5개는?")
print("")
print("🎨 사용법:")
print("   1. 질문을 입력하세요")
print("   2. Agent가 답변을 제공합니다")
print("   3. 'y'를 입력하면 인포그래픽을 생성합니다")
print("   4. 'quit'를 입력하면 종료합니다")
print("-" * 60)

while True:
    try:
        user_question = input("\\n❓ 질문을 입력하세요: ").strip()

        if user_question.lower() in ['quit', 'exit', '종료', 'q']:
            print("👋 대화를 종료합니다.")
            break

        if not user_question:
            print("⚠️ 질문을 입력해주세요.")
            continue

        print(f"\\n🔍 질문: {user_question}")
        print("🤔 처리 중...")

        # Agent 실행 (출력 캡처)
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            result = agent_executor.invoke({"input": user_question})
        finally:
            sys.stdout = old_stdout

        captured_text = captured_output.getvalue()

        print(f"\\n✅ 답변:")
        print(result['output'])

        # SQL 쿼리 추출
        sql_query = extract_sql_from_agent_output(captured_text)

        if sql_query:
            print(f"\\n📝 실행된 SQL: {sql_query[:100]}...")

            create_chart = input(
                "\\n🎨 인포그래픽을 생성하시겠습니까? (y/n): ").strip().lower()

            if create_chart in ['y', 'yes', '네', 'ㅇ']:
                print("\\n🎨 인포그래픽 생성 중...")

                infographic_file = create_infographic_from_sql_query(
                    sql_query, user_question)

                if infographic_file:
                    print("✨ 생성 완료! 파일을 더블클릭해서 브라우저에서 확인하세요.")
                else:
                    print("⚠️ 인포그래픽 생성에 실패했습니다.")
        else:
            print("\\n⚠️ SQL 쿼리를 찾을 수 없어 인포그래픽을 생성할 수 없습니다.")

        print("\\n" + "="*60)

    except KeyboardInterrupt:
        print("\\n\\n👋 사용자가 중단했습니다.")
        break
    except Exception as e:
        print(f"\\n❌ 오류 발생: {e}")
        print("다시 시도해주세요.")
