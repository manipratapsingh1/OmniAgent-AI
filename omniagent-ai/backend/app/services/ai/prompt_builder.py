from typing import List


class PromptBuilder:
    @staticmethod
    def build_system_prompt(role: str = "assistant") -> str:
        return f"You are an AI assistant acting as a {role}. Respond helpfully."

    @staticmethod
    def build_chat_prompt(history: List[str], user_message: str) -> str:
        ctx = "\n".join(history[-10:])
        return f"{ctx}\nUser: {user_message}\nAssistant:"
