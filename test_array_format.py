#!/usr/bin/env python3
"""
ensure_array_format 함수 테스트
"""

import json

def ensure_array_format(data) -> list:
    """데이터를 올바른 배열 형식으로 변환 (JSONB 호환)"""
    if data is None:
        return []
    
    if isinstance(data, list):
        # 이미 배열인 경우, 각 요소를 그대로 유지 (이스케이프 방지)
        return [item for item in data if item is not None and str(item).strip()]
    
    if isinstance(data, str):
        # 문자열인 경우, JSON 파싱 시도 후 실패하면 단일 요소 배열로 변환
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                # 파싱된 배열의 각 요소를 그대로 유지
                return [item for item in parsed if item is not None and str(item).strip()]
            else:
                # 단일 값인 경우 그대로 반환
                return [parsed] if str(parsed).strip() else []
        except (json.JSONDecodeError, TypeError):
            # JSON 파싱 실패 시 원본 문자열을 그대로 반환
            return [data] if data.strip() else []
    
    # 기타 타입인 경우 그대로 단일 요소 배열로 반환
    return [data] if str(data).strip() else []

# 테스트 케이스들
test_cases = [
    # None 값
    (None, []),
    
    # 빈 배열
    ([], []),
    
    # 올바른 배열
    (["장비 및 식사 준비 목록", "활동 계획 및 전체 일정표"], ["장비 및 식사 준비 목록", "활동 계획 및 전체 일정표"]),
    
    # JSON 문자열 배열
    ('["장비 및 식사 준비 목록", "활동 계획 및 전체 일정표"]', ["장비 및 식사 준비 목록", "활동 계획 및 전체 일정표"]),
    
    # 단일 문자열
    ("장비 및 식사 준비 목록", ["장비 및 식사 준비 목록"]),
    
    # 빈 문자열
    ("", []),
    
    # 공백만 있는 문자열
    ("   ", []),
    
    # 숫자 배열 (원본 유지)
    ([1, 2, 3], [1, 2, 3]),
    
    # 혼합 타입 배열 (원본 유지)
    (["문자열", 123, None, ""], ["문자열", 123]),
    
    # JSON 문자열 (단일 값)
    ('"단일 값"', ["단일 값"]),
    
    # JSON 객체 (파싱된 객체 유지)
    ('{"key": "value"}', [{"key": "value"}]),
]

print("ensure_array_format 함수 테스트 결과:")
print("=" * 50)

all_passed = True
for i, (input_data, expected) in enumerate(test_cases, 1):
    result = ensure_array_format(input_data)
    passed = result == expected
    all_passed = all_passed and passed
    
    print(f"테스트 {i}: {'✅ 통과' if passed else '❌ 실패'}")
    print(f"  입력: {repr(input_data)}")
    print(f"  예상: {expected}")
    print(f"  결과: {result}")
    print()

print("=" * 50)
print(f"전체 테스트 결과: {'✅ 모든 테스트 통과' if all_passed else '❌ 일부 테스트 실패'}")
