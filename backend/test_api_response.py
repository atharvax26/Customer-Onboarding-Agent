"""
Test script to verify API is returning AI-generated content
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.onboarding_service import OnboardingEngine
from app.database import User, Document, OnboardingSession

async def test_api_response():
    # Create async engine
    engine = create_async_engine("sqlite+aiosqlite:///./customer_onboarding.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get the latest onboarding session
        from sqlalchemy import select, desc
        result = await session.execute(
            select(OnboardingSession)
            .where(OnboardingSession.status == 'ACTIVE')
            .order_by(desc(OnboardingSession.id))
            .limit(1)
        )
        onboarding_session = result.scalar_one_or_none()
        
        if not onboarding_session:
            print("❌ No active onboarding session found")
            return
        
        print(f"✅ Found active session: ID={onboarding_session.id}")
        print(f"   Document ID: {onboarding_session.document_id}")
        print(f"   Current Step: {onboarding_session.current_step}")
        print(f"   Total Steps: {onboarding_session.total_steps}")
        print()
        
        # Get the document
        doc_result = await session.execute(
            select(Document).where(Document.id == onboarding_session.document_id)
        )
        document = doc_result.scalar_one_or_none()
        
        if document:
            print(f"✅ Document found: {document.filename}")
            print(f"   Has step_tasks: {document.step_tasks is not None}")
            if document.step_tasks:
                print(f"   Number of tasks: {len(document.step_tasks)}")
                print(f"   Tasks: {document.step_tasks}")
            print()
        
        # Get current step using the service
        engine = OnboardingEngine(session)
        try:
            step_response = await engine.get_current_step(onboarding_session.id)
            print("✅ API Response:")
            print(f"   Step Number: {step_response.step_number}")
            print(f"   Total Steps: {step_response.total_steps}")
            print(f"   Title: {step_response.title}")
            print(f"   Content: {step_response.content}")
            print(f"   Tasks: {step_response.tasks}")
            print(f"   Estimated Time: {step_response.estimated_time}")
            print()
            
            # Check if it's AI-generated or hardcoded
            if step_response.title == "Review Document Content":
                print("✅ SUCCESS: Using AI-generated content!")
            elif step_response.title == "API Authentication Setup":
                print("❌ PROBLEM: Using hardcoded content!")
            else:
                print(f"⚠️  Unknown content source: {step_response.title}")
                
        except Exception as e:
            print(f"❌ Error getting current step: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_response())
