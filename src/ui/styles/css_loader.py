"""
CSS 파일들을 로드하고 Streamlit에 적용하는 유틸리티
"""
import os
import streamlit as st
from pathlib import Path


def load_css_file(css_file_path: str) -> str:
    """CSS 파일을 읽어서 문자열로 반환"""
    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"CSS 파일을 찾을 수 없습니다: {css_file_path}")
        return ""
    except Exception as e:
        st.error(f"CSS 파일 로드 중 오류 발생: {e}")
        return ""


def apply_css_files(*css_files: str):
    """여러 CSS 파일들을 Streamlit에 적용"""
    css_content = ""
    
    for css_file in css_files:
        # 상대 경로를 절대 경로로 변환
        current_dir = Path(__file__).parent
        css_path = current_dir / "css" / css_file
        
        if css_path.exists():
            css_content += load_css_file(str(css_path))
        else:
            st.warning(f"CSS 파일을 찾을 수 없습니다: {css_path}")
    
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def load_all_styles():
    """모든 스타일 파일을 로드"""
    apply_css_files("main.css", "cards.css")

