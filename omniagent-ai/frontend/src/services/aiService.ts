const apiBase = '/api/v1/assistant';

interface ChatPayload {
  message?: string;
  prompt?: string;
  stream?: boolean;
  provider?: string;
}

interface ChatChunk {
  type: 'chunk' | 'complete';
  data: {
    text: string;
  };
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

const chat = async (payload: ChatPayload, signal?: AbortSignal) => {
  const res = await fetch(apiBase + '/chat', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

const chatStream = async (
  payload: ChatPayload,
  onChunk: (chunk: ChatChunk) => void,
  signal?: AbortSignal
): Promise<string> => {
  const res = await fetch(apiBase + '/chat', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ ...payload, stream: true }),
    signal,
  });

  if (!res.ok) throw new Error(await res.text());
  if (!res.body) throw new Error('Stream response body is missing');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullResponse = '';
  let buffer = '';

  try {
    let readResult = await reader.read();
    while (!readResult.done) {
      const value = readResult.value;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();
          if (jsonStr) {
            const chunk: ChatChunk = JSON.parse(jsonStr);
            onChunk(chunk);
            fullResponse += chunk.data.text;
          }
        }
      }

      readResult = await reader.read();
    }
  } finally {
    reader.releaseLock();
  }

  return fullResponse;
};

export default { chat, chatStream };
