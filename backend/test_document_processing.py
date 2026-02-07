"""
Test script to debug document processing issues
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal, Document, User
from app.services.scaledown_service import ScaleDownService

async def test_processing():
    """Test document processing to identify issues"""
    
    print("=" * 60)
    print("Testing Document Processing")
    print("=" * 60)
    
    service = ScaleDownService()
    
    async with AsyncSessionLocal() as db:
        # Get first user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users found")
            return False
        
        print(f"✓ Testing with user: {user.email} (ID: {user.id})")
        
        # Get unprocessed documents
        result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.processed_summary == None
            )
        )
        unprocessed = result.scalars().all()
        
        if not unprocessed:
            print("✓ No unprocessed documents found")
            
            # Get all documents for this user
            result = await db.execute(
                select(Document).where(Document.user_id == user.id)
            )
            all_docs = result.scalars().all()
            print(f"✓ User has {len(all_docs)} total document(s)")
            
            for doc in all_docs:
                status = "Processed" if doc.processed_summary else "Unprocessed"
                print(f"  - {doc.filename} (ID: {doc.id}) - {status}")
            
            return True
        
        print(f"\n✓ Found {len(unprocessed)} unprocessed document(s)")
        
        # Try to process the first one
        doc = unprocessed[0]
        print(f"\nAttempting to process: {doc.filename} (ID: {doc.id})")
        print(f"Content length: {len(doc.original_content)} characters")
        
        try:
            print("\nCalling process_document...")
            result = await service.process_document(doc.id, db, user.id)
            
            print("\n✓ Processing successful!")
            print(f"  Summary: {result.summary[:100]}...")
            print(f"  Tasks generated: {len(result.tasks)}")
            print(f"  Processing time: {result.processing_time:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Processing failed!")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error message: {str(e)}")
            
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
            
            return False

if __name__ == "__main__":
    success = asyncio.run(test_processing())
    print("=" * 60)
    if success:
        print("✓ Test completed!")
        sys.exit(0)
    else:
        print("✗ Test failed!")
        sys.exit(1)
