"""
Health check script for monitoring.
Returns exit code 0 if healthy, 1 if unhealthy.
"""
import sys
from pathlib import Path
import requests
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.logging_config import app_logger


def check_health(timeout: int = 30) -> bool:
    """
    Check system health.
    
    Args:
        timeout: Timeout in seconds
    
    Returns:
        True if healthy
    """
    api_url = f"http://{settings.api_host}:{settings.api_port}"
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{api_url}/api/v1/health/detailed", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'healthy':
                    app_logger.info("✓ System is healthy")
                    
                    # Print component status
                    for component, status in data['components'].items():
                        emoji = "✓" if status == "healthy" else "✗"
                        app_logger.info(f"  {emoji} {component}: {status}")
                    
                    return True
                else:
                    app_logger.warning(f"System status: {data['status']}")
                    
                    # Print failed components
                    for component, status in data['components'].items():
                        if status != "healthy":
                            app_logger.error(f"  ✗ {component}: {status}")
                    
                    return False
            else:
                app_logger.warning(f"Health check returned {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            app_logger.warning("Cannot connect to API, retrying...")
        except Exception as e:
            app_logger.error(f"Health check error: {e}")
        
        time.sleep(2)
    
    app_logger.error("Health check timed out")
    return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health check for RAG system")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds"
    )
    
    args = parser.parse_args()
    
    healthy = check_health(timeout=args.timeout)
    
    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()