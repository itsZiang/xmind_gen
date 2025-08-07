from g4f.client import Client
from langchain_core.messages import AIMessageChunk

class ChatG4F:
    def __init__(self, model="gpt-4", **kwargs):
        self.client = Client()
        self.model = model

    def invoke(self, prompt: str, config: dict = None):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message

    def stream(self, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield AIMessageChunk(content=delta.content)

