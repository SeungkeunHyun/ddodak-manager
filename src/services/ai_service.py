import google.generativeai as genai
from src.config import Config

# =========================================================
# 2. Service Layer - AI
# Google Gemini API를 이용한 AI 기능을 제공합니다.
# =========================================================

class AIService:
    """
    Google Gemini API를 이용한 AI 기능을 제공하는 클래스입니다.
    """
    def __init__(self):
        self.model = self._setup_model()
        self.model_name = "None"

    def _setup_model(self):
        """
        API 키를 확인하고 사용 가능한 Gemini 모델을 설정합니다.
        """
        if not Config.GEMINI_API_KEY: return None
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            models = genai.list_models()
            # 텍스트 생성이 가능한 모델 필터링
            text_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            target = "models/gemini-1.5-flash"
            # 선호하는 모델 선택 (없으면 첫 번째 모델)
            self.model_name = target if target in text_models else text_models[0]
            return genai.GenerativeModel(self.model_name)
        except: return None

    # (참고) 이전 버전의 레거시 메서드 - 현재는 show_ai_briefing에서 직접 호출함
    def get_briefing(self, df):
        if not self.model: return "AI 서비스가 연결되지 않았습니다."
        prompt = f"산악회 회원 데이터 분석 후 MVP 칭찬과 격려 메시지를 작성해줘: {df.to_json()}"
        return self.model.generate_content(prompt).text
