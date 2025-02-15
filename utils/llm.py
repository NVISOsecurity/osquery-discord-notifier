import os
import json
from os import path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMAssistant:
  def __init__(self, logger):
    self.logger = logger        

    self.openai_api_key = os.getenv("OPENAI_API_KEY")
    self.openai_model_name = os.getenv("OPENAI_MODEL_NAME")
    self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

    self.openai_client = OpenAI(
        api_key=self.openai_api_key,
        base_url=self.openai_base_url
    )

    self.json_response_example = {
      "event_summary": "Summary of the event (10 words or less), always start with an appropriate and relevant emoji symbolizing the event.",
      "event_details": """Description of the event as a single string, no lists or dictionaries.
                          Explicitly mention if the event looks potentially malicious or not, and briefly explain why. 
                          Format this entire field as a Markdown unordered list with at most 5 items, so focus on the most important information.
                          Include the details required for the user to understand at a high level if the event looks normal, such as service names and file paths.
                          Do not literally mention all the fields in the event data, but rather summarize the key points.
                          Avoid using semicolons in your unordered list but generate short and easy to understand sentences.
                        """
    }

  def llm_test(self) -> str:
    prompt = "Respond to the user with the literal text 'LLM test succeeded'."

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

  def llm_question(self, question: str) -> dict:  # Specify return type as dict
          prompt = (
              f"Output a JSON object with the following keys & instructions: {self.json_response_example}"
              f"\n\nThis is the event you should analyze:\n\n\n\n{question}"
          )
          attempts = 0
          max_attempts = 10

          while attempts < max_attempts:
              try:
                  response = self.openai_client.chat.completions.create(
                      model=self.openai_model_name,
                      timeout=120,
                      messages=[
                          {
                              "role": "system",
                              "content":  f"Respond only with valid JSON. "
                                          f"Do not write an introduction or summary. "
                                          f"Your response should be a valid JSON object we can parse with json.loads in Python."
                          },
                          {
                              "role": "user",
                              "content": prompt,
                          },
                      ],
                  )

                  content = response.choices[0].message.content

                  # Verify that the response is a valid JSON & that each value is a string
                  try:
                    data = json.loads(content)
                    for key, value in data.items():
                        if not isinstance(value, str):
                            raise ValueError(f"Value for key '{key}' is not a string: {type(value)}")
                    return data # Return the parsed JSON object

                  except json.JSONDecodeError as e:
                      attempts += 1
                      self.logger.warning(f"Invalid JSON response, attempt {attempts}/{max_attempts}")
                  except ValueError as e:
                      attempts += 1
                      self.logger.warning(f"Invalid JSON structure, attempt {attempts}/{max_attempts}")
                      
              except Exception as e:
                  self.logger.error("LLM question failed: %s", e)
                  break

          return {"error": "Failed to get a valid JSON response after multiple attempts."}  # Return a dict with an error message