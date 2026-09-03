"""
================================================================================
MaC (Memory & Color) Architecture — Vercel Serverless Pipeline Handler
================================================================================
[설계 목적]
1. 비즈니스 로직과 모델 공급자 간의 완전한 결합 분리(services/llm_engine.py 연동).
2. 4색 HEX 및 면적비(0.45, 0.30, 0.15, 0.10) 가중치를 CIELAB 공간에서 벡터 합성하여
   개인 고유 암호 해시 'MaC-L.C.H' 도출.
3. 원본 emailTemplate.html의 다크 씰 토글(<details>/<summary>) 및 슬림 2x2 카드 복원.
4. CORS 프리플라이트 및 Resend 트랜잭션 메일 발송 처리.
"""

from http.server import BaseHTTPRequestHandler
import json
import math
import os
from pathlib import Path
from dotenv import load_dotenv
import resend

# 환경 변수 로드
load_dotenv()

# Resend API Key 설정
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# 분리된 프롬프트 빌더 및 고가용성 AI 추론 엔진 임포트
try:
    from prompts.color_prompt import build_system_prompt
    from services.llm_engine import analyze_memory_with_llm
except ImportError:
    from color_prompt import build_system_prompt
    from llm_engine import analyze_memory_with_llm


# ------------------------------------------------------------------------------
# 1. 색채 물리학 연산 엔진 (sRGB -> CIE XYZ -> CIELAB -> 가중 LCH 해시)
# ------------------------------------------------------------------------------
def hex_to_rgb(hex_str: str):
    """HEX(#RRGGBB)를 0.0 ~ 1.0 선형 전 RGB 값으로 변환"""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return 0.5, 0.5, 0.5
    return (
        int(hex_str[0:2], 16) / 255.0,
        int(hex_str[2:4], 16) / 255.0,
        int(hex_str[4:6], 16) / 255.0,
    )

def srgb_to_xyz(r: float, g: float, b: float):
    """sRGB 감마(γ=2.4) 역보정 후 D65 백색광 기준 CIE XYZ 변환"""
    def linearize(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = linearize(r), linearize(g), linearize(b)
    X = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    Y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    Z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041
    return X, Y, Z

def xyz_to_lab(X: float, Y: float, Z: float):
    """CIE XYZ를 인간 지각 균등 공간인 CIELAB(L*, a*, b*)으로 변환"""
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    xr, yr, zr = X / Xn, Y / Yn, Z / Zn

    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    fx, fy, fz = f(xr), f(yr), f(zr)
    L = (116.0 * fy) - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return L, a, b

def compute_weighted_lch_hash(palette: list) -> str:
    """
    각 색상의 면적비(0.45, 0.30, 0.15, 0.10) 가중치를 적용해
    CIELAB 공간 내 가중 중심점을 구하고, 최종 고유 암호 해시(MaC-L.C.H)를 산출합니다.
    """
    total_weight = sum(item.get("weight", item.get("area_ratio", 0.25)) for item in palette)
    if total_weight <= 0:
        total_weight = 1.0

    weighted_L = 0.0
    weighted_a = 0.0
    weighted_b = 0.0

    for item in palette:
        w = item.get("weight", item.get("area_ratio", 0.25)) / total_weight
        r, g, b = hex_to_rgb(item.get("hex", "#888888"))
        X, Y, Z = srgb_to_xyz(r, g, b)
        L, a, b_val = xyz_to_lab(X, Y, Z)

        weighted_L += L * w
        weighted_a += a * w
        weighted_b += b_val * w

    chroma = math.sqrt(weighted_a ** 2 + weighted_b ** 2)
    hue_rad = math.atan2(weighted_b, weighted_a)
    hue_deg = math.degrees(hue_rad)
    if hue_deg < 0:
        hue_deg += 360.0

    l_int = int(round(weighted_L))
    c_int = int(round(chroma))
    h_int = int(round(hue_deg))

    return f"MaC-{l_int:02d}.{c_int:02d}.{h_int:03d}"


# ------------------------------------------------------------------------------
# 2. Vercel Serverless 요청 핸들러
# ------------------------------------------------------------------------------
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """웹 브라우저 비동기 fetch()를 위한 CORS 승인 응답"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            memory = data.get('memory', '').strip()
            email = data.get('email', '').strip()

            if not memory or not email:
                self._send_json(400, {"error": "기억 문장과 이메일 주소를 모두 입력해 주세요."})
                return

            # 1. 분리된 AI 추론 엔진 호출 (내부 자동 폴백: 3.1-pro -> 3.7 -> 3.6 -> 3.5)
            system_prompt = build_system_prompt()
            full_prompt = f"{system_prompt}\n\n[입력된 사용자 기억 사연]\n\"{memory}\""

            result_json = analyze_memory_with_llm(full_prompt)
            palette = result_json.get("palette", [])
            memory_summary = result_json.get("memory_summary", memory)

            # 2. 면적비 가중치 기반 최종 고유 암호 해시(MaC-L.C.H) 산출
            specimen_hash = compute_weighted_lch_hash(palette)
            result_json["specimen_hash"] = specimen_hash

            # 3. emailTemplate.html 읽기 및 데이터 정밀 바인딩
            template_path = Path(__file__).resolve().parent.parent / "emailTemplate.html"
            with open(template_path, "r", encoding="utf-8") as f:
                rendered_html = f.read()

            # 1) 해시 치환 (클릭 토글 영역의 {{ specimen_hash }} 매핑)
            rendered_html = rendered_html.replace("{{ specimen_hash }}", specimen_hash)
            rendered_html = rendered_html.replace("{{specimen_hash}}", specimen_hash)
            rendered_html = rendered_html.replace("{{SPECIMEN_HASH}}", specimen_hash)

            # 2) 요약문 치환
            rendered_html = rendered_html.replace("{{ memory_summary }}", memory_summary)
            rendered_html = rendered_html.replace("{{memory_summary}}", memory_summary)
            rendered_html = rendered_html.replace("{{MEMORY_SUMMARY}}", memory_summary)
            rendered_html = rendered_html.replace("{{USER_MEMORY}}", memory)

            # 3) 4색 칩 영역 바인딩 (palette[0] ~ palette[3] 인덱스 및 대문자 HEX 매핑)
            for i in range(4):
                chip = palette[i] if i < len(palette) else {}
                c_name = chip.get("color_name", f"Color {i+1}")
                c_hex = chip.get("hex", "#CCCCCC").upper()

                rendered_html = rendered_html.replace(f"{{{{ palette[{i}].color_name }}}}", c_name)
                rendered_html = rendered_html.replace(f"{{{{palette[{i}].color_name}}}}", c_name)
                rendered_html = rendered_html.replace(f"{{{{ palette[{i}].hex }}}}", c_hex)
                rendered_html = rendered_html.replace(f"{{{{palette[{i}].hex}}}}", c_hex)

            # 4. Resend 트랜잭션 메일 발송
            if RESEND_API_KEY:
                params = {
                    "from": "MaC <curator@mac.ai.kr>",
                    "to": [email],
                    "subject": f"MaC Chromatic Specimen [{specimen_hash}]",
                    "html": rendered_html
                }
                resend.Emails.send(params)

            # 5. 프론트엔드 응답 반환
            self._send_json(200, {
                "status": "success",
                "message": "발송 완료되었습니다.",
                "hash": specimen_hash,
                "data": result_json
            })

        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))