"""
인포그래픽 생성 문제 디버깅 스크립트
"""
import sys
import os


def check_dependencies():
    """필요한 라이브러리들이 설치되어 있는지 확인"""
    print("🔍 === 라이브러리 의존성 확인 ===")

    required_packages = [
        'pandas',
        'plotly',
        'numpy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 설치됨")
        except ImportError:
            print(f"❌ {package}: 설치되지 않음")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ 누락된 패키지: {missing_packages}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def test_plotly():
    """Plotly 기본 기능 테스트"""
    print("\n🔍 === Plotly 기능 테스트 ===")

    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import pandas as pd

        # 간단한 데이터 생성
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })

        # 차트 생성 테스트
        fig = px.bar(df, x='category', y='value', title='테스트 차트')

        # HTML 생성 테스트
        html_str = fig.to_html()

        if len(html_str) > 100:
            print("✅ Plotly 차트 생성 성공")
            return True
        else:
            print("❌ Plotly 차트 생성 실패")
            return False

    except Exception as e:
        print(f"❌ Plotly 테스트 실패: {e}")
        return False


def test_file_creation():
    """파일 생성 권한 테스트"""
    print("\n🔍 === 파일 생성 권한 테스트 ===")

    try:
        # 테스트 디렉토리 생성
        test_dir = "test_infographics"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            print(f"✅ 디렉토리 생성 성공: {test_dir}")

        # 테스트 파일 생성
        test_file = os.path.join(test_dir, "test.html")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("<html><body><h1>테스트</h1></body></html>")

        print(f"✅ 파일 생성 성공: {test_file}")

        # 파일 삭제
        os.remove(test_file)
        os.rmdir(test_dir)
        print("✅ 파일 정리 완료")

        return True

    except Exception as e:
        print(f"❌ 파일 생성 테스트 실패: {e}")
        return False


def test_data_parsing():
    """데이터 파싱 테스트"""
    print("\n🔍 === 데이터 파싱 테스트 ===")

    try:
        import pandas as pd

        # 다양한 형태의 테스트 데이터
        test_cases = [
            # 케이스 1: 튜플 리스트
            [('Action', 15000000), ('Comedy', 12000000)],

            # 케이스 2: 문자열 (일반적인 SQL 결과)
            "('Action', 15000000)\n('Comedy', 12000000)",

            # 케이스 3: 단일 값
            42
        ]

        for i, test_data in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}: {type(test_data)}")

            if isinstance(test_data, list) and test_data and isinstance(test_data[0], tuple):
                df = pd.DataFrame(test_data, columns=['category', 'value'])
                print(f"✅ 케이스 {i} 성공: {df.shape}")
            elif isinstance(test_data, str):
                # 문자열 파싱 시도
                lines = test_data.strip().split('\n')
                data = []
                for line in lines:
                    if line.startswith('(') and line.endswith(')'):
                        try:
                            import ast
                            row = ast.literal_eval(line)
                            data.append(row)
                        except:
                            pass

                if data:
                    df = pd.DataFrame(data, columns=['category', 'value'])
                    print(f"✅ 케이스 {i} 성공: {df.shape}")
                else:
                    print(f"❌ 케이스 {i} 실패: 파싱 불가")
            else:
                df = pd.DataFrame({'result': [test_data]})
                print(f"✅ 케이스 {i} 성공: {df.shape}")

        return True

    except Exception as e:
        print(f"❌ 데이터 파싱 테스트 실패: {e}")
        return False


def create_simple_infographic():
    """간단한 인포그래픽 생성 테스트"""
    print("\n🔍 === 인포그래픽 생성 테스트 ===")

    try:
        import pandas as pd
        import plotly.express as px
        from datetime import datetime

        # 테스트 데이터
        df = pd.DataFrame({
            'category': ['액션', '코미디', '드라마', '호러'],
            'count': [25, 18, 12, 8]
        })

        # 차트 생성
        fig = px.bar(
            df,
            x='category',
            y='count',
            title='영화 장르별 개수',
            color='count',
            color_continuous_scale='viridis'
        )

        fig.update_layout(
            title_font_size=16,
            height=500,
            margin=dict(t=100, b=50, l=50, r=50)
        )

        # 디렉토리 생성
        infographic_dir = "infographics"
        if not os.path.exists(infographic_dir):
            os.makedirs(infographic_dir)

        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'{infographic_dir}/debug_test_{timestamp}.html'
        fig.write_html(filename)

        print(f"✅ 인포그래픽 생성 성공: {filename}")

        # 파일 크기 확인
        file_size = os.path.getsize(filename)
        print(f"📁 파일 크기: {file_size:,} bytes")

        if file_size > 1000:  # 1KB 이상이면 정상
            print("✅ 파일이 정상적으로 생성되었습니다!")
            return True
        else:
            print("⚠️ 파일이 너무 작습니다. 내용이 제대로 생성되지 않았을 수 있습니다.")
            return False

    except Exception as e:
        print(f"❌ 인포그래픽 생성 실패: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return False


def main():
    """메인 디버깅 함수"""
    print("🔧 === 인포그래픽 생성 문제 진단 시작 ===")
    print("=" * 60)

    results = []

    # 1. 의존성 확인
    results.append(("라이브러리 의존성", check_dependencies()))

    # 2. Plotly 테스트
    results.append(("Plotly 기능", test_plotly()))

    # 3. 파일 생성 권한
    results.append(("파일 생성 권한", test_file_creation()))

    # 4. 데이터 파싱
    results.append(("데이터 파싱", test_data_parsing()))

    # 5. 인포그래픽 생성
    results.append(("인포그래픽 생성", create_simple_infographic()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("🔍 === 진단 결과 요약 ===")

    all_passed = True
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트가 통과했습니다!")
        print("💡 인포그래픽 생성이 정상적으로 작동해야 합니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        print("💡 실패한 항목을 확인하고 해결해주세요.")


if __name__ == "__main__":
    main()
