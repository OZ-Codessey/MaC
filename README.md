# 🎨 MaC (Memory and Color | My and Color)

> **"당신의 추억을 한 줄로 적어주세요. 당신의 기억을, 색으로 돌려드립니다."** > 사용자의 추억 문장과 생년월일을 바탕으로 감정 및 사주 오행을 분석하여, 나만의 시그니처 퍼스널 HEX 컬러 팔레트(70:25:5 비율)와 감성 리포트를 제공하는 AI 웹 서비스입니다.

---

## 🚀 1. 서비스 소개 및 기획
- **서비스명**: MaC (`Memory & Color` / `My Color`)
- **타겟 사용자**:
- **핵심 기능**:
  1. **Memory & Color 모드**:
  2. **My & Color 모드**: 
  3. **Color Archive & Contact**:

---

## 🛠️ 2. 기술 스택 (Tech Stack)
- **Frontend**: 순수 HTML5, CSS3 (Glassmorphism UI), Vanilla JavaScript (SPA 형태 네비게이션 및 비동기 Fetch 통신)
- **Backend**: Vercel Serverless Functions (Python)
- **AI Model**:
- **Deployment**: Vercel

---

## 📂 3. 프로젝트 구조 (Directory Structure)
```text
MaC/
├── api/
│   └── recommend.py     # Vercel 파이썬 서버less 백엔드 (AI API 연동)
├── css/
│   └── style.css        # 글래스모피즘 디자인 및 반응형 스타일
├── js/
│   └── main.js          # 프론트엔드 UX 분기 및 API fetch 통신
├── index.html           # 메인 웹페이지 (4대 섹션 및 네비게이션)
├── requirements.txt     # 파이썬 라이브러리 목록 (requests, openai 등)
├── .gitignore           # 보안 설정 (API 키 및 캐시 제외)
└── README.md            # 프로젝트 설명서