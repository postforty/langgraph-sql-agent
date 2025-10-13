"""
Decimal 파싱 테스트
"""
import os
import ast
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

# 테스트 데이터 (실제 SQL 결과와 동일한 형태)
test_result = "[('KARL', 'SEAL', Decimal('221.55')), ('ELEANOR', 'HUNT', Decimal('216.54')), ('CLARA', 'SHAW', Decimal('195.58'))]"

print(f"🔍 원본 데이터: {test_result}")

# Decimal 처리


def decimal_replacer(match):
    return match.group(1)


# Decimal 객체를 숫자 문자열로 변환
cleaned_result = re.sub(r"Decimal\('([^']+)'\)", decimal_replacer, test_result)
print(f"🔧 Decimal 처리 후: {cleaned_result}")

# 파싱
parsed_result = ast.literal_eval(cleaned_result)
print(f"✅ 파싱 결과: {parsed_result}")

# DataFrame 생성
df = pd.DataFrame(parsed_result, columns=['col1', 'col2', 'col3'])
print(f"📊 DataFrame:\n{df}")

# 숫자 컬럼 변환
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col], errors='ignore')
    except:
        pass

print(f"📊 타입 변환 후:\n{df.dtypes}")

# 이름 합치기
df['full_name'] = df['col1'] + ' ' + df['col2']
print(f"📊 이름 합친 후:\n{df}")

# 차트 생성
fig = px.bar(
    df,
    x='full_name',
    y='col3',
    title='고객별 총 결제 금액',
    color='col3',
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
filename = f'{infographic_dir}/decimal_test_{timestamp}.html'
fig.write_html(filename)

print(f"✅ 테스트 차트 생성 완료: {filename}")
