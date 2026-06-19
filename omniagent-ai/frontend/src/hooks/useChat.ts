import { useStore } from "../store";
import type { Message } from "../api/types";

type ChatMode = "fast" | "knowledge";

let currentController: AbortController | null = null;

export function useChat() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { activeId, setActive, setTrace, setSources } = useStore();

  async function send(
    text: string,
    model?: string,
    useRag = true,
    systemPrompt?: string,
    mode: ChatMode = "fast",
    images: string[] = []
  ) {
    return await streamChat({ message: text, model, useRag, systemPrompt, mode, images });
  }

  function stop() {
    if (currentController) {
      currentController.abort();
      currentController = null;
    }
  }

  async function streamChat({
    message,
    model,
    useRag,
    systemPrompt,
    mode = "fast",
    images = [],
  }: {
    message: string;
    model?: string;
    useRag?: boolean;
    systemPrompt?: string;
    mode?: ChatMode;
    images?: string[];
  }) {
    const localUser: Message = {
      id: Date.now(),
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };

    const placeholderId = Date.now() + 1;
    const assistantPlaceholder: Message = {
      id: placeholderId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };

    setSources([]);

    useStore.setState((state) => ({
      messages: [...state.messages, localUser, assistantPlaceholder],
    }));

    try {
      currentController = new AbortController();
      const token = localStorage.getItem("token");
      const endpoint =
        mode === "knowledge"
          ? "/api/v1/chat/knowledge-assistant/stream"
          : "/api/v1/chat/stream";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { "Authorization": `Bearer ${token}` }),
        },
        body: JSON.stringify({
          conversation_id: activeId,
          message,
          model: model || "phi3:mini",
          use_rag: useRag ?? true,
          system_prompt: systemPrompt,
          images,
          temperature: 0.7,
          top_p: 0.9,
          top_k: 40,
        }),
        signal: currentController.signal,
      });

      if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => response.statusText);
        // Update the placeholder with error instead of creating a new message
        useStore.setState((state) => ({
          messages: state.messages.map((item) =>
            item.id === placeholderId
              ? { ...item, content: `Sorry, I couldn't process your request (Error: ${errorText}). Please try again.` }
              : item,
          ),
        }));
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";

      let readResult = await reader.read();
      while (!readResult.done) {
        const value = readResult.value;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          try {
            const event = JSON.parse(trimmed);
            if (event.type === "meta" && event.conversation_id) {
              setActive(event.conversation_id);
            } else if (event.type === "token" && event.content) {
              assistantContent += event.content;
            } else if (event.type === "chunk" && event.data?.answer_chunk) {
              assistantContent += event.data.answer_chunk;
            } else if (event.type === "metadata" && event.data?.sources) {
              setSources(event.data.sources);
            } else if (event.type === "done") {
              if (event.conversation_id) {
                setActive(event.conversation_id);
              }
              if (event.sources) {
                setSources(event.sources);
              }
            } else if (event.type === "error" && event.data?.message) {
              assistantContent += `\nError: ${event.data.message}`;
            }

            if (assistantContent) {
              useStore.setState((state) => ({
                messages: state.messages.map((item) =>
                  item.id === placeholderId
                    ? { ...item, content: assistantContent }
                    : item,
                ),
              }));
            }
          } catch (error) {
            console.warn("Failed to parse stream event", error, line);
          }
        }

        readResult = await reader.read();
      }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      const errName = typeof error === "object" && error !== null && "name" in error ? (error as { name?: unknown }).name : undefined;
      if (errName === "AbortError") {
        useStore.setState((state) => ({
          messages: state.messages.map((item) =>
            item.id === placeholderId
              ? { ...item, content: "Generation stopped." }
              : item,
          ),
        }));
        return;
      }

      console.error("Streaming chat error:", error);
      // Update the placeholder message with error instead of creating a new one
      useStore.setState((state) => ({
        messages: state.messages.map((item) =>
          item.id === placeholderId
            ? { ...item, content: "I encountered an error. Please try again." }
            : item,
        ),
      }));
    } finally {
      currentController = null;
    }
  }

  return { send, stop, streamChat };
}