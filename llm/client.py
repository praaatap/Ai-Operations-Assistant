"""
LLM Client - Supports Gemini and Groq LLM providers using LangChain
"""
import os
import json
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

class LLMClient:
    """Unified LLM client supporting Gemini and Groq via LangChain"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client with specified provider.
        
        Args:
            provider: 'gemini' or 'groq'. If None, auto-detects based on available keys.
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0
        }
        self.model = self._setup_client()

    def _setup_client(self):
        """Setup the appropriate LangChain Chat Model"""
        if self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            
        elif self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=api_key,
                temperature=0.7
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}. Supported: 'gemini', 'groq'")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response from LLM using LangChain.
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.model.invoke(messages)
            content = response.content
            
            # Track usage
            self._track_usage_from_response(response)
            
            return content
        except Exception as e:
            # Simple fallback error handling
            print(f"Error during generation: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """
        Generate JSON response from LLM using LangChain.
        """
        json_instruction = "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations."
        full_user_prompt = prompt + json_instruction
        
        response_text = self.generate(full_user_prompt, system_prompt)
        
        # Clean response
        cleaned_response = self._clean_json_text(response_text)
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            # Last ditch effort: try to find JSON blob
            import re
            match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    def get_token_usage(self) -> dict:
        """Get accumulated token usage statistics"""
        return self._token_usage

    def _track_usage_from_response(self, response: Any):
        """Track token usage from LangChain response metadata"""
        try:
            usage = response.response_metadata.get("token_usage", {})
            if not usage:
                 usage = response.response_metadata.get("usage", {})

            # Normalize keys (Gemini vs Groq/OpenAI formats differ)
            p_tokens = usage.get("prompt_tokens") or usage.get("prompt_token_count", 0)
            c_tokens = usage.get("completion_tokens") or usage.get("candidates_token_count", 0) or usage.get("completion_token_count", 0)
            
            if p_tokens or c_tokens:
                self._update_usage_stats(p_tokens, c_tokens)
            else:
                # Fallback estimate
                self._update_usage_stats(len(str(response.content))//4, len(str(response.content))//4)
                
        except Exception:
            pass

    def _update_usage_stats(self, prompt_tokens: int, completion_tokens: int):
        """Update internal counters and cost estimate"""
        self._token_usage["prompt_tokens"] += prompt_tokens
        self._token_usage["completion_tokens"] += completion_tokens
        self._token_usage["total_tokens"] += prompt_tokens + completion_tokens
        
        # Estimate cost (approximate rates)
        cost = 0.0
        if self.provider == "gemini":
            # Gemini Flash rates
            cost = (prompt_tokens * 0.000125 / 1000) + (completion_tokens * 0.000375 / 1000)
        elif self.provider == "groq":
            # Llama 3 70B rates on Groq (approx)
            cost = (prompt_tokens * 0.00059 / 1000) + (completion_tokens * 0.00079 / 1000)
            
        self._token_usage["estimated_cost_usd"] += cost

    def _clean_json_text(self, text: str) -> str:
        """Remove markdown code blocks and whitespace"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
