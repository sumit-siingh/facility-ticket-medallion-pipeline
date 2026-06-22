import requests
import json


class LocalLLMAgent:
    """
    Lightweight LLM agent using Ollama.
    Used ONLY for:
    - insights
    - cleaning suggestions
    - gold layer suggestions
    """

    def __init__(self, model="llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def ask(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]

    # --------------------------------------------------------
    # Agent: Data Quality Insights
    # --------------------------------------------------------
    def data_quality_insight(self, profile: dict) -> str:
        prompt = f"""
You are a data engineer.

Given this dataset profile:
{json.dumps(profile, indent=2)}

Provide:
1. Data quality issues
2. Cleaning suggestions
3. Validation rules

Keep it concise.
"""
        return self.ask(prompt)

    # --------------------------------------------------------
    # Agent: Gold Layer Suggestions
    # --------------------------------------------------------
    def gold_layer_suggestion(self, schema: dict) -> str:
        prompt = f"""
You are a data architect.

Given:
1. Silver schema
2. Column statistics

Propose:
- 3 business gold tables
- Purpose
- Key metrics
- Business value

Return JSON only.
"""
        return self.ask(prompt)