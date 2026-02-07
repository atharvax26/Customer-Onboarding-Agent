"""
Upload and process sample document with tips
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Document
from app.services.gemini_client import GeminiClient
from app.services.document_processor import DocumentProcessor


async def upload_and_process():
    """Upload and process sample document"""
    
    # Create async engine
    DATABASE_URL = "sqlite+aiosqlite:///./customer_onboarding.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Read the text file
    txt_path = "sample_product_doc.txt"
    if not os.path.exists(txt_path):
        print(f"❌ File not found: {txt_path}")
        return
    
    print(f"📄 Reading file: {txt_path}")
    
    # Read file content
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✅ Read {len(content)} characters")
    
    # Calculate hash
    doc_processor = DocumentProcessor()
    content_hash = doc_processor.calculate_content_hash(content)
    
    async with async_session() as session:
        # Create document record
        document = Document(
            filename="CloudFlow_Product_Documentation.txt",
            original_content=content,
            content_hash=content_hash,
            file_size=len(content.encode('utf-8'))
        )
        
        session.add(document)
        await session.commit()
        await session.refresh(document)
        
        print(f"✅ Document uploaded with ID: {document.id}")
        
        # Initialize Gemini client
        gemini_client = GeminiClient()
        print("✅ Gemini client initialized")
        
        # Generate onboarding guide with tips
        print("🤖 Generating onboarding guide with tips using Gemini...")
        start_time = datetime.utcnow()
        
        guide_data = await gemini_client.generate_onboarding_guide(
            document_content=content,
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
            if 'tip' in step:
                print(f"  💡 Tip: {step['tip']}")
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
        
        # Update document with processed content
        document.processed_summary = summary_data
        document.step_tasks = steps
        
        await session.commit()
        print("\n✅ Document processed and saved successfully!")
        print(f"\n📊 Document ID: {document.id}")
        print(f"📄 Filename: {document.filename}")
        print(f"📝 Content: {len(document.original_content)} characters")
        print(f"✨ Steps: {len(steps)}")
        print(f"💡 Tips included: Yes")


if __name__ == "__main__":
    asyncio.run(upload_and_process())
