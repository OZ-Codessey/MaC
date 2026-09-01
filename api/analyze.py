from http.server import BaseHTTPRequestHandler
import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Gemini 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            memory = data.get('memory', '').strip()
            email = data.get('email', '').strip()

            if not memory or not email:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "추억 문장과 이메일 주소를 모두 입력해 주세요."}).encode('utf-8'))
                return

            # Gemini 프롬프트 구성 (JSON 형식으로 색상 추출)
            prompt = f"""
            Analyze the following memory text and convert its emotion/mood into a Color Field art palette.
            Memory: "{memory}"

            Return ONLY a raw JSON object with this exact structure:
            {{
                "palette_title": "A poetic English title (e.g. Autumn Solitude)",
                "gradient": "linear-gradient(135deg, #HEX1 0%, #HEX2 50%, #HEX3 100%)"
            }}
            """

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )

            result_json = json.loads(response.text)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result_json).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))