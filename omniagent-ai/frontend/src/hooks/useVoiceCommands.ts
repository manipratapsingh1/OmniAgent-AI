import { useNavigate } from "react-router-dom";
import { parseVoiceCommand, routeForVoiceCommand } from "../utils/voiceCommands";

export function useVoiceCommands() {
  const navigate = useNavigate();

  function handleTranscript(text: string, onChatInput?: (text: string) => void): boolean {
    const command = parseVoiceCommand(text);
    const route = routeForVoiceCommand(command);

    if (route) {
      navigate(route);
      return true;
    }

    onChatInput?.(text);
    return false;
  }

  return { handleTranscript };
}
