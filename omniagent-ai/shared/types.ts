// Mirrors backend Pydantic schemas for cross-package typing.
export type Role = "user" | "assistant" | "system" | "tool";
export interface SharedMessage { id: number; role: Role; content: string; created_at: string; }