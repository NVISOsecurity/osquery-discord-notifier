import os
import json
from openai import AzureOpenAI


class LLMAssistant:
    def __init__(self, logger):
        self.logger = logger

        self.openai_api_base = os.getenv("OPENAI_API_BASE")
        self.openai_api_version = os.getenv("OPENAI_API_VERSION")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME")

        self.azure_openai_client = AzureOpenAI(
            api_key=self.openai_api_key,
            api_version=self.openai_api_version,
            azure_endpoint=self.openai_api_base,
        )

        self.json_response_example = {
            "event_summary": "a one sentence summary of the event",
            "event_details": "a detailed description of the event",
            "original_event": "the original event data",
        }

    def llm_question(self, question: str) -> str:
        prompt = f"Example of expected JSON output: {self.json_response_example} \n\n Question: {question}"

        response = self.azure_openai_client.chat.completions.create(
            model=self.openai_model_name,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return json.loads(response.choices[0].message.content)
        