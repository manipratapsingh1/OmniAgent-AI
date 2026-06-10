const startListening = async (onPartial: (t: string) => void) => {
  const win = window as unknown as {
    webkitSpeechRecognition?: unknown;
    SpeechRecognition?: unknown;
    _speechRec?: unknown;
  };

  const ctor = (win.webkitSpeechRecognition ?? win.SpeechRecognition) as
    | (new () => {
        interimResults: boolean;
        continuous: boolean;
        onresult: (e: unknown) => void;
        start: () => void;
        stop: () => void;
      })
    | undefined;

  if (!ctor) return null;

  const r = new ctor();
  r.interimResults = true;
  r.continuous = false;
  r.onresult = (e: unknown) => {
    try {
      const evt = e as { results?: ArrayLike<unknown> };
      const results = Array.from(evt.results || []);
      const text = results
        .map((res) => {
          const first = (res as unknown as ArrayLike<unknown>)[0] as unknown as {
            transcript?: string;
          } | undefined;
          return first?.transcript ?? "";
        })
        .join("\n");
      onPartial(text);
    } catch {
      /* ignore parse errors */
    }
  };
  r.start();
  win._speechRec = r;
  return "";
};

const stopListening = () => {
  const win = window as unknown as { _speechRec?: { stop: () => void } | null };
  const r = win._speechRec;
  if (r) {
    r.stop();
    win._speechRec = null;
  }
};

const speak = (text: string) => {
  if (!window.speechSynthesis) return;
  
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();
  
  const utterance = new SpeechSynthesisUtterance(text);
  
  // Try to find a natural-sounding voice
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => 
    v.name.includes("Google") || v.name.includes("Natural") || v.lang === "en-US"
  );
  
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }
  
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  
  window.speechSynthesis.speak(utterance);
};

export default { startListening, stopListening, speak };
