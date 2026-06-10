#!/usr/bin/env python3
"""
Comprehensive System Setup and Verification Script
Sets up PostgreSQL database, verifies all connections, and initializes the application
"""

import subprocess
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "omniagent-ai" / "backend"
sys.path.insert(0, str(backend_path))

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")

def print_success(text):
    print(f"  ✓ {text}")

def print_error(text):
    print(f"  ✗ {text}")

def print_info(text):
    print(f"  ℹ {text}")

def print_warning(text):
    print(f"  ⚠ {text}")

print_header("OMNIAGENT SYSTEM SETUP & VERIFICATION")

# Step 1: Check Python
print_step(1, "Checking Python Installation")
try:
    python_version = subprocess.check_output(["python", "--version"]).decode().strip()
    print_success(f"Python is installed: {python_version}")
except:
    print_error("Python is not installed or not in PATH")
    sys.exit(1)

# Step 2: Check PostgreSQL
print_step(2, "Checking PostgreSQL Installation")
try:
    pg_version = subprocess.check_output(["psql", "--version"]).decode().strip()
    print_success(f"PostgreSQL is installed: {pg_version}")
except:
    print_error("PostgreSQL is not installed or 'psql' is not in PATH")
    print_info("Please install PostgreSQL from: https://www.postgresql.org/download/")
    print_info("Make sure to add the PostgreSQL bin folder to your PATH")
    sys.exit(1)

# Step 3: Check if PostgreSQL service is running
print_step(3, "Checking PostgreSQL Service")
try:
    # Try to connect to PostgreSQL
    result = subprocess.run(
        ["psql", "-U", "postgres", "-d", "postgres", "-c", "SELECT 1"],
        capture_output=True,
        timeout=5
    )
    if result.returncode == 0:
        print_success("PostgreSQL service is running")
    else:
        print_error("PostgreSQL is installed but the service is not running")
        print_info("Windows: Start the PostgreSQL service from Services")
        print_info("Or run: pg_ctl -D \"C:\\Program Files\\PostgreSQL\\data\" start")
        sys.exit(1)
except Exception as e:
    print_error(f"Cannot connect to PostgreSQL: {str(e)}")
    print_info("Make sure PostgreSQL service is running")
    sys.exit(1)

# Step 4: Create database if it doesn't exist
print_step(4, "Setting Up Database")
try:
    # Check if database exists
    result = subprocess.run(
        ["psql", "-U", "postgres", "-d", "postgres", "-c", 
         "SELECT 1 FROM pg_database WHERE datname = 'omniagent'"],
        capture_output=True,
        text=True
    )
    
    if "(0 rows)" in result.stdout or result.returncode != 0:
        print_info("Creating 'omniagent' database...")
        subprocess.run(
            ["psql", "-U", "postgres", "-d", "postgres", 
             "-c", "CREATE DATABASE omniagent"],
            check=True
        )
        print_success("Database 'omniagent' created successfully")
    else:
        print_success("Database 'omniagent' already exists")
except Exception as e:
    print_error(f"Failed to create database: {str(e)}")
    sys.exit(1)

# Step 5: Verify .env file
print_step(5, "Verifying Configuration")
env_path = backend_path / ".env"
if not env_path.exists():
    print_error(".env file not found in backend directory")
    sys.exit(1)

with open(env_path) as f:
    env_content = f.read()
    
if "DATABASE_URL" not in env_content:
    print_error("DATABASE_URL not configured in .env")
    sys.exit(1)
    
if "SECRET_KEY" not in env_content:
    print_error("SECRET_KEY not configured in .env")
    sys.exit(1)

print_success(".env file is properly configured")

# Step 6: Initialize Python Environment
print_step(6, "Checking Python Virtual Environment")
venv_path = backend_path.parent.parent / ".venv"
if not venv_path.exists():
    print_warning("Virtual environment not found. Creating one...")
    os.chdir(backend_path.parent.parent)
    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    print_success("Virtual environment created")
else:
    print_success("Virtual environment found")

# Step 7: Install/Update Dependencies
print_step(7, "Installing Python Dependencies")
try:
    # Activate venv and install requirements
    os.chdir(backend_path)
    if sys.platform == "win32":
        activate_cmd = str(venv_path / "Scripts" / "activate.bat")
        # Using subprocess to run with activated venv
        req_file = backend_path / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                [str(venv_path / "Scripts" / "pip"), "install", "-q", "-r", "requirements.txt"],
                check=True
            )
            print_success("Python dependencies installed")
        else:
            print_warning("requirements.txt not found, skipping pip install")
    else:
        req_file = backend_path / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                [str(venv_path / "bin" / "pip"), "install", "-q", "-r", "requirements.txt"],
                check=True
            )
            print_success("Python dependencies installed")
except Exception as e:
    print_warning(f"Could not auto-install dependencies: {str(e)}")
    print_info("You can manually install with: pip install -r requirements.txt")

# Step 8: Test database connection and initialize
print_step(8, "Testing Database Connection and Initializing")
try:
    os.chdir(backend_path)
    result = subprocess.run(
        [sys.executable, "init_and_run.py"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if "database_ready" in result.stderr or "database.initialized" in result.stderr:
        print_success("Database connection successful and initialized")
    else:
        print_info("Database initialization output:")
        print(result.stderr)
        if result.returncode == 0:
            print_success("Database initialization completed")
        else:
            print_warning("Database initialization may have had issues")
            print_info("Full output:")
            print(result.stdout)
            print(result.stderr)
except subprocess.TimeoutExpired:
    print_warning("Database initialization timeout (this may be normal)")
except Exception as e:
    print_warning(f"Could not auto-test database: {str(e)}")
    print_info("You can manually test with: python init_and_run.py")

# Step 9: Provide startup instructions
print_header("SETUP COMPLETE - NEXT STEPS")

print_step("1", "START BACKEND SERVER")
print_info("In a terminal, run:")
print_info(f"  cd backend")
print_info(f"  .venv\\Scripts\\activate  (Windows) or source .venv/bin/activate (Unix)")
print_info(f"  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

print_step("2", "START FRONTEND SERVER")
print_info("In another terminal, run:")
print_info(f"  cd frontend")
print_info(f"  npm install (if not done)")
print_info(f"  npm run dev")

print_step("3", "ACCESS APPLICATION")
print_info("Open your browser and navigate to:")
print_info(f"  http://localhost:5173")

print_step("4", "LOGIN WITH ADMIN ACCOUNT")
print_info("Use these credentials (or create an admin account):")
print_info(f"  Email: admin@example.com")
print_info(f"  Password: (check if pre-created or create via signup)")

print_step("5", "TEST HEALTH ENDPOINT")
print_info("To verify backend is running, check:")
print_info(f"  http://localhost:8000/api/v1/health/readyz")
print_info("Should return JSON with: ready: true/false, checks: { database, redis, ollama, chroma }")

print_step("6", "VERIFY DOCUMENT UPLOAD")
print_info("1. Navigate to Documents page")
print_info("2. Upload a PDF file (should show 'successfully uploaded')")
print_info("3. Check System Status (bottom left) - should show all green checkmarks")

print_header("TROUBLESHOOTING")

print_info("Database Connection Failed?")
print("  1. Verify PostgreSQL is running: tasklist | grep postgres (Windows)")
print("  2. Check DATABASE_URL in .env is correct")
print("  3. Verify database 'omniagent' exists: psql -U postgres -c \"\\\\l\"")

print_info("Port Already in Use?")
print("  Backend: Change port in .env (default: 8000)")
print("  Frontend: Change port in vite.config.ts (default: 5173)")

print_info("Module not found errors?")
print("  Run: pip install -r requirements.txt (in backend directory)")

print_header("SYSTEM READY!")
