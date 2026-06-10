/**
 * Utility for exporting chat conversations to JSON or markdown
 */

import type { Message, Conversation } from "../api/types";

export function exportConversationAsJSON(conversation: Conversation & { messages: Message[] }): string {
  return JSON.stringify(conversation, null, 2);
}

export function exportConversationAsMarkdown(conversation: Conversation & { messages: Message[] }): string {
  let md = `# ${conversation.title}\n\n`;
  md += `*Exported on ${new Date().toLocaleString()}*\n\n`;
  
  for (const msg of conversation.messages) {
    if (msg.role === "user") {
      md += `## You\n${msg.content}\n\n`;
    } else {
      md += `## Assistant\n${msg.content}\n\n`;
    }
  }
  
  return md;
}

export function downloadFile(filename: string, content: string, mimeType: string = "text/plain") {
  const element = document.createElement("a");
  element.setAttribute("href", `data:${mimeType};charset=utf-8,${encodeURIComponent(content)}`);
  element.setAttribute("download", filename);
  element.style.display = "none";
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}
