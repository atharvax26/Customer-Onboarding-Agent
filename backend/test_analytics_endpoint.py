"""
Quick test script to check if analytics endpoints are working
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.analytics_service import AnalyticsService

async def test_real_time_metrics():
    # Create async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///./customer_onboarding.db",
        echo=True
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        analytics_service = AnalyticsService(session)
        
        try:
            print("\n" + "="*60)
            print("Testing Real-Time Metrics Endpoint")
            print("="*60)
            
            metrics = await analytics_service.get_real_time_metrics()
            
            print("\n✅ Success! Metrics retrieved:")
            print(f"  Active Sessions: {metrics['active_sessions']}")
            print(f"  Total Sessions: {metrics['total_sessions']}")
            print(f"  Total Interventions Today: {metrics['total_interventions_today']}")
            print(f"  Average Engagement (24h): {metrics['average_engagement_24h']}%")
            print(f"  Last Updated: {metrics['last_updated']}")
            
            print("\n" + "="*60)
            print("All fields present and correct!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_real_time_metrics())
