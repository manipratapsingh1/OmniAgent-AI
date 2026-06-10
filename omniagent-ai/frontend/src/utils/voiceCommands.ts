export type VoiceCommand =
  | "open_dashboard"
  | "upload_document"
  | "search_documents"
  | "create_task"
  | "delete_task"
  | "start_chat"
  | null;

const COMMAND_PATTERNS: { command: VoiceCommand; patterns: RegExp[] }[] = [
  { command: "open_dashboard", patterns: [/open\s+dashboard/i, /go\s+to\s+dashboard/i] },
  { command: "upload_document", patterns: [/upload\s+document/i, /upload\s+a\s+document/i] },
  { command: "search_documents", patterns: [/search\s+documents?/i, /find\s+documents?/i] },
  { command: "create_task", patterns: [/create\s+task/i, /new\s+task/i, /add\s+task/i] },
  { command: "delete_task", patterns: [/delete\s+task/i, /remove\s+task/i] },
  { command: "start_chat", patterns: [/start\s+chat/i, /new\s+chat/i, /open\s+chat/i] },
];

export function parseVoiceCommand(text: string): VoiceCommand {
  const normalized = text.trim();
  for (const { command, patterns } of COMMAND_PATTERNS) {
    if (patterns.some((p) => p.test(normalized))) {
      return command;
    }
  }
  return null;
}

export function routeForVoiceCommand(command: VoiceCommand): string | null {
  switch (command) {
    case "open_dashboard":
      return "/";
    case "upload_document":
      return "/documents";
    case "search_documents":
      return "/search";
    case "create_task":
    case "delete_task":
      return "/tasks";
    case "start_chat":
      return "/chat";
    default:
      return null;
  }
}
