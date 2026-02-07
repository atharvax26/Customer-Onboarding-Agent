"""
Reprocess existing document with Gemini to include tips
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Document
from app.services.gemini_client import GeminiClient
from sqlalchemy import select
from datetime import datetime


async def reprocess_document():
    """Reprocess document ID 1 with Gemini to include tips"""
    
    # Create async engine
    DATABASE_URL = "sqlite+aiosqlite:///./customer_onboarding.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get document
        result = await session.execute(select(Document).where(Document.id == 1))
        document = result.scalar_one_or_none()
        
        if not document:
            print("❌ Document ID 1 not found")
            return
        
        print(f"📄 Found document: {document.filename}")
        print(f"📝 Content length: {len(document.original_content)} characters")
        
        # Initialize Gemini client
        gemini_client = GeminiClient()
        print("✅ Gemini client initialized")
        
        # Generate new guide with tips
        print("🤖 Generating onboarding guide with tips using Gemini...")
        start_time = datetime.utcnow()
        
        guide_data = await gemini_client.generate_onboarding_guide(
            document_content=document.original_content,
            user_role="Developer"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Extract summary and steps
        summary_text = guide_data.get('summary', 'Document processed successfully')
        steps = guide_data.get('steps', [])
        
        print(f"\n✅ Generated {len(steps)} steps in {processing_time:.2f} seconds")
        print(f"\n📋 Summary: {summary_text}\n")
        
        # Display steps with tips
        for step in steps:
            print(f"Step {step['step']}: {step['title']}")
            print(f"  ⏱️  Time: {step['estimated_time']} min")
            print(f"  📝 Description: {step['description']}")
            if 'tip' in step:
                print(f"  💡 Tip: {step['tip']}")
            print(f"  ✓ Subtasks: {len(step.get('subtasks', []))}")
            print()
        
        # Format summary with metadata
        summary_data = {
            'text': summary_text,
            'processing_metadata': {
                'model_used': 'gemini-2.5-flash',
                'processed_at': datetime.utcnow().isoformat(),
                'processing_time': processing_time,
                'steps_generated': len(steps),
                'includes_tips': True
            }
        }
        
        # Update document
        document.processed_summary = summary_data
        document.step_tasks = steps
        
        await session.commit()
        print("✅ Document updated successfully with tips!")


if __name__ == "__main__":
    asyncio.run(reprocess_document())
