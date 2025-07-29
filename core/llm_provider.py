from openai import OpenAI
import g4f

class LLMProvider:
    """Lớp quản lý LLM"""
    def __init__(self):
        self.client = None
        self.provider = None

    def initialize_client(self, base_url: str, provider: str, api_key: str = None):
        """Khởi tạo client cho provider được chọn"""
        self.provider = provider
        try:
            if provider == "openai":
                if not api_key:
                    raise ValueError("API Key is required for OpenAI")
                self.client = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                    default_headers={"App-Code": "fresher"}
                )
            elif provider == "g4f":
                self.client = g4f
        except Exception as e:
            raise Exception(f"Lỗi khởi tạo {provider}: {str(e)}")

    def get_available_models(self) -> list:
        """Lấy danh sách model có sẵn cho provider"""
        if self.provider == "openai":
            return ["gpt-4.1", "gpt-4.1-mini", "misa-qwen3-30b", "misa-qwen3-235b", "misa-internvl3-38b", "omni-moderation-latest"]
        elif self.provider == "g4f":
            try:
                return [model.replace('_', '-') for model in dir(g4f.models) if not model.startswith('_')]
            except Exception as e:
                raise Exception(f"Lỗi khi lấy danh sách model g4f: {str(e)}")
        return []

    def call_llm(self, prompt: str, model: str = "gpt-4.1-mini") -> str:
        """Gọi LLM"""
        if not self.client:
            return "Client LLM chưa được khởi tạo."
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=15000,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            elif self.provider == "g4f":
                response = self.client.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=15000,
                    temperature=0.3
                )
                if isinstance(response, str):
                    return response.strip()
                elif hasattr(response, 'choices') and response.choices:
                    return response.choices[0].message.content.strip()
                else:
                    raise Exception(f"Phản hồi g4f không đúng định dạng: {response}")
        except Exception as e:
            return f"Lỗi {self.provider}: {str(e)}"
