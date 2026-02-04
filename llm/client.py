"""
LLM Client - Supports multiple LLM providers (Gemini and OpenAI)
"""
import os
import json
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMClient:
    """Unified LLM client supporting Gemini and OpenAI"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client with specified provider.
        
        Args:
            provider: 'gemini' or 'openai'. If None, auto-detects based on available keys.
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0
        }
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate LLM client based on provider"""
        if self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("google-generativeai package not installed")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "gpt-3.5-turbo"
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text response from LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        if self.provider == "gemini":
            return self._generate_gemini(prompt, system_prompt)
        else:
            return self._generate_openai(prompt, system_prompt)
    
    def _generate_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Gemini"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.model.generate_content(full_prompt)
        
        # Track usage
        prompt_tokens = self._estimate_tokens(full_prompt)
        completion_tokens = self._estimate_tokens(response.text)
        self._track_usage(prompt_tokens, completion_tokens)
        
        return response.text
    
    def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7
        )
        
        # Track usage
        if hasattr(response, 'usage') and response.usage:
            self._track_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
        else:
            prompt_tokens = self._estimate_tokens(str(messages))
            completion_tokens = self._estimate_tokens(response.choices[0].message.content)
            self._track_usage(prompt_tokens, completion_tokens)
            
        return response.choices[0].message.content
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """
        Generate JSON response from LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Parsed JSON response as dictionary
        """
        json_instruction = "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations."
        
        if self.provider == "gemini":
            response = self._generate_gemini(prompt + json_instruction, system_prompt)
        else:
            response = self._generate_openai(prompt + json_instruction, system_prompt)
        
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        return json.loads(response)

    def get_token_usage(self) -> dict:
        """Get accumulated token usage statistics"""
        return self._token_usage

    def _track_usage(self, prompt_tokens: int, completion_tokens: int):
        """Track token usage and estimated cost"""
        self._token_usage["prompt_tokens"] += prompt_tokens
        self._token_usage["completion_tokens"] += completion_tokens
        self._token_usage["total_tokens"] += prompt_tokens + completion_tokens
        
        # Estimate cost (approximate rates)
        cost = 0.0
        if self.provider == "openai":
            # GPT-3.5 Turbo rates
            cost = (prompt_tokens * 0.0005 / 1000) + (completion_tokens * 0.0015 / 1000)
        elif self.provider == "gemini":
            # Gemini Flash rates (free tier or low cost)
            cost = (prompt_tokens * 0.000125 / 1000) + (completion_tokens * 0.000375 / 1000)
            
        self._token_usage["estimated_cost_usd"] += cost

    def _estimate_tokens(self, text: str) -> int:
        """Simple rule-of-thumb token estimation (4 chars ~= 1 token)"""
        return len(text) // 4
