import { useStore } from "../../store";

export default function SourcesPanel() {
  const { sources } = useStore();
  return (
    <div className="p-3 border-t border-zinc-800">
      <h3 className="font-semibold mb-2 text-sm uppercase tracking-wider text-zinc-400">Sources</h3>
      {sources.length === 0 && <p className="text-xs text-zinc-500">No citations.</p>}
      <ul className="space-y-2">
        {sources.map((s, i) => (
          <li key={i} className="text-xs bg-zinc-900 rounded p-2 border border-zinc-800">
            <div className="font-mono text-brand-500">doc:{s.document_id}#{s.chunk_index}</div>
            <div className="text-zinc-400 mt-1 line-clamp-3">{s.snippet}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}