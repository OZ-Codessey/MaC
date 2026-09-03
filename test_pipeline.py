"""
================================================================================
MaC (Memory & Color) Pipeline — Local Integration Test Script
================================================================================
[핵심 동작]
1. 분리된 services/llm_engine.py를 통해 4색 팔레트 및 정제된 한 줄 요약문 도출.
2. 면적비 가중치 기반 CIELAB 벡터 합성을 거쳐 고유 암호 해시(MaC-L.C.H) 산출.
3. 정규표현식(re.sub)으로 emailTemplate.html 내 이중 중괄호({{ ... }})와 줄바꿈을 
   통째로 제거하고 실제 색상 HEX 및 다크 씰 토글 인터랙션 복원.
4. preview_pipeline.html 파일 생성 및 Resend 트랜잭션 메일 발송 검증.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
import resend

# 1. 환경 변수 로드
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# 분리된 모듈 임포트
from services.llm_engine import analyze_memory_with_llm
from api.analyze import compute_weighted_lch_hash
from prompts.color_prompt import build_system_prompt

# ------------------------------------------------------------------------------
# 테스트용 입력 데이터
# ------------------------------------------------------------------------------
test_memory = "5월 화창한 날 아빠 손을 잡고 갔던 놀이공원의 달콤한 솜사탕과 반짝이던 회전목마"
test_email = "test@example.com"  # 실제 메일 수신 테스트 시 본인 이메일 주소 입력


# ------------------------------------------------------------------------------
# [1/4] 단계: 분리된 AI 엔진 계층 호출 (추론 및 4색 추출)
# ------------------------------------------------------------------------------
print("🚀 [1/4] AI 엔진 분석 호출 중 (services/llm_engine.py 연동)...")
system_prompt = build_system_prompt()
full_prompt = f"{system_prompt}\n\n[입력된 사용자 기억 사연]\n\"{test_memory}\""

result_json = analyze_memory_with_llm(full_prompt)
palette = result_json.get("palette", [])
memory_summary = result_json.get("memory_summary", test_memory)

print(f"✅ AI 한 줄 요약: {memory_summary}")
print("🎨 추출된 4색 팔레트 규격:")
for idx, chip in enumerate(palette, start=1):
    c_name = chip.get("color_name", "Unknown")
    c_hex = chip.get("hex", "#FFFFFF").upper()
    c_weight = chip.get("weight", chip.get("area_ratio", 0.25))
    print(f"   [{idx}] {c_name:<16} | HEX: {c_hex} (비중: {c_weight})")


# ------------------------------------------------------------------------------
# [2/4] 단계: 색채 물리학 기반 면적비 가중 LCH 암호 해시 산출
# ------------------------------------------------------------------------------
print("\n⚙️ [2/4] 면적비(0.45, 0.30, 0.15, 0.10) 가중치 기반 MaC-L.C.H 해시 계산 중...")
specimen_hash = compute_weighted_lch_hash(palette)
print(f"🔑 최종 산출된 고유 표본 해시: {specimen_hash}")


# ------------------------------------------------------------------------------
# [3/4] 단계: emailTemplate.html 정밀 바인딩 (이중 중괄호 완전 제거 & 배경색 주입)
# ------------------------------------------------------------------------------
print("\n📄 [3/4] emailTemplate.html 바인딩 및 preview_pipeline.html 생성 중...")

template_path = Path(__file__).resolve().parent / "emailTemplate.html"
with open(template_path, "r", encoding="utf-8") as f:
    rendered_html = f.read()

# 이중 중괄호 {{ 와 }} 및 내부 줄바꿈·공백을 정확히 한 번에 매칭하여 치환하는 함수
def replace_double_curly(tag_pattern: str, value: str, text: str) -> str:
    pattern = rf"\{{\{{\s*{tag_pattern}\s*\}}\}}"
    return re.sub(pattern, value, text, flags=re.DOTALL | re.IGNORECASE)

# 1) 해시 치환 (클릭 시 토글되는 다크 씰 내부 {{ specimen_hash }})
rendered_html = replace_double_curly(r"specimen_hash", specimen_hash, rendered_html)

# 2) 요약문 치환 ({{ memory_summary }})
rendered_html = replace_double_curly(r"memory_summary", memory_summary, rendered_html)

# 3) 4색 칩 영역 치환 (각 칩의 상단 배경색 HEX, 컬러명, 하단 HEX 텍스트)
for i in range(4):
    chip = palette[i] if i < len(palette) else {}
    c_name = chip.get("color_name", f"Color {i+1}")
    c_hex = chip.get("hex", "#CCCCCC").upper()

    rendered_html = replace_double_curly(rf"palette\[{i}\]\.color_name", c_name, rendered_html)
    rendered_html = replace_double_curly(rf"palette\[{i}\]\.hex", c_hex, rendered_html)

# 4) 치환 누락 여부 검증
remaining_tags = re.findall(r"\{\{.*?\}\}", rendered_html, re.DOTALL)
if remaining_tags:
    print(f"⚠️ 미치환 태그 발견: {remaining_tags}")
else:
    print("✨ 모든 {{ ... }} 태그가 깨끗하게 실제 데이터로 치환되었습니다.")

# 5) 시각 검증용 미리보기 파일 저장
preview_path = Path(__file__).resolve().parent / "preview_pipeline.html"
with open(preview_path, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print(f"✅ 렌더링 파일 생성 완료: {preview_path.resolve()}")


# ------------------------------------------------------------------------------
# [4/4] 단계: Resend 트랜잭션 메일 발송 테스트
# ------------------------------------------------------------------------------
print("\n✉️ [4/4] Resend 메일 발송 테스트...")
if RESEND_API_KEY:
    try:
        send_res = resend.Emails.send({
            "from": "MaC <curator@mac.ai.kr>",
            "to": "rainbowjjinn@gmail.com",
            "subject": f"MaC Chromatic Specimen [{specimen_hash}]",
            "html": rendered_html
        })
        print(f"🎉 메일 발송 성공! Resend Message ID: {send_res}")
    except Exception as e:
        print(f"⚠️ 메일 발송 API 응답: {e}")
else:
    print("ℹ️ RESEND_API_KEY가 없어 실제 발송은 생략되었습니다.")

print("\n" + "=" * 60)
print("🎯 [검증 완료] 브라우저에서 새로고침하거나 아래 명령어로 확인하세요:")
print("   open preview_pipeline.html")
print("=" * 60)