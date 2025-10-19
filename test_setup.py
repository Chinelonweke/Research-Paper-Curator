"""Test if basic setup is working."""
import sys

print("=" * 60)
print("🧪 TESTING YOUR SETUP")
print("=" * 60)
print()

# Test 1: Import packages
print("📦 Test 1: Checking Python packages...")
try:
    import fastapi
    import sqlalchemy
    import groq
    import sentence_transformers
    import gradio
    print("   ✅ All required packages found")
except ImportError as e:
    print(f"   ❌ Missing package: {e}")
    sys.exit(1)

# Test 2: Load configuration
print()
print("⚙️  Test 2: Loading configuration...")
try:
    from src.core.config import settings
    print(f"   ✅ Configuration loaded")
    print(f"      App: {settings.app_name}")
    print(f"      Database: {settings.db_type}")
    print(f"      LLM: {settings.llm_provider}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    sys.exit(1)

# Test 3: Check Groq API key
print()
print("🔑 Test 3: Checking Groq API key...")
if settings.groq_api_key and len(settings.groq_api_key) > 20:
    print(f"   ✅ Groq API key found (starts with {settings.groq_api_key[:7]}...)")
else:
    print(f"   ❌ Groq API key not set in .env file")
    sys.exit(1)

# Test 4: Test Groq API
print()
print("🤖 Test 4: Testing Groq API...")
try:
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ Groq working! Response: {result}")
except Exception as e:
    print(f"   ❌ Groq error: {e}")
    sys.exit(1)

# Test 5: Test embedding model
print()
print("🧠 Test 5: Testing embedding model...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.embedding_model)
    embedding = model.encode("test")
    print(f"   ✅ Embedding model working! Dimension: {len(embedding)}")
except Exception as e:
    print(f"   ❌ Embedding error: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)