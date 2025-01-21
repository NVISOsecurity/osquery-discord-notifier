import os
import json
from os import path
from openai import OpenAI

class LLMAssistant:
  def __init__(self, logger):
    self.logger = logger        

    self.openai_api_key = os.getenv("OPENAI_API_KEY")
    self.openai_model_name = os.getenv("OPENAI_MODEL_NAME")

    self.openai_client = OpenAI(
        api_key=self.openai_api_key,
    )

    self.json_response_example = {
      "event_summary": "Summary of the event (10 words or less), always start with an appropriate and relevant emoji symbolizing the event.",
      "event_details": """Description of the event. 
                          Explicitly mention if the event looks potentially malicious or not, and briefly explain why. 
                          Format this entire field as a Markdown unordered list with at most 3 items, so focus on the most important information.
                          Do not literally mention all the fields in the event data, but rather summarize the key points.
                          Avoid using semicolons in your unordered list but generate short and easy to understand sentences.
                        """,
      "original_event": "the original event data",
    }

  def llm_test(self) -> str:
    prompt = "Respond to the user with a friendly short sentence mentioning that the LLM test was successful. Add a small random fact to show you are able to respond. max 10 words."

    try:
      response = self.openai_client.chat.completions.create(
          model=self.openai_model_name,
          messages=[
              {
                  "role": "system",
                  "content": "You are a helpful assistant",
              },
              {
                  "role": "user",
                  "content": prompt,
              },
          ],
      )

      return response.choices[0].message.content
    except Exception as e:
      self.logger.error("LLM test failed: %s", e)
      return "LLM test failed."

  def llm_question(self, question: str) -> str:
    prompt = f"Example of expected JSON output: {self.json_response_example} \n\n Question: {question}"

    response = self.openai_client.chat.completions.create(
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