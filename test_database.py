"""Test database setup."""
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print("=" * 60)
print("💾 TESTING DATABASE")
print("=" * 60)

try:
    from src.core.config import settings
    
    print(f"\n1️⃣ Database Type: {settings.db_type}")
    print(f"   URL: {settings.database_url}")
    
    # Create engine
    print("\n2️⃣ Creating database engine...")
    engine = create_engine(settings.database_url, echo=False)
    
    # Test connection
    print("\n3️⃣ Testing connection...")
    with engine.connect() as conn:
        print("   ✅ Database connection successful!")
    
    # Create a simple test table
    print("\n4️⃣ Creating test table...")
    Base = declarative_base()
    
    class TestTable(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        description = Column(Text)
    
    Base.metadata.create_all(engine)
    print("   ✅ Test table created!")
    
    # Test insert
    print("\n5️⃣ Testing insert...")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    test_record = TestTable(
        name="Test Paper",
        description="This is a test record"
    )
    session.add(test_record)
    session.commit()
    print("   ✅ Record inserted!")
    
    # Test query
    print("\n6️⃣ Testing query...")
    result = session.query(TestTable).first()
    print(f"   ✅ Record retrieved: {result.name}")
    
    # Cleanup
    session.close()
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE TEST PASSED!")
    print("=" * 60)
    print(f"\n📁 Database file created: research_papers.db")
    print("   (You can delete it after testing if you want)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)