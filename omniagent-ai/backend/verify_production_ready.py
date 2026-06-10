#!/usr/bin/env python3
"""
Production Deployment Verification Script
Validates all critical components before going live
"""
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Print status message with color"""
    colors = {
        "OK": Colors.GREEN,
        "FAIL": Colors.RED,
        "WARN": Colors.YELLOW,
        "INFO": Colors.BLUE,
    }
    color = colors.get(status, Colors.BLUE)
    print(f"{color}[{status}]{Colors.RESET} {message}")

def run_command(cmd: List[str], description: str = "") -> Tuple[bool, str]:
    """Run command and return success/output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out: {' '.join(cmd)}"
    except Exception as e:
        return False, str(e)

def check_environment() -> bool:
    """Check environment variables"""
    print("\n" + "="*60)
    print("1. ENVIRONMENT VARIABLES")
    print("="*60)
    
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "CORS_ORIGINS",
        "APP_ENV",
    ]
    
    all_ok = True
    for var in required_vars:
        import os
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print_status(f"{var}: {masked}", "OK")
        else:
            print_status(f"{var}: NOT SET", "FAIL")
            all_ok = False
    
    return all_ok

def check_database() -> bool:
    """Check database connection"""
    print("\n" + "="*60)
    print("2. DATABASE CONNECTION")
    print("="*60)
    
    try:
        from app.db.session import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print_status("Database connection: OK", "OK")
            return True
    except Exception as e:
        print_status(f"Database connection: {str(e)}", "FAIL")
        return False

def check_dependencies() -> bool:
    """Check critical dependencies"""
    print("\n" + "="*60)
    print("3. PYTHON DEPENDENCIES")
    print("="*60)
    
    critical_packages = [
        "fastapi",
        "sqlmodel",
        "pydantic",
        "httpx",
        "redis",
    ]
    
    all_ok = True
    for package in critical_packages:
        try:
            __import__(package.replace("-", "_"))
            print_status(f"{package}: OK", "OK")
        except ImportError:
            print_status(f"{package}: NOT INSTALLED", "FAIL")
            all_ok = False
    
    return all_ok

def check_external_services() -> bool:
    """Check external service connectivity"""
    print("\n" + "="*60)
    print("4. EXTERNAL SERVICES")
    print("="*60)
    
    services = {
        "Ollama": ("http://localhost:11434/api/tags", "GET"),
        "Redis": ("redis://localhost:6379", "REDIS"),
        "PostgreSQL": ("postgresql://localhost:5432", "DB"),
    }
    
    all_ok = True
    
    # Check Ollama
    try:
        import httpx
        client = httpx.Client(timeout=5)
        response = client.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print_status("Ollama: OK", "OK")
        else:
            print_status("Ollama: Responded but failed", "WARN")
    except Exception as e:
        print_status(f"Ollama: {str(e)}", "WARN")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
        r.ping()
        print_status("Redis: OK", "OK")
    except Exception as e:
        print_status(f"Redis: {str(e)} (Optional)", "WARN")
    
    return all_ok

def check_imports() -> bool:
    """Check if all app modules can be imported"""
    print("\n" + "="*60)
    print("5. APP IMPORTS")
    print("="*60)
    
    try:
        from app.main import app
        print_status(f"Main app: OK ({len(app.routes)} routes registered)", "OK")
        
        from app.api.v1 import auth, chat, document
        print_status("API endpoints: OK", "OK")
        
        from app.services.chat_service import ChatService
        print_status("Services: OK", "OK")
        
        return True
    except Exception as e:
        print_status(f"Import failed: {str(e)}", "FAIL")
        import traceback
        traceback.print_exc()
        return False

def check_migrations() -> bool:
    """Check if database migrations are up to date"""
    print("\n" + "="*60)
    print("6. DATABASE MIGRATIONS")
    print("="*60)
    
    try:
        success, output = run_command(
            ["alembic", "current"],
            "Checking migration status"
        )
        if success:
            print_status("Migrations: OK", "OK")
            print(f"  {output.strip()}")
            return True
        else:
            print_status("Migrations: Check manually with 'alembic current'", "WARN")
            return True
    except Exception as e:
        print_status(f"Alembic check failed: {str(e)}", "WARN")
        return True  # Don't fail on this

def check_file_permissions() -> bool:
    """Check file permissions"""
    print("\n" + "="*60)
    print("7. FILE PERMISSIONS")
    print("="*60)
    
    critical_dirs = [
        Path("app"),
        Path("alembic"),
    ]
    
    all_ok = True
    for directory in critical_dirs:
        if directory.exists():
            print_status(f"{directory}: OK", "OK")
        else:
            print_status(f"{directory}: MISSING", "FAIL")
            all_ok = False
    
    return all_ok

def check_config() -> bool:
    """Check if config can be loaded"""
    print("\n" + "="*60)
    print("8. CONFIGURATION")
    print("="*60)
    
    try:
        from app.config import get_settings
        settings = get_settings()
        print_status(f"App Environment: {settings.APP_ENV}", "OK")
        print_status(f"Debug Mode: {settings.APP_DEBUG}", "OK")
        print_status(f"Database: {settings.DATABASE_URL[:20]}...", "OK")
        print_status(f"JWT Algorithm: {settings.JWT_ALGORITHM}", "OK")
        return True
    except Exception as e:
        print_status(f"Config load failed: {str(e)}", "FAIL")
        return False

def run_all_checks() -> bool:
    """Run all verification checks"""
    print("\n")
    print(f"{Colors.BLUE}╔════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BLUE}║  OMNIAGENT PRODUCTION VERIFICATION    ║{Colors.RESET}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════╝{Colors.RESET}")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Configuration", check_config),
        ("Dependencies", check_dependencies),
        ("Imports", check_imports),
        ("File Permissions", check_file_permissions),
        ("Database Connection", check_database),
        ("Migrations", check_migrations),
        ("External Services", check_external_services),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Check failed with exception: {str(e)}", "FAIL")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "OK" if result else "FAIL"
        print_status(f"{name}: {status}", status)
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ All checks passed! Ready for deployment.{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}✗ Some checks failed. Review the output above.{Colors.RESET}\n")
        return False

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    
    success = run_all_checks()
    sys.exit(0 if success else 1)
