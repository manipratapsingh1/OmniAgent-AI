import { useStore } from "../../store";

export default function AgentTracePanel() {
  const { trace } = useStore();
  return (
    <div className="p-3">
      <h3 className="font-semibold mb-2 text-sm uppercase tracking-wider text-zinc-400">Agent Trace</h3>
      {trace.length === 0 && <p className="text-xs text-zinc-500">No trace yet.</p>}
      <ol className="space-y-2">
        {trace.map((t, i) => (
          <li key={i} className="text-xs bg-zinc-900 rounded p-2 border border-zinc-800">
            <div className="flex justify-between">
              <span className="font-mono text-brand-500">{t.agent}</span>
              <span className="text-zinc-500">{t.latency_ms}ms</span>
            </div>
            <div className="text-zinc-400 mt-1 line-clamp-3">{t.output}</div>
          </li>
        ))}
      </ol>
    </div>
  );
}