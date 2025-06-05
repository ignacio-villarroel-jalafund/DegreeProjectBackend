import requests
from requests.exceptions import RequestException, HTTPError, JSONDecodeError
from typing import Dict, Any
from app.core.config import settings

class AIAgentsService:
    def __init__(self):
        self.base_url = settings.N8N_BASE_URL
        self.session = requests.Session()

    def _call_n8n_webhook(self, webhook_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        full_url = f'{self.base_url}{webhook_path}'

        try:
            response = self.session.post(full_url, json=payload, timeout=30)

            response.raise_for_status()

            if response.text and response.text.strip():
                return response.json()
            else:
                print("n8n response was empty, returning specific error.")
                return {"error": "Empty response from n8n agent", "details": "The webhook returned 200 OK but with no JSON body."}

        except HTTPError as e:
            print(f"Error in n8n agent response: {e.response.status_code} - {e.response.text}")
            return {"error": f"Agent returned an error {e.response.status_code}", "details": e.response.text}
        
        except JSONDecodeError as e:
            print(f"Error decoding JSON from n8n: {e}")
            print(f"Response text that caused JSONDecodeError: '{response.text}'")
            return {"error": "Invalid JSON response from n8n agent.", "details": response.text if 'response' in locals() else "No response object available."}

        except RequestException as e:
            print(f"Network error contacting n8n agent: {e}")
            return {"error": "Connection error with the agent service.", "details": str(e)}
        
        except Exception as e:
            print(f"An unexpected error occurred when calling the agent: {e}")
            return {"error": "Unexpected error in the agent service.", "details": str(e)}

    def analyze_search_query(self, query: str) -> Dict[str, Any]:
        webhook_path = "/webhook/a58b586d-c75a-43a3-9e5b-9cd8962dfa33" 
        payload = {
            "query": query
        }
        return self._call_n8n_webhook(webhook_path, payload)

    def analyze_recipe_ingredients(self, search_query: str, recipe: list) -> Dict[str, Any]:
        webhook_path = "/webhook-test/043a365f-75da-4235-8515-debbab933e65"
        payload = {
            "search_query": search_query,
            "recipe": recipe
        }
        return self._call_n8n_webhook(webhook_path, payload)

    def adapt_recipe_interactively(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        webhook_path = "/webhook/ae6bacec-c322-408a-9c01-225d4215eb86"
        payload = request_body
        return self._call_n8n_webhook(webhook_path, payload)
    
    def extract_ingredient(self, body: str) -> Dict[str, Any]:
        webhook_path = "/webhook/40d91208-97ec-45c4-bfbe-528c65e2f7de"
        payload = body
        return self._call_n8n_webhook(webhook_path, payload)


ai_agents_service = AIAgentsService()