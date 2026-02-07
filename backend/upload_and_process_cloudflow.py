"""
Upload and process CloudFlow document with tips
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
    """Upload and process CloudFlow document"""
    
    # Create async engine
    DATABASE_URL = "sqlite+aiosqlite:///./customer_onboarding.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Read the PDF file
    pdf_path = "CloudFlow_Product_Documentation.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        print("Please ensure CloudFlow_Product_Documentation.pdf is in the backend directory")
        return
    
    print(f"📄 Reading file: {pdf_path}")
    
    # Extract content using document processor
    doc_processor = DocumentProcessor()
    
    # Read file content
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    
    # Create a mock UploadFile object
    class MockUploadFile:
        def __init__(self, filename, content):
            self.filename = filename
            self.content = content
            self.size = len(content)
        
        async def read(self):
            return self.content
    
    mock_file = MockUploadFile(pdf_path, file_content)
    
    # Extract text content
    print("📝 Extracting text from PDF...")
    content = await doc_processor.extract_content(mock_file)
    print(f"✅ Extracted {len(content)} characters")
    
    # Calculate hash
    content_hash = doc_processor.calculate_content_hash(content)
    
    async with async_session() as session:
        # Create document record
        document = Document(
            filename=pdf_path,
            original_content=content,
            content_hash=content_hash,
            file_size=len(file_content)
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
                print(f"  💡 Tip: {step['tip'][:80]}...")
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
        print("✅ Document processed and saved successfully!")
        print(f"\n📊 Document ID: {document.id}")
        print(f"📄 Filename: {document.filename}")
        print(f"📝 Content: {len(document.original_content)} characters")
        print(f"✨ Steps: {len(steps)}")
        print(f"💡 Tips included: Yes")


if __name__ == "__main__":
    asyncio.run(upload_and_process())
