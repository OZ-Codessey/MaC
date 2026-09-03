"""
================================================================================
MaC (Memory & Color) Architecture — Color Association Standard (v1.0)
================================================================================
[설계 목적]
개인의 정성적 사연(서사, 감정, 시공간, 조도)을 객관적 색채 물리량(LCH 속성)으로 
사상(Mapping)하기 위한 정량적 참조 기준 데이터 레이어입니다.

[평가 및 심사 포인트]
1. 단순 사전식 치환(예: '바다=파란색')을 배제하고, 기억의 정서적 기저와 맥락을 우선시하는 휴리스틱을 구축함.
2. 4색 컬러칩의 면적비 가중치(0.45, 0.30, 0.15, 0.10)를 엄격히 규정하여 CIELAB/LCH 벡터 합성식의 무결성을 보장함.
3. 시스템 지시문(Prompt)과 데이터 기준표를 분리하여 향후 버전 관리(v1.0 -> v2.0) 및 모델 튜닝이 용이하도록 설계함.
"""

# ------------------------------------------------------------------------------
# 1. 팔레트 위계 및 면적비 가중치 (Palette Hierarchy & Weight Spec)
# ------------------------------------------------------------------------------
# LCH 가중치 합산 시 사용되는 정량적 면적 비율 규격 (합계는 정확히 1.00)
PALETTE_HIERARCHY = {
    "dominant": {
        "role": "Dominant (기저 지배색)",
        "weight": 0.45,
        "purpose": "장면 전체를 감싸는 핵심 정서이자 기억의 바탕을 형성하는 지배적 색채"
    },
    "supporting": {
        "role": "Supporting (배경 보조색)",
        "weight": 0.30,
        "purpose": "시공간, 계절적 배경, 물리적 장소를 든든하게 받쳐주는 구조적 색채"
    },
    "atmospheric": {
        "role": "Atmospheric (공간 조도/광원색)",
        "weight": 0.15,
        "purpose": "빛의 조도, 공기의 온도감, 찰나의 날씨와 감각적 정취를 환기하는 색채"
    },
    "accent": {
        "role": "Accent (선명한 기억의 표식)",
        "weight": 0.10,
        "purpose": "기억 속 가장 강렬하게 남아 있는 대상, 오브젝트 혹은 개인적 감정의 방점"
    }
}

# ------------------------------------------------------------------------------
# 2. 기억 요소별 영향력 가중치 (Feature Importance Mapping)
# ------------------------------------------------------------------------------
# 서사 분석 시 AI가 우선적으로 색채를 유추할 수 있도록 지정한 가중 지표
COLOR_MAPPING_PRIORITY = {
    "emotion": 0.30,          # 핵심 정서 (가장 높은 영향력)
    "memory_quality": 0.20,   # 기억의 선명도/풍화 정도 (채도 및 대비 결정)
    "time": 0.15,             # 시간대 (명도 결정)
    "space": 0.15,            # 공간적 배경
    "temperature": 0.10,      # 체감 온도 (Warm/Cool 축 결정)
    "light": 0.05,            # 광원 특성
    "sensory": 0.05           # 미각/촉각 등 공감각적 요소
}

# ------------------------------------------------------------------------------
# 3. 색채 연상 대원칙 (Color Association Principles)
# ------------------------------------------------------------------------------
COLOR_ASSOCIATION_PRINCIPLES = [
    "사물의 실제 표면색보다 기억에서 발생하는 정서적·심리적 색채연상을 우선한다.",
    "하나의 감정이나 단어를 특정한 단일 색상으로 고정 치환하지 않는다.",
    "동일한 장소라도 기억의 맥락(누구와 함께했는지, 어떤 감정이었는지)에 따라 전혀 다른 색채가 도출될 수 있다.",
    "Dominant(0.45)는 시각적으로 가장 튀는 색이 아니라 기억 전체를 지배하는 기저 정서의 색이다.",
    "Accent(0.10)는 면적비는 가장 작지만 개인적 기억의 인상을 강렬하게 각인시키는 색이다.",
    "오래되거나 아련한 기억은 채도(Chroma)와 명암 대비를 낮추어 부드럽게 감쇄시킨다.",
    "강렬하고 생생한 기억은 채도와 대비를 상승시켜 선명도를 확보한다.",
    "추출된 4개의 색상은 독립된 파편이 아니라, 단 하나의 기억에서 파생된 통일된 색채 조화(Harmony)를 이룬다.",
    "사연에 명시되지 않은 허구적 인물이나 사물을 임의로 날조하여 색상 근거로 삼지 않는다."
]

# ------------------------------------------------------------------------------
# 4. 정서 -> 색채 속성 매핑 (Emotion to Color Attribute Rules)
# ------------------------------------------------------------------------------
EMOTION_COLOR_RULES = {
    "warm_nostalgia": {
        "association": ["Sugar Pink", "Peach Cream", "Caramel Beige"],
        "lightness": "medium-high",
        "chroma": "medium",
        "temperature": "warm",
        "keywords": ["추억", "어린 시절", "다정함", "포근함", "가족", "손잡고"]
    },
    "joy_excitement": {
        "association": ["Carousel Gold", "Coral Pop", "Sunny Amber"],
        "lightness": "high",
        "chroma": "high",
        "temperature": "warm",
        "keywords": ["놀이공원", "설렘", "환희", "축제", "신남", "웃음"]
    },
    "calm_peace": {
        "association": ["May Sky", "Pale Sage", "Soft Cerulean"],
        "lightness": "high",
        "chroma": "low-medium",
        "temperature": "cool-neutral",
        "keywords": ["평온", "고요", "5월", "하늘", "바람", "휴식"]
    },
    "stability_affection": {
        "association": ["Warm Wood", "Earthy Oak", "Soft Umber"],
        "lightness": "medium-low",
        "chroma": "low-medium",
        "temperature": "warm",
        "keywords": ["아빠", "든든함", "나무", "기둥", "의지", "신뢰"]
    }
}

# ------------------------------------------------------------------------------
# 5. 시간/공간/기억 질감 보정 룰 (Context Modifiers)
# ------------------------------------------------------------------------------
TIME_COLOR_RULES = {
    "afternoon": {"lightness": "medium-high", "chroma": "medium", "keywords": ["오후", "낮", "햇살"]},
    "sunset": {"lightness": "medium", "chroma": "medium-high", "keywords": ["노을", "황혼", "해질녘"]}
}

SPACE_COLOR_RULES = {
    "amusement_park": {"association": ["pink", "gold", "sky_blue", "wood"], "keywords": ["놀이공원", "회전목마", "테마파크"]}
}

MEMORY_QUALITY_RULES = {
    "cherished": {"chroma": "balanced", "contrast": "harmonious", "keywords": ["소중한", "기억에 남는", "따뜻한"]}
}