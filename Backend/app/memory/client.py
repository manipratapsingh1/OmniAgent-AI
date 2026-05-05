# backend/app/memory/client.py
from mem0 import MemoryClient
import os

class OmniMemory:
    def __init__(self):
        self.client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

    def store(self, user_id: str, content: str):
        # Extracts atomic facts like "User prefers dark mode" [2]
        self.client.add([{"role": "user", "content": content}], user_id=user_id)

    def retrieve(self, user_id: str, query: str):
        # Similarity-based fact recall
        return self.client.search(query, user_id=user_id)