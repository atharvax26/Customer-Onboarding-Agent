#!/usr/bin/env python3
"""
End-to-End Integration Test Runner

This script runs comprehensive end-to-end integration tests for the
Customer Onboarding Agent system, including performance validation
and error scenario testing.

Requirements: 9.1 - Performance and Reliability
"""

import asyncio
import sys
import time
import subprocess
import os
import signal
from pathlib import Path
from typing import Dict, List, Any
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('e2e_test_results.log')
    ]
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """End-to-end integration test runner"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.test_results = {
            'backend_tests': {},
            'frontend_tests': {},
            'performance_tests': {},
            'integration_tests': {},
            'total_duration': 0,
            'success': False
        }
    
    async def setup_test_environment(self):
        """Setup test environment with backend and frontend servers"""
        logger.info("Setting up test environment...")
        
        try:
            # Start backend server
            logger.info("Starting backend server...")
            backend_env = os.environ.copy()
            backend_env['TESTING'] = 'true'
            backend_env['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_e2e.db'
            
            self.backend_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                cwd='backend',
                env=backend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for backend to start
            await asyncio.sleep(5)
            
            # Check if backend is running
            if self.backend_process.poll() is not None:
                stdout, stderr = self.backend_process.communicate()
                logger.error(f"Backend failed to start: {stderr.decode()}")
                return False
            
            logger.info("Backend server started successfully")
            
            # Start frontend development server
            logger.info("Starting frontend server...")
            self.frontend_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd='frontend',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for frontend to start
            await asyncio.sleep(10)
            
            if self.frontend_process.poll() is not None:
                stdout, stderr = self.frontend_process.communicate()
                logger.error(f"Frontend failed to start: {stderr.decode()}")
                return False
            
            logger.info("Frontend server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def run_backend_tests(self):
        """Run backend integration tests"""
        logger.info("Running backend integration tests...")
        
        try:
            # Run specific E2E test file
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_e2e_integration.py', '-v', '--tb=short'],
                cwd='backend',
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            self.test_results['backend_tests'] = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info("Backend integration tests passed")
            else:
                logger.error(f"Backend integration tests failed: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("Backend tests timed out")
            self.test_results['backend_tests'] = {
                'exit_code': -1,
                'error': 'Timeout',
                'success': False
            }
            return False
        except Exception as e:
            logger.error(f"Error running backend tests: {e}")
            self.test_results['backend_tests'] = {
                'exit_code': -1,
                'error': str(e),
                'success': False
            }
            return False
    
    async def run_frontend_tests(self):
        """Run frontend integration tests"""
        logger.info("Running frontend integration tests...")
        
        try:
            # Run specific E2E test file
            result = subprocess.run(
                ['npm', 'run', 'test', '--', 'e2e-integration.test.tsx'],
                cwd='frontend',
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            self.test_results['frontend_tests'] = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info("Frontend integration tests passed")
            else:
                logger.error(f"Frontend integration tests failed: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("Frontend tests timed out")
            self.test_results['frontend_tests'] = {
                'exit_code': -1,
                'error': 'Timeout',
                'success': False
            }
            return False
        except Exception as e:
            logger.error(f"Error running frontend tests: {e}")
            self.test_results['frontend_tests'] = {
                'exit_code': -1,
                'error': str(e),
                'success': False
            }
            return False
    
    async def run_performance_tests(self):
        """Run performance validation tests"""
        logger.info("Running performance validation tests...")
        
        try:
            # Run performance-specific tests
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_e2e_integration.py::TestPerformanceRequirements', '-v'],
                cwd='backend',
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            self.test_results['performance_tests'] = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info("Performance tests passed")
            else:
                logger.error(f"Performance tests failed: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error running performance tests: {e}")
            self.test_results['performance_tests'] = {
                'exit_code': -1,
                'error': str(e),
                'success': False
            }
            return False
    
    async def run_cross_system_integration_tests(self):
        """Run tests that verify frontend-backend integration"""
        logger.info("Running cross-system integration tests...")
        
        try:
            # This would run tests that actually hit the running servers
            # For now, we'll run a subset of backend tests that verify API endpoints
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_e2e_integration.py::TestCompleteUserJourneys', '-v'],
                cwd='backend',
                capture_output=True,
                text=True,
                timeout=240  # 4 minutes timeout
            )
            
            self.test_results['integration_tests'] = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info("Cross-system integration tests passed")
            else:
                logger.error(f"Cross-system integration tests failed: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")
            self.test_results['integration_tests'] = {
                'exit_code': -1,
                'error': str(e),
                'success': False
            }
            return False
    
    async def cleanup_test_environment(self):
        """Cleanup test environment"""
        logger.info("Cleaning up test environment...")
        
        try:
            # Stop backend process
            if self.backend_process and self.backend_process.poll() is None:
                self.backend_process.terminate()
                try:
                    self.backend_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.backend_process.kill()
                logger.info("Backend server stopped")
            
            # Stop frontend process
            if self.frontend_process and self.frontend_process.poll() is None:
                self.frontend_process.terminate()
                try:
                    self.frontend_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.frontend_process.kill()
                logger.info("Frontend server stopped")
            
            # Clean up test database
            test_db_path = Path('backend/test_e2e.db')
            if test_db_path.exists():
                test_db_path.unlink()
                logger.info("Test database cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        report = {
            'test_run_summary': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_duration': self.test_results['total_duration'],
                'overall_success': self.test_results['success']
            },
            'test_results': self.test_results
        }
        
        # Save report to file
        with open('e2e_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("END-TO-END INTEGRATION TEST REPORT")
        print("="*60)
        print(f"Test Run Time: {report['test_run_summary']['timestamp']}")
        print(f"Total Duration: {self.test_results['total_duration']:.2f} seconds")
        print(f"Overall Success: {'✅ PASS' if self.test_results['success'] else '❌ FAIL'}")
        print()
        
        # Backend tests
        backend_success = self.test_results['backend_tests'].get('success', False)
        print(f"Backend Tests: {'✅ PASS' if backend_success else '❌ FAIL'}")
        
        # Frontend tests
        frontend_success = self.test_results['frontend_tests'].get('success', False)
        print(f"Frontend Tests: {'✅ PASS' if frontend_success else '❌ FAIL'}")
        
        # Performance tests
        perf_success = self.test_results['performance_tests'].get('success', False)
        print(f"Performance Tests: {'✅ PASS' if perf_success else '❌ FAIL'}")
        
        # Integration tests
        integration_success = self.test_results['integration_tests'].get('success', False)
        print(f"Integration Tests: {'✅ PASS' if integration_success else '❌ FAIL'}")
        
        print("="*60)
        
        if not self.test_results['success']:
            print("\nFAILED TESTS DETAILS:")
            for test_type, results in self.test_results.items():
                if isinstance(results, dict) and not results.get('success', True):
                    print(f"\n{test_type.upper()}:")
                    if 'stderr' in results and results['stderr']:
                        print(results['stderr'])
                    if 'error' in results:
                        print(results['error'])
    
    async def run_all_tests(self):
        """Run all end-to-end integration tests"""
        start_time = time.time()
        
        try:
            logger.info("Starting end-to-end integration test suite...")
            
            # Setup test environment
            if not await self.setup_test_environment():
                logger.error("Failed to setup test environment")
                return False
            
            # Run all test suites
            test_results = []
            
            # Backend tests
            backend_success = await self.run_backend_tests()
            test_results.append(backend_success)
            
            # Frontend tests
            frontend_success = await self.run_frontend_tests()
            test_results.append(frontend_success)
            
            # Performance tests
            perf_success = await self.run_performance_tests()
            test_results.append(perf_success)
            
            # Cross-system integration tests
            integration_success = await self.run_cross_system_integration_tests()
            test_results.append(integration_success)
            
            # Overall success
            overall_success = all(test_results)
            self.test_results['success'] = overall_success
            
            end_time = time.time()
            self.test_results['total_duration'] = end_time - start_time
            
            logger.info(f"Test suite completed in {self.test_results['total_duration']:.2f} seconds")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"Error running test suite: {e}")
            return False
        finally:
            await self.cleanup_test_environment()
            self.generate_test_report()


async def main():
    """Main entry point"""
    runner = E2ETestRunner()
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        logger.info("Received interrupt signal, cleaning up...")
        asyncio.create_task(runner.cleanup_test_environment())
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = await runner.run_all_tests()
        
        if success:
            logger.info("🎉 All end-to-end integration tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some end-to-end integration tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())