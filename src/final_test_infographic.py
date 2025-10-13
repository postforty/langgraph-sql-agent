"""
최종 인포그래픽 테스트 - 실제 SQL 실행
"""
import re
from datetime import datetime
import plotly.express as px
import pandas as pd
from langchain_community.utilities import SQLDatabase
import os
from dotenv import load_dotenv
load_dotenv(override=True)


# 데이터베이스 연결
db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
db = SQLDatabase.from_uri(db_uri)


def create_infographic_from_sql_query(sql_query, question):
    """SQL 쿼리 실행 및 인포그래픽 생성"""
    try:
        print(f"🔍 SQL 실행: {sql_query}")

        # SQL 실행
        result = db.run(sql_query)
        print(f"🔍 결과 타입: {type(result)}")
        print(f"🔍 결과: {result}")

        # Decimal 처리
        if isinstance(result, str):
            def decimal_replacer(match):
                return match.group(1)

            cleaned_result = re.sub(
                r"Decimal\('([^']+)'\)", decimal_replacer, result)
            print(f"🔧 Decimal 처리 후: {cleaned_result}")

            import ast
            parsed_result = ast.literal_eval(cleaned_result)

            if isinstance(parsed_result, list) and parsed_result:
                num_cols = len(parsed_result[0])
                if num_cols == 2:
                    columns = ['name', 'value']
                elif num_cols == 3:
                    columns = ['col1', 'col2', 'col3']
                else:
                    columns = [f'col_{i+1}' for i in range(num_cols)]

                df = pd.DataFrame(parsed_result, columns=columns)
                print(f"✅ DataFrame 생성: {df.shape}")
                print(df)

                # 숫자 컬럼 변환
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass

                # 차트 생성
                if len(df.columns) == 3:
                    # 3컬럼: 이름 합치기
                    df['full_name'] = df['col1'] + ' ' + df['col2']
                    x_col = 'full_name'
                    y_col = 'col3'
                else:
                    # 2컬럼
                    x_col = 'name'
                    y_col = 'value'

                fig = px.bar(
                    df,
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

                # 파일 저장
                infographic_dir = "infographics"
                if not os.path.exists(infographic_dir):
                    os.makedirs(infographic_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'{infographic_dir}/final_test_{timestamp}.html'
                fig.write_html(filename)

                print(f"✅ 인포그래픽 생성 완료: {filename}")
                return filename

        return None

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return None


# 테스트 1: 카테고리별 영화 수 (2컬럼)
print("=" * 60)
print("🧪 테스트 1: 카테고리별 영화 수")
sql1 = "SELECT c.name AS category_name, COUNT(fc.film_id) AS film_count FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY film_count DESC LIMIT 5;"
result1 = create_infographic_from_sql_query(sql1, "영화 카테고리별 개수 (상위 5개)")

# 테스트 2: 고객별 결제 금액 (3컬럼)
print("\n" + "=" * 60)
print("🧪 테스트 2: 고객별 총 결제 금액")
sql2 = "SELECT c.first_name, c.last_name, SUM(p.amount) AS total_payment FROM customer c JOIN payment p ON c.customer_id = p.customer_id GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY total_payment DESC LIMIT 5;"
result2 = create_infographic_from_sql_query(sql2, "고객별 총 결제 금액 (상위 5명)")

print("\n" + "=" * 60)
print("🎉 테스트 완료!")
if result1:
    print(f"✅ 테스트 1 성공: {result1}")
if result2:
    print(f"✅ 테스트 2 성공: {result2}")

print("💡 생성된 HTML 파일을 브라우저에서 확인해보세요!")
