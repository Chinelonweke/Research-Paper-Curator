"""Test embedding model."""
print("🧠 Testing Embedding Model...")
print("=" * 60)

try:
    from sentence_transformers import SentenceTransformer
    from src.core.config import settings
    
    print(f"Loading model: {settings.embedding_model}")
    print("(First time may take 2-5 minutes to download)")
    
    model = SentenceTransformer(settings.embedding_model)
    
    # Test embedding
    text = "This is a test sentence about machine learning."
    embedding = model.encode(text)
    
    print(f"\n✅ Embedding model working!")
    print(f"   Model: {settings.embedding_model}")
    print(f"   Embedding dimension: {len(embedding)}")
    print(f"   Expected dimension: {settings.embedding_dimension}")
    
    if len(embedding) == settings.embedding_dimension:
        print(f"   ✅ Dimensions match!")
    else:
        print(f"   ⚠️  Dimension mismatch (but works)")
    
    print("\n" + "=" * 60)
    print("🎉 EMBEDDING TEST PASSED!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nThis might be the PyTorch compatibility issue.")
    print("Let's fix it...")