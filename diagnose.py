import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    print(f"\n[-] Python Executable: {sys.executable}")
    # print(f"[-] Python Path: {sys.path}")
    print("\n[-] Checking Environment Configuration...")
    
    try:
        import google.generativeai
        print("  - [OK] Import google.generativeai success")
    except ImportError as e:
        print(f"  - [ERROR] Import google.generativeai failed: {e}")
    
    # Check API Keys
    keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "gemini"),
    }
    
    valid_llm_found = False
    for key, val in keys.items():
        if "API_KEY" in key:
            status = "[OK] Found" if val and len(val) > 10 and not val.startswith("your_") else "[MISSING] Missing/Default"
            print(f"  - {key}: {status}")
            if status == "[OK] Found" and key != "NEWS_API_KEY":
                valid_llm_found = True
        else:
            print(f"  - {key}: {val}")
            
    if not valid_llm_found:
        print("\n[CRITICAL]: No valid LLM API Key found! The system cannot work without one.")
        print("Please edit your .env file and add a valid key for GEMINI, OPENAI, or GROQ.")
        return False
        
    return True

def test_llm_connection():
    print("\n[?] Testing LLM Connectivity...")
    try:
        from llm.client import LLMClient
        client = LLMClient()
        print(f"  - Client initialized for provider: {client.provider}")
        
        print("  - Attempting to generate text...")
        response = client.generate("Hello, are you working?")
        print(f"  - [OK] Response received: {response}")
        
        print("  - Attempting to generate JSON (Planner test)...")
        json_response = client.generate_json("Create a simple JSON object with a key 'status' and value 'working'")
        print(f"  - [OK] JSON received: {json_response}")
        
        return True
    except Exception as e:
        print(f"\n[ERROR] LLM Connection Failed: {str(e)}")
        print("This is likely why the system is returning 'Partial' results.")
        return False

if __name__ == "__main__":
    print("="*50)
    print("AI OPERATIONS ASSISTANT - DIAGNOSTIC TOOL")
    print("="*50)
    
    env_ok = check_environment()
    if env_ok:
        llm_ok = test_llm_connection()
        
        if llm_ok:
            print("\n[SUCCESS] SYSTEM HEALTHY. You should be able to run the app.")
        else:
            print("\n[FAILURE] SYSTEM ISSUES DETECTED. Please fix the errors above.")
    else:
        print("\n[FAILURE] ENVIRONMENT ISSUES DETECTED. Please check your .env file.")
    
    # print("\nPress Enter to exit...")
    # input()
