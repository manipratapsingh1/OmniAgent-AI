"""Export service for conversations and documents."""

from typing import List, Dict, Any, Optional
import structlog
import json
from io import BytesIO
from datetime import datetime

log = structlog.get_logger("export_service")


class ExportService:
    """Export conversations and data in multiple formats."""
    
    @staticmethod
    def export_conversation_to_markdown(
        messages: List[Dict[str, Any]],
        title: str = "Conversation Export"
    ) -> str:
        """Export conversation as Markdown."""
        try:
            md_content = f"# {title}\n\n"
            md_content += f"**Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += "---\n\n"
            
            for msg in messages:
                role = "**User**" if msg.get("role") == "user" else "**Assistant**"
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                md_content += f"{role}\n\n{content}\n\n"
                if msg.get("sources"):
                    md_content += "**Sources:**\n"
                    for source in msg["sources"]:
                        md_content += f"- {source.get('filename', 'Unknown')} (Chunk {source.get('chunk_index', 'N/A')})\n"
                    md_content += "\n"
                md_content += "---\n\n"
            
            log.info("export.markdown_created", messages_count=len(messages))
            return md_content
        except Exception as e:
            log.error("export.markdown_failed", error=str(e))
            raise
    
    @staticmethod
    def export_conversation_to_json(
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export conversation as JSON."""
        try:
            export_data = {
                "exported_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "messages": messages,
            }
            
            json_str = json.dumps(export_data, indent=2, default=str)
            log.info("export.json_created", messages_count=len(messages))
            return json_str
        except Exception as e:
            log.error("export.json_failed", error=str(e))
            raise
    
    @staticmethod
    def export_conversation_to_csv(
        messages: List[Dict[str, Any]]
    ) -> str:
        """Export conversation as CSV."""
        try:
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Timestamp", "Role", "Content", "Sources"])
            
            # Write messages
            for msg in messages:
                sources = "; ".join([
                    f"{s.get('filename', 'Unknown')}"
                    for s in msg.get("sources", [])
                ]) or "None"
                
                writer.writerow([
                    msg.get("timestamp", ""),
                    msg.get("role", ""),
                    msg.get("content", "").replace("\n", " "),
                    sources,
                ])
            
            csv_str = output.getvalue()
            log.info("export.csv_created", messages_count=len(messages))
            return csv_str
        except Exception as e:
            log.error("export.csv_failed", error=str(e))
            raise
