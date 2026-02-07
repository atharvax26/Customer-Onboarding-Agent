#!/usr/bin/env python3
"""
Performance Monitoring Script for E2E Tests

This script monitors system performance during end-to-end testing
to validate performance requirements.

Requirements: 9.1 - Performance and Reliability
"""

import asyncio
import time
import psutil
import httpx
import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    response_time_ms: float
    endpoint: str
    status_code: int
    error: str = None


class PerformanceMonitor:
    """Performance monitoring for E2E tests"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.metrics: List[PerformanceMetric] = []
        self.monitoring = False
    
    async def monitor_system_resources(self, duration: int = 60):
        """Monitor system resources during testing"""
        logger.info(f"Starting system resource monitoring for {duration} seconds...")
        
        start_time = time.time()
        while time.time() - start_time < duration and self.monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Test API response time
                response_time, status_code, error = await self.test_api_response_time()
                
                metric = PerformanceMetric(
                    timestamp=datetime.now().isoformat(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_mb=memory.used / 1024 / 1024,
                    response_time_ms=response_time,
                    endpoint="/health",
                    status_code=status_code,
                    error=error
                )
                
                self.metrics.append(metric)
                
                # Log if performance is concerning
                if response_time > 2000:  # > 2 seconds
                    logger.warning(f"Slow API response: {response_time:.2f}ms")
                
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
                if memory.percent > 80:
                    logger.warning(f"High memory usage: {memory.percent:.1f}%")
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(5)
    
    async def test_api_response_time(self) -> tuple[float, int, str]:
        """Test API response time"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=10.0)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return response_time, response.status_code, None
            
        except Exception as e:
            return 0.0, 0, str(e)
    
    async def test_concurrent_load(self, concurrent_requests: int = 10) -> Dict[str, Any]:
        """Test system under concurrent load"""
        logger.info(f"Testing concurrent load with {concurrent_requests} requests...")
        
        async def make_request(request_id: int) -> Dict[str, Any]:
            try:
                start_time = time.time()
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health", timeout=10.0)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    'request_id': request_id,
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
                
            except Exception as e:
                return {
                    'request_id': request_id,
                    'response_time_ms': 0,
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time_ms'] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        total_duration = (end_time - start_time) * 1000
        
        load_test_results = {
            'concurrent_requests': concurrent_requests,
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / concurrent_requests * 100,
            'total_duration_ms': total_duration,
            'avg_response_time_ms': avg_response_time,
            'max_response_time_ms': max_response_time,
            'min_response_time_ms': min_response_time,
            'requests_per_second': concurrent_requests / (total_duration / 1000) if total_duration > 0 else 0
        }
        
        logger.info(f"Load test completed: {load_test_results['success_rate']:.1f}% success rate")
        logger.info(f"Average response time: {avg_response_time:.2f}ms")
        
        return load_test_results
    
    async def test_endpoint_performance(self, endpoints: List[str]) -> Dict[str, Dict[str, Any]]:
        """Test performance of specific endpoints"""
        logger.info(f"Testing performance of {len(endpoints)} endpoints...")
        
        results = {}
        
        for endpoint in endpoints:
            try:
                # Test endpoint multiple times for average
                response_times = []
                status_codes = []
                
                for _ in range(5):  # 5 requests per endpoint
                    start_time = time.time()
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.base_url}{endpoint}", timeout=10.0)
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    response_times.append(response_time)
                    status_codes.append(response.status_code)
                    
                    await asyncio.sleep(0.1)  # Small delay between requests
                
                # Calculate statistics
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                results[endpoint] = {
                    'avg_response_time_ms': avg_response_time,
                    'max_response_time_ms': max_response_time,
                    'min_response_time_ms': min_response_time,
                    'status_codes': status_codes,
                    'success_rate': sum(1 for code in status_codes if 200 <= code < 300) / len(status_codes) * 100,
                    'meets_requirement': avg_response_time < 2000  # < 2 seconds requirement
                }
                
                logger.info(f"{endpoint}: {avg_response_time:.2f}ms avg ({'✅' if avg_response_time < 2000 else '❌'})")
                
            except Exception as e:
                results[endpoint] = {
                    'error': str(e),
                    'meets_requirement': False
                }
                logger.error(f"Error testing {endpoint}: {e}")
        
        return results
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        logger.info("Performance monitoring stopped")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report from collected metrics"""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        # Calculate statistics
        response_times = [m.response_time_ms for m in self.metrics if m.response_time_ms > 0]
        cpu_usage = [m.cpu_percent for m in self.metrics]
        memory_usage = [m.memory_percent for m in self.metrics]
        
        report = {
            'monitoring_duration': len(self.metrics) * 5,  # 5 seconds per metric
            'total_metrics': len(self.metrics),
            'api_performance': {
                'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0,
                'min_response_time_ms': min(response_times) if response_times else 0,
                'slow_responses': len([rt for rt in response_times if rt > 2000]),
                'meets_requirement': all(rt < 2000 for rt in response_times) if response_times else False
            },
            'system_resources': {
                'avg_cpu_percent': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                'max_cpu_percent': max(cpu_usage) if cpu_usage else 0,
                'avg_memory_percent': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'max_memory_percent': max(memory_usage) if memory_usage else 0
            },
            'raw_metrics': [asdict(m) for m in self.metrics]
        }
        
        return report
    
    def save_report(self, filename: str = "performance_report.json"):
        """Save performance report to file"""
        report = self.generate_performance_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {filename}")
        return report


async def main():
    """Main function for standalone performance testing"""
    monitor = PerformanceMonitor()
    
    try:
        logger.info("Starting performance monitoring...")
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Monitor for 30 seconds
        monitor_task = asyncio.create_task(monitor.monitor_system_resources(30))
        
        # Test concurrent load
        load_results = await monitor.test_concurrent_load(10)
        
        # Test specific endpoints
        endpoints = ["/health", "/", "/api/auth/me"]
        endpoint_results = await monitor.test_endpoint_performance(endpoints)
        
        # Wait for monitoring to complete
        await monitor_task
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Generate and save report
        report = monitor.save_report()
        
        # Print summary
        print("\n" + "="*50)
        print("PERFORMANCE TEST SUMMARY")
        print("="*50)
        
        if report.get('api_performance'):
            api_perf = report['api_performance']
            print(f"API Performance:")
            print(f"  Average Response Time: {api_perf['avg_response_time_ms']:.2f}ms")
            print(f"  Max Response Time: {api_perf['max_response_time_ms']:.2f}ms")
            print(f"  Meets Requirement (<2s): {'✅' if api_perf['meets_requirement'] else '❌'}")
        
        print(f"\nLoad Test Results:")
        print(f"  Success Rate: {load_results['success_rate']:.1f}%")
        print(f"  Requests/Second: {load_results['requests_per_second']:.1f}")
        
        print(f"\nEndpoint Performance:")
        for endpoint, results in endpoint_results.items():
            if 'error' not in results:
                meets_req = "✅" if results['meets_requirement'] else "❌"
                print(f"  {endpoint}: {results['avg_response_time_ms']:.2f}ms {meets_req}")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Performance monitoring failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())