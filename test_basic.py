"""Basic test without sentence transformers."""
import sys

print("=" * 60)
print("🧪 TESTING BASIC SETUP")
print("=" * 60)
print()

# Test 1: Core packages
print("📦 Test 1: Checking core packages...")
try:
    import fastapi
    import sqlalchemy
    import groq
    import gradio
    print("   ✅ Core packages working")
except ImportError as e:
    print(f"   ❌ Missing package: {e}")
    sys.exit(1)

# Test 2: Configuration
print()
print("⚙️  Test 2: Loading configuration...")
try:
    from src.core.config import settings
    print(f"   ✅ Configuration loaded")
    print(f"      App: {settings.app_name}")
    print(f"      LLM: {settings.llm_provider}")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    sys.exit(1)

# Test 3: Groq API key
print()
print("🔑 Test 3: Checking Groq API key...")
if settings.groq_api_key and len(settings.groq_api_key) > 20:
    print(f"   ✅ API key found")
else:
    print(f"   ❌ API key not set")
    sys.exit(1)

# Test 4: Groq API
print()
print("🤖 Test 4: Testing Groq API...")
try:
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": "Say hello in one word"}],
        max_tokens=5
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ Groq working! Response: {result}")
except Exception as e:
    print(f"   ❌ Groq error: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🎉 BASIC TESTS PASSED!")
print("=" * 60)
print()
print("Now fixing the sentence-transformers compatibility issue...")