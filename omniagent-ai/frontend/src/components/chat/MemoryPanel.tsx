import { useStore } from "../../store";

export default function MemoryPanel() {
  const { activeId, messages } = useStore();
  const assistantMessages = messages.filter((message) => message.role === "assistant");
  const lastAssistant = assistantMessages[assistantMessages.length - 1]?.content;

  return (
    <div className="p-3 border-t border-zinc-800">
      <h3 className="font-semibold mb-2 text-sm uppercase tracking-wider text-zinc-400">Memory</h3>
      <div className="text-xs text-zinc-400 space-y-2">
        <div>
          <span className="font-medium text-zinc-200">Conversation:</span> {activeId ? `#${activeId}` : "New"}
        </div>
        <div>
          <span className="font-medium text-zinc-200">Messages:</span> {messages.length}
        </div>
        {lastAssistant ? (
          <div className="text-zinc-500">
            <span className="font-medium text-zinc-200">Last reply:</span> {lastAssistant.slice(0, 80)}{lastAssistant.length > 80 ? "…" : ""}
          </div>
        ) : (
          <div className="text-zinc-500">Memory previews appear after your first assistant response.</div>
        )}
      </div>
    </div>
  );
}