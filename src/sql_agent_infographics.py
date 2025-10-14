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
from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv(override=True)


# LLM 설정
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
# llm = OllamaLLM(model="gemma3:latest", base_url="http://localhost:11434")

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
    # agent_type="openai-tools",
    agent_type="zero-shot-react-description",  # Ollama 호환
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
                print(f"📊 데이터 미리보기:\n{df.head()}")

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
                        print(f"📊 데이터 미리보기:\n{df.head()}")

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
                            print(f"📊 데이터 미리보기:\n{df.head()}")

                except Exception as e2:
                    print(f"⚠️ 대안 파싱도 실패: {e2}")

        if df is None or df.empty:
            print("⚠️ DataFrame 생성 실패")
            return None

        # 숫자 컬럼 변환
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
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
            print(f"\n📊 인포그래픽 생성 완료!")
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
    # ANSI 색상 코드 제거
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned_text = ansi_escape.sub('', captured_text)

    patterns = [
        # LangChain SQL Agent 패턴들
        r"Invoking: `sql_db_query` with `\\{'query': '([^']+)'\\}`",
        r'Action Input:\s*(SELECT[^}]+?)(?:\n|$)',
        r'sql_db_query.*?query["\']:\s*["\']([^"\']+)["\']',
        r'query.*?["\']([^"\']*SELECT[^"\']*)["\']',
        # 순수 SQL 패턴
        r'(SELECT\s+[^;]+?)(?:;|\n|$)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
        if matches:
            for match in matches:
                # 문자열 정리
                clean_match = match.strip()

                # ANSI 코드 다시 제거
                clean_match = ansi_escape.sub('', clean_match)

                # Action/Thought 등 Agent 키워드 제거
                agent_keywords = ['Action:', 'Thought:',
                                  'Observation:', 'Final Answer:', 'Action Input:']
                for keyword in agent_keywords:
                    if keyword in clean_match:
                        clean_match = clean_match.split(keyword)[0].strip()

                # SELECT로 시작하는지 확인
                if clean_match.upper().startswith('SELECT'):
                    # 줄바꿈을 공백으로 변경하고 여러 공백을 하나로
                    clean_match = re.sub(r'\s+', ' ', clean_match)
                    return clean_match.strip()

    return None


def extract_all_sql_from_agent_output(captured_text):
    """Agent 출력에서 모든 SQL 쿼리 추출"""
    patterns = [
        r"Invoking: `sql_db_query` with `\\{'query': '([^']+)'\\}`",
        r'query.*?["\']([^"\']*SELECT[^"\']*)["\']',
    ]

    all_queries = []

    for pattern in patterns:
        matches = re.findall(pattern, captured_text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if match.strip().upper().startswith('SELECT'):
                query = match.strip()
                if query not in all_queries:  # 중복 제거
                    all_queries.append(query)

    return all_queries


def process_multiple_questions(questions_list):
    """다중 질문을 처리하고 각각의 SQL 쿼리와 결과를 반환"""
    results = []

    for i, question in enumerate(questions_list, 1):
        print(f"\n🔍 질문 {i}/{len(questions_list)}: {question}")
        print("🤔 처리 중...")

        try:
            # Agent 실행 (출력 캡처)
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                result = agent_executor.invoke({"input": question})
            finally:
                sys.stdout = old_stdout

            captured_text = captured_output.getvalue()

            # SQL 쿼리 추출
            sql_query = extract_sql_from_agent_output(captured_text)

            if sql_query:
                results.append({
                    'question': question,
                    'answer': result['output'],
                    'sql_query': sql_query,
                    'captured_text': captured_text
                })
                print(f"✅ 질문 {i} 처리 완료")
                print(f"📝 실행된 SQL: {sql_query}")
            else:
                print(f"⚠️ 질문 {i}: SQL 쿼리를 찾을 수 없습니다.")
                results.append({
                    'question': question,
                    'answer': result['output'],
                    'sql_query': None,
                    'captured_text': captured_text
                })

        except Exception as e:
            print(f"❌ 질문 {i} 처리 중 오류: {e}")
            results.append({
                'question': question,
                'answer': f"오류 발생: {e}",
                'sql_query': None,
                'captured_text': ""
            })

    return results


def generate_data_analysis(df, question, chart_type):
    """데이터 분석 코멘트 생성"""
    try:
        # 데이터 요약 정보 생성
        data_summary = f"데이터 행 수: {len(df)}, 컬럼 수: {len(df.columns)}"

        # 숫자 컬럼 통계
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            for col in numeric_cols:
                stats = df[col].describe()
                data_summary += f"\n{col} 통계: 평균 {stats['mean']:.2f}, 최대 {stats['max']:.2f}, 최소 {stats['min']:.2f}"

        # 상위 데이터 정보
        if len(df) > 0:
            top_data = df.head(3).to_string(index=False)
            data_summary += f"\n상위 3개 데이터:\n{top_data}"

        # LLM을 사용한 분석 생성
        analysis_prompt = f"""
다음 데이터 분석 결과에 대해 간단하고 명확한 인사이트를 제공해주세요:

질문: {question}
차트 유형: {chart_type}
데이터 요약: {data_summary}

다음 형식으로 답변해주세요:
1. 주요 발견사항 (2-3줄)
2. 데이터 특징 (1-2줄)
3. 비즈니스 시사점 (1-2줄)

간결하고 실용적인 분석을 제공해주세요.
"""

        try:
            analysis_result = llm.invoke(analysis_prompt)
            return analysis_result.content.strip()
        except Exception as e:
            print(f"⚠️ LLM 분석 생성 실패: {e}")
            return f"데이터 분석: {chart_type} 형태로 {len(df)}개의 데이터를 시각화했습니다."

    except Exception as e:
        print(f"⚠️ 데이터 분석 생성 오류: {e}")
        return "데이터 분석을 생성할 수 없습니다."


def validate_and_clean_sql(sql_query):
    """SQL 쿼리 유효성 검사 및 정리"""
    if not sql_query:
        return None

    # ANSI 색상 코드 제거
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_sql = ansi_escape.sub('', sql_query)

    # 마크다운 코드 블록 표시 제거
    clean_sql = re.sub(r'```sql.*?```', '', clean_sql, flags=re.DOTALL)
    clean_sql = re.sub(r'```.*?```', '', clean_sql, flags=re.DOTALL)
    clean_sql = re.sub(r'```sql', '', clean_sql)
    clean_sql = re.sub(r'```', '', clean_sql)

    # 줄바꿈과 여러 공백 정리
    clean_sql = re.sub(r'\s+', ' ', clean_sql).strip()

    # SELECT로 시작하는지 확인
    if not clean_sql.upper().startswith('SELECT'):
        return None

    # 기본적인 SQL 구문 확인
    required_keywords = ['SELECT', 'FROM']
    clean_sql_upper = clean_sql.upper()

    for keyword in required_keywords:
        if keyword not in clean_sql_upper:
            return None

    # 세미콜론 제거 (MySQL에서는 세미콜론이 없어도 됨)
    clean_sql = clean_sql.rstrip(';')

    return clean_sql


def create_chart_figure(sql_query, question, chart_index):
    """개별 차트 Figure 객체 생성"""
    try:
        print(f"📊 차트 {chart_index} 데이터 처리 중: {question}")

        # SQL 쿼리 유효성 검사 및 정리
        clean_sql = validate_and_clean_sql(sql_query)
        if not clean_sql:
            print(f"⚠️ 유효하지 않은 SQL 쿼리: {sql_query}")
            return None, "오류", "유효하지 않은 SQL 쿼리입니다."

        print(f"🔍 정리된 SQL: {clean_sql}")

        # SQL 쿼리 직접 실행
        result = db.run(clean_sql)

        # DataFrame 변환 (기존 로직 재사용)
        df = None

        if isinstance(result, list) and result:
            if isinstance(result[0], tuple):
                num_cols = len(result[0])
                if num_cols == 2:
                    columns = ['name', 'value']
                elif num_cols == 3:
                    columns = ['col1', 'col2', 'col3']
                else:
                    columns = [f'col_{i+1}' for i in range(num_cols)]

                df = pd.DataFrame(result, columns=columns)

        elif isinstance(result, str):
            # 문자열 결과 파싱 (기존 로직)
            try:
                def decimal_replacer(match):
                    return match.group(1)

                cleaned_result = re.sub(
                    r"Decimal\('([^']+)'\)", decimal_replacer, result)

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

            except Exception as e:
                # 정규식 대안 파싱
                try:
                    pattern = r"\('([^']+)',\s*'([^']+)',\s*(?:Decimal\('([^']+)'\)|(\d+(?:\.\d+)?))\)"
                    matches = re.findall(pattern, result)

                    if matches:
                        data = []
                        for match in matches:
                            name1, name2, decimal_val, regular_val = match
                            value = float(decimal_val) if decimal_val else float(
                                regular_val)
                            data.append((name1, name2, value))

                        if data:
                            df = pd.DataFrame(
                                data, columns=['col1', 'col2', 'col3'])
                except Exception:
                    pass

        if df is None or df.empty:
            return None

        # 숫자 컬럼 변환
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        # 데이터 타입 분석
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=['object']).columns.tolist()

        # 차트 생성
        fig = None
        chart_type = ""

        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # 막대 차트
            if len(df.columns) == 3 and len(categorical_cols) == 2:
                df['full_name'] = df[categorical_cols[0]] + \
                    ' ' + df[categorical_cols[1]]
                x_col = 'full_name'
                y_col = numeric_cols[0]
            else:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]

            fig = px.bar(
                df.head(15),
                x=x_col,
                y=y_col,
                title=f"[{chart_index}] {question}",
                color=y_col,
                color_continuous_scale='viridis'
            )
            chart_type = "막대 차트"

        elif len(categorical_cols) >= 1:
            # 파이 차트
            value_counts = df[categorical_cols[0]].value_counts().head(10)
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"[{chart_index}] {question}"
            )
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
            fig.update_layout(title=f"[{chart_index}] {question}")
            chart_type = "테이블"

        if fig:
            fig.update_layout(
                title_font_size=14,
                height=500,
                margin=dict(t=80, b=50, l=50, r=50)
            )

            if chart_type == "막대 차트":
                fig.update_xaxes(tickangle=45)

        # 데이터 분석 생성
        analysis = generate_data_analysis(df, question, chart_type)

        print(f"✅ 차트 {chart_index} 생성 완료 ({chart_type})")
        return fig, chart_type, analysis

    except Exception as e:
        print(f"❌ 차트 {chart_index} 생성 오류: {e}")
        return None, "오류", "분석을 생성할 수 없습니다."


def markdown_to_html(text):
    """간단한 마크다운을 HTML로 변환"""
    if not text:
        return text

    # 줄바꿈을 <br>로 변환하기 전에 마크다운 처리
    lines = text.split('\n')
    html_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
            continue

        # 헤더 변환
        if line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        # 볼드 텍스트 변환
        elif '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html_lines.append(f'<p>{line}</p>')
        # 리스트 아이템 변환
        elif line.startswith('- ') or line.startswith('* '):
            html_lines.append(f'<li>{line[2:]}</li>')
        # 일반 텍스트
        else:
            html_lines.append(f'<p>{line}</p>')

    # 연속된 <li> 태그를 <ul>로 감싸기
    result = []
    in_list = False

    for line in html_lines:
        if line.startswith('<li>'):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(line)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)

    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


def generate_comprehensive_analysis(chart_info):
    """모든 차트 결과를 종합한 분석 의견 생성"""
    try:
        # 차트 정보 요약
        summary = f"총 {len(chart_info)}개의 분석 결과:\n"
        for info in chart_info:
            summary += f"- {info['question']} ({info['chart_type']})\n"

        # 개별 분석 내용 수집
        individual_analyses = "\n\n".join([
            f"[분석 {info['index']}] {info['question']}\n{info['analysis']}"
            for info in chart_info
        ])

        # LLM을 사용한 종합 분석 생성
        comprehensive_prompt = f"""
다음은 여러 데이터 분석 결과입니다. 이를 종합하여 전체적인 인사이트와 권장사항을 제공해주세요:

{summary}

개별 분석 결과:
{individual_analyses}

다음 형식으로 종합 의견을 작성해주세요:
1. 전체 데이터 트렌드 요약 (3-4줄)
2. 주요 인사이트 (3-4개 포인트)
3. 비즈니스 권장사항 (2-3개 포인트)
4. 추가 분석 제안 (1-2개 포인트)

실용적이고 구체적인 의견을 제공해주세요.
"""

        try:
            analysis_result = llm.invoke(comprehensive_prompt)
            return analysis_result.content.strip()
        except Exception as e:
            print(f"⚠️ 종합 분석 생성 실패: {e}")
            return f"총 {len(chart_info)}개의 차트를 통해 다양한 데이터 인사이트를 확인할 수 있습니다."

    except Exception as e:
        print(f"⚠️ 종합 분석 생성 오류: {e}")
        return "종합 분석을 생성할 수 없습니다."


def create_multiple_infographics(results):
    """다중 결과를 하나의 대시보드 HTML 파일로 생성"""
    print(f"\n🎨 === 통합 대시보드 생성 시작 ===")
    print(f"📊 총 {len(results)}개의 결과를 처리합니다.")

    valid_results = [r for r in results if r['sql_query']]

    if not valid_results:
        print("⚠️ 유효한 결과가 없습니다.")
        return []

    # 각 차트 생성
    figures = []
    chart_info = []

    for i, result in enumerate(valid_results, 1):
        fig, chart_type, analysis = create_chart_figure(
            result['sql_query'],
            result['question'],
            i
        )

        if fig:
            figures.append(fig)
            chart_info.append({
                'question': result['question'],
                'chart_type': chart_type,
                'analysis': analysis,
                'index': i
            })

    if not figures:
        print("⚠️ 생성된 차트가 없습니다.")
        return []

    # 종합 의견 생성
    print("🤔 종합 분석 의견 생성 중...")
    comprehensive_analysis = generate_comprehensive_analysis(chart_info)

    # 통합 HTML 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'{infographic_dir}/dashboard_{timestamp}.html'

    # HTML 헤더 생성
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SQL Agent 다중 쿼리 대시보드</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                text-align: center;
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .chart-container {{
                background-color: white;
                margin: 20px 0;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .chart-info {{
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
                font-size: 14px;
            }}
            .summary {{
                background-color: #3498db;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .analysis {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
                border-left: 4px solid #17a2b8;
                font-size: 14px;
                line-height: 1.6;
            }}
            .comprehensive-analysis {{
                background-color: #e8f5e8;
                padding: 20px;
                border-radius: 10px;
                margin: 30px 0;
                border-left: 5px solid #28a745;
            }}
            .comprehensive-analysis h3 {{
                color: #155724;
                margin-top: 0;
            }}
            .analysis h1, .analysis h2, .analysis h3 {{
                color: #17a2b8;
                margin-top: 15px;
                margin-bottom: 10px;
            }}
            .analysis ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .analysis li {{
                margin: 5px 0;
            }}
            .analysis p {{
                margin: 8px 0;
            }}
            .comprehensive-analysis h1, .comprehensive-analysis h2, .comprehensive-analysis h3 {{
                color: #155724;
                margin-top: 15px;
                margin-bottom: 10px;
            }}
            .comprehensive-analysis ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .comprehensive-analysis li {{
                margin: 5px 0;
            }}
            .comprehensive-analysis p {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 SQL Agent 다중 쿼리 대시보드</h1>
            <p>생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h3>📊 대시보드 요약</h3>
            <p>총 {len(figures)}개의 차트가 생성되었습니다.</p>
            <ul>
    """

    # 요약 정보 추가
    for info in chart_info:
        html_content += f"<li>차트 {info['index']}: {info['chart_type']} - {info['question']}</li>\n"

    html_content += """
            </ul>
        </div>
    """

    # 종합 분석 의견 추가 (마크다운을 HTML로 변환)
    comprehensive_analysis_html = markdown_to_html(comprehensive_analysis)
    html_content += f"""
        <div class="comprehensive-analysis">
            <h3>🎯 종합 분석 의견</h3>
            <div>{comprehensive_analysis_html}</div>
        </div>
    """

    # 각 차트를 HTML에 추가
    for i, (fig, info) in enumerate(zip(figures, chart_info)):
        div_id = f"chart_{i+1}"

        html_content += f"""
        <div class="chart-container">
            <div class="chart-info">
                <strong>차트 {info['index']}: {info['chart_type']}</strong><br>
                질문: {info['question']}
            </div>
            <div id="{div_id}"></div>
            <div class="analysis">
                <strong>📊 데이터 분석:</strong><br>
                <div>{markdown_to_html(info['analysis'])}</div>
            </div>
        </div>
        """

    # JavaScript 코드 추가
    html_content += "\n<script>\n"

    for i, fig in enumerate(figures):
        div_id = f"chart_{i+1}"
        # Plotly 차트를 JSON으로 변환
        fig_json = fig.to_json()
        html_content += f"""
        var fig_{i+1} = {fig_json};
        Plotly.newPlot('{div_id}', fig_{i+1}.data, fig_{i+1}.layout);
        """

    html_content += """
    </script>
    </body>
    </html>
    """

    # 파일 저장
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n📊 통합 대시보드 생성 완료!")
        print(f"📁 파일: {filename}")
        print(f"📈 포함된 차트: {len(figures)}개")
        print(
            f"📋 차트 유형: {', '.join([info['chart_type'] for info in chart_info])}")

        return [{
            'question': '통합 대시보드',
            'file': filename,
            'index': 'ALL',
            'chart_count': len(figures)
        }]

    except Exception as e:
        print(f"❌ 파일 저장 오류: {e}")
        return []


def parse_multiple_questions(input_text):
    """입력 텍스트에서 다중 질문을 파싱"""
    # 구분자로 질문들을 분리
    separators = ['\n', ';', '|', ',']

    questions = [input_text]  # 기본값은 단일 질문

    for sep in separators:
        if sep in input_text:
            questions = [q.strip() for q in input_text.split(sep) if q.strip()]
            break

    # 번호가 있는 질문 형태 처리 (1. 질문1 2. 질문2)
    numbered_pattern = r'^\d+\.\s*(.+)'
    if any(re.match(numbered_pattern, q.strip()) for q in questions):
        questions = [re.sub(numbered_pattern, r'\1', q.strip())
                     for q in questions]

    return [q for q in questions if q]  # 빈 문자열 제거


print("✅ 다중 쿼리 SQL Agent with 인포그래픽이 준비되었습니다!")

# 메인 대화 루프
print("=" * 60)
print("🤖 SQL Agent와 대화하기 (다중 쿼리 인포그래픽)")
print("=" * 60)
print("💡 단일 질문 예시:")
print("   - 각 카테고리별 영화 수를 알려주세요")
print("   - 고객별 총 결제 금액 상위 10명을 보여주세요")
print("")
print("💡 다중 질문 예시 (구분자: 줄바꿈, 세미콜론, 파이프, 쉼표):")
print("   - 각 카테고리별 영화 수를 알려주세요, 고객별 총 결제 금액 상위 10명을 보여주세요, 가장 많이 대여된 영화 5개는?")
print("")
print("   또는: 질문1; 질문2; 질문3")
print("   또는: 1. 질문1 2. 질문2 3. 질문3")
print("")
print("🎨 사용법:")
print("   1. 단일 또는 다중 질문을 입력하세요")
print("   2. Agent가 각 질문에 대해 답변을 제공합니다")
print("   3. 'y'를 입력하면 모든 결과에 대해 인포그래픽을 생성합니다")
print("   4. 'multi:'로 시작하면 강제로 다중 모드로 처리합니다")
print("   5. 'quit'를 입력하면 종료합니다")
print("-" * 60)

while True:
    try:
        user_input = input("\n❓ 질문을 입력하세요 (다중 질문 가능): ").strip()

        if user_input.lower() in ['quit', 'exit', '종료', 'q']:
            print("👋 대화를 종료합니다.")
            break

        if not user_input:
            print("⚠️ 질문을 입력해주세요.")
            continue

        # 다중 질문 파싱
        force_multi = user_input.startswith('multi:')
        if force_multi:
            user_input = user_input[6:].strip()  # 'multi:' 제거

        questions = parse_multiple_questions(user_input)

        print(f"\n🔍 감지된 질문 수: {len(questions)}")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")

        # 단일 질문 처리
        if len(questions) == 1 and not force_multi:
            question = questions[0]
            print(f"\n🔍 단일 질문 처리: {question}")
            print("🤔 처리 중...")

            # Agent 실행 (출력 캡처)
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                result = agent_executor.invoke({"input": question})
            finally:
                sys.stdout = old_stdout

            captured_text = captured_output.getvalue()

            print(f"\n✅ 답변:")
            print(result['output'])

            # SQL 쿼리 추출
            sql_query = extract_sql_from_agent_output(captured_text)

            if sql_query:
                print(f"\n📝 실행된 SQL: {sql_query}")

                create_chart = input(
                    "\n🎨 인포그래픽을 생성하시겠습니까? (y/n): ").strip().lower()

                if create_chart in ['y', 'yes', '네', 'ㅇ']:
                    print("\n🎨 인포그래픽 생성 중...")

                    infographic_file = create_infographic_from_sql_query(
                        sql_query, question)

                    if infographic_file:
                        print("✨ 생성 완료! 파일을 더블클릭해서 브라우저에서 확인하세요.")
                    else:
                        print("⚠️ 인포그래픽 생성에 실패했습니다.")
            else:
                print("\n⚠️ SQL 쿼리를 찾을 수 없어 인포그래픽을 생성할 수 없습니다.")

        # 다중 질문 처리
        else:
            print(f"\n🔍 다중 질문 처리 모드 ({len(questions)}개 질문)")

            # 모든 질문 처리
            results = process_multiple_questions(questions)

            # 결과 요약 출력
            print(f"\n📊 === 처리 결과 요약 ===")
            valid_results = [r for r in results if r['sql_query']]
            print(f"✅ 성공: {len(valid_results)}개")
            print(f"⚠️ 실패: {len(results) - len(valid_results)}개")

            # 각 결과 출력
            for i, result in enumerate(results, 1):
                print(f"\n--- 질문 {i} ---")
                print(f"❓ {result['question']}")
                print(f"✅ {result['answer']}")
                if result['sql_query']:
                    print(f"📝 SQL: {result['sql_query']}")

            if valid_results:
                create_charts = input(
                    f"\n🎨 {len(valid_results)}개의 인포그래픽을 생성하시겠습니까? (y/n): ").strip().lower()

                if create_charts in ['y', 'yes', '네', 'ㅇ']:
                    print(f"\n🎨 다중 인포그래픽 생성 중...")

                    created_files = create_multiple_infographics(results)

                    if created_files:
                        dashboard_info = created_files[0]
                        print(f"\n✨ 통합 대시보드가 생성되었습니다!")
                        print(f"📁 파일: {dashboard_info['file']}")
                        print(f"📊 포함된 차트: {dashboard_info['chart_count']}개")
                        print("\n💡 파일을 더블클릭해서 브라우저에서 확인하세요.")
                    else:
                        print("⚠️ 대시보드 생성에 실패했습니다.")
            else:
                print("\n⚠️ 유효한 SQL 쿼리가 없어 인포그래픽을 생성할 수 없습니다.")

        print("\n" + "="*60)

    except KeyboardInterrupt:
        print("\n\n👋 사용자가 중단했습니다.")
        break
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("다시 시도해주세요.")
