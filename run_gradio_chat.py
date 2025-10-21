#!/usr/bin/env python3
"""
SQL Agent Gradio 챗봇 실행 스크립트
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    from sql_agent_gradio_chat import main
    main()
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("💡 다음 명령으로 의존성을 설치해주세요:")
    print("   pip install -r requirements.txt")
except Exception as e:
    print(f"❌ 실행 실패: {e}")
