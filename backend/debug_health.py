#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.health_monitor import health_monitor

async def test_health():
    result = await health_monitor.check_system_health()
    print('Overall status:', result['status'])
    print('Components:')
    for name, component in result['components'].items():
        print(f'  {name}: {component["status"]}')
        if 'error' in component:
            print(f'    Error: {component["error"]}')

if __name__ == "__main__":
    asyncio.run(test_health())