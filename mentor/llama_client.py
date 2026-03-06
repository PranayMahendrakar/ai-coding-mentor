"""Llama Client - Handles communication with local Llama model via Ollama"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"


class LlamaClient:
      def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL, timeout: int = 120):
                self.base_url = base_url
                self.model = model
                self.timeout = timeout
                self.client = httpx.AsyncClient(timeout=timeout)

      async def generate(self, prompt: str, system: Optional[str] = None) -> str:
                """Generate a response from Llama model."""
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 2048}
                }
                if system:
                              payload["system"] = system
                          try:
                                        response = await self.client.post(f"{self.base_url}/api/generate", json=payload)
                                        response.raise_for_status()
                                        return response.json().get("response", "")
except httpx.ConnectError:
            logger.warning("Ollama not running, using mock response")
            return self._mock_response(prompt)
except Exception as e:
            logger.error(f"Llama generate error: {e}")
            return self._mock_response(prompt)

    async def check_connection(self) -> bool:
              """Check if Ollama is running and model is available."""
              try:
                            response = await self.client.get(f"{self.base_url}/api/tags")
                            if response.status_code == 200:
                                              models = [m["name"] for m in response.json().get("models", [])]
                                              return any(self.model in m for m in models)
                                          return False
except Exception:
            return False

    def _mock_response(self, prompt: str) -> str:
              """Fallback mock response when Ollama is not available."""
              prompt_lower = prompt.lower()
              if "explain" in prompt_lower or "eli5" in prompt_lower:
                            return "**Code Explanation (Mock Mode)**\n\nThis code defines functions and logic.\nInstall Ollama (`ollama pull llama3`) for real AI explanations.\n\nVisit https://ollama.ai to get started."
elif "improve" in prompt_lower:
            return "**Improvement Suggestions (Mock Mode)**\n\n1. Add type hints\n2. Add docstrings\n3. Handle edge cases\n4. Use constants for magic numbers\n\nInstall Ollama for AI-powered suggestions."
elif "test" in prompt_lower:
            return "**Generated Tests (Mock Mode)**\n\n```python\nimport pytest\n\ndef test_example():\n    assert your_function(input) == expected\n\ndef test_edge_case():\n    assert your_function(None) is not None\n```\n\nInstall Ollama for AI-generated tests."
elif "complex" in prompt_lower:
            return "**Complexity Analysis (Mock Mode)**\n\nTime Complexity: O(n)\nSpace Complexity: O(1)\n\nInstall Ollama for detailed analysis."
elif "debug" in prompt_lower:
            return "**Debug Suggestions (Mock Mode)**\n\n1. Check input validation\n2. Add print/logging statements\n3. Review error messages\n4. Test boundary conditions\n\nInstall Ollama for AI-powered debugging."
        return "Mock response - Install Ollama and run `ollama pull llama3` for full AI functionality."

    async def close(self):
              await self.client.aclose()
