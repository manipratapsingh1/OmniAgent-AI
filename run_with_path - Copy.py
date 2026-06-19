import sys, runpy, os
# Add backend app path so `import app` resolves
base = os.path.dirname(__file__)
backend_app = os.path.join(base, 'omniagent-ai', 'backend')
sys.path.insert(0, backend_app)
# Provide minimal env defaults so get_settings() can initialize in dev
import os
os.environ.setdefault('SECRET_KEY', 'dev_secret_for_local_32_chars_minimum_1234')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test_local.db')

runpy.run_path(os.path.join(base, 'test_chroma_connection.py'), run_name='__main__')
print('done')
