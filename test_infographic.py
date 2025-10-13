"""
인포그래픽 생성 테스트 스크립트
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 테스트용 샘플 데이터 생성


def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    # 영화 카테고리별 매출 데이터 (예시)
    data = [
        ('Action', 15000000),
        ('Comedy', 12000000),
        ('Drama', 8000000),
        ('Horror', 6000000),
        ('Romance', 5000000)
    ]
    return data


def parse_sql_result_to_dataframe(query_result):
    """SQL 쿼리 결과를 DataFrame으로 변환"""
    try:
        print(f"🔍 쿼리 결과 타입: {type(query_result)}")
        print(f"🔍 쿼리 결과: {query_result}")

        if isinstance(query_result, list) and query_result:
            if isinstance(query_result[0], tuple):
                df = pd.DataFrame(query_result, columns=[
                                  'category', 'revenue'])
                print(f"✅ DataFrame 생성 성공: {df.shape}")
                print(f"📊 데이터 미리보기:\n{df}")
                return df

        return None

    except Exception as e:
        print(f"❌ DataFrame 변환 오류: {e}")
        return None


def create_html_infographic(df, question):
    """HTML 인포그래픽 생성"""
    try:
        # 디렉토리 생성
        infographic_dir = "infographics"
        if not os.path.exists(infographic_dir):
            os.makedirs(infographic_dir)
            print(f"📁 '{infographic_dir}' 폴더를 생성했습니다.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 데이터 타입 확인
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=['object']).columns.tolist()

        print(f"📊 숫자 컬럼: {numeric_cols}")
        print(f"📊 카테고리 컬럼: {categorical_cols}")

        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # 막대 차트 생성
            fig = px.bar(
                df,
                x=categorical_cols[0],
                y=numeric_cols[0],
                title=f'{question}',
                color=numeric_cols[0],
                color_continuous_scale='viridis'
            )

            fig.update_layout(
                title_font_size=16,
                height=600,
                margin=dict(t=100, b=100, l=50, r=50)
            )

            filename = f'{infographic_dir}/test_chart_{timestamp}.html'
            fig.write_html(filename)

            print(f"✅ HTML 인포그래픽 생성 완료!")
            print(f"📁 파일 위치: {filename}")
            return filename

        return None

    except Exception as e:
        print(f"❌ 인포그래픽 생성 오류: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return None


def main():
    """메인 테스트 함수"""
    print("🧪 인포그래픽 생성 테스트 시작")
    print("=" * 50)

    # 1. 샘플 데이터 생성
    sample_data = create_sample_data()
    print(f"📊 샘플 데이터: {sample_data}")

    # 2. DataFrame 변환 테스트
    df = parse_sql_result_to_dataframe(sample_data)

    if df is not None:
        # 3. 인포그래픽 생성 테스트
        question = "영화 카테고리별 매출 현황"
        result = create_html_infographic(df, question)

        if result:
            print(f"\n🎉 테스트 성공! 파일을 브라우저에서 열어보세요.")
            print(f"💡 Windows에서는 파일을 더블클릭하면 기본 브라우저에서 열립니다.")
        else:
            print("\n❌ 인포그래픽 생성 실패")
    else:
        print("\n❌ DataFrame 변환 실패")


if __name__ == "__main__":
    main()
