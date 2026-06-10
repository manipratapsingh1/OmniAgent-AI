import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);
  return (
    <button onClick={() => setDark(!dark)} className="px-2 py-1 rounded bg-zinc-800 text-xs">
      {dark ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}