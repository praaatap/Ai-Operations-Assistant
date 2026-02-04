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
