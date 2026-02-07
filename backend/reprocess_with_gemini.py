"""
Script to reprocess document with Gemini AI
Replaces mock data with actual AI-generated onboarding guide
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.scaledown_service import ScaleDownService
from app.database import Document
from sqlalchemy import select

DATABASE_URL = "sqlite+aiosqlite:///./customer_onboarding.db"

async def reprocess_document(document_id: int):
    """Reprocess a document with Gemini AI"""
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Get the document
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            print(f"❌ Document with ID {document_id} not found")
            return False
        
        print(f"📄 Found document: {document.filename}")
        print(f"📝 Content length: {len(document.original_content)} characters")
        
        # Initialize service
        scaledown_service = ScaleDownService()
        
        if not scaledown_service.gemini_client:
            print("❌ Gemini AI client not initialized!")
            print("   Check that GEMINI_API_KEY is set in .env file")
            return False
        
        print("✅ Gemini AI client initialized")
        print("🔄 Processing document with Gemini AI...")
        print("   This may take 30-60 seconds...")
        
        try:
            # Process the document
            result = await scaledown_service.process_document(document_id, session)
            
            print(f"\n✅ Document processed successfully!")
            print(f"📊 Summary: {result.summary[:100]}...")
            print(f"📋 Number of steps: {len(result.tasks)}")
            print(f"⏱️  Processing time: {result.processing_time:.2f} seconds")
            
            print("\n📋 Generated Onboarding Steps:")
            for i, task in enumerate(result.tasks, 1):
                title = task.get('title', 'Untitled')
                desc = task.get('description', 'No description')
                time_est = task.get('estimated_time', 'N/A')
                subtasks = task.get('subtasks', [])
                
                print(f"\n  Step {i}: {title}")
                print(f"  ⏱️  Estimated time: {time_est} minutes")
                print(f"  📝 {desc[:80]}...")
                if subtasks:
                    print(f"  ✓ {len(subtasks)} subtasks")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error processing document: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    await engine.dispose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python reprocess_with_gemini.py <document_id>")
        print("\nExample: python reprocess_with_gemini.py 1")
        sys.exit(1)
    
    try:
        document_id = int(sys.argv[1])
    except ValueError:
        print("❌ Document ID must be a number")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Gemini AI Document Reprocessing")
    print("=" * 60)
    print(f"\nDocument ID: {document_id}\n")
    
    success = await reprocess_document(document_id)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Document reprocessing completed successfully!")
        print("=" * 60)
        print("\n📱 Next steps:")
        print("  1. Refresh your browser")
        print("  2. Go to the Onboarding page")
        print("  3. You should now see CloudFlow-specific content!")
        print("\n")
    else:
        print("\n" + "=" * 60)
        print("❌ Document reprocessing failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
