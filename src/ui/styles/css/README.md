# CSS 스타일 파일들

이 폴더에는 애플리케이션의 모든 CSS 스타일이 포함되어 있습니다.

## 파일 구조

- `main.css` - 메인 애플리케이션 스타일 (폰트, 헤더, 탭 등)
- `cards.css` - 카드 및 배지 컴포넌트 스타일

## 사용법

CSS 파일들은 `src/ui/styles/css_loader.py`의 `load_all_styles()` 함수를 통해 자동으로 로드됩니다.

### 새로운 CSS 파일 추가하기

1. 이 폴더에 새로운 `.css` 파일을 생성
2. `css_loader.py`의 `load_all_styles()` 함수에 파일명 추가

```python
def load_all_styles():
    """모든 스타일 파일을 로드"""
    apply_css_files("main.css", "cards.css", "새파일.css")
```

## 마이그레이션

기존의 인라인 CSS 스타일들이 이 폴더로 이동되었습니다:
- `app.py`의 메인 스타일 → `main.css`
- `card_styles.py`의 카드 스타일 → `cards.css`

