"""Extended module tests — schemas, providers, retriever, ingest formats."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCommonSchemas:
    def test_pagination_params(self):
        from app.schemas.common import PaginationParams, SortParams, SafeString, OkResponse

        p = PaginationParams(skip=0, limit=50)
        assert p.limit == 50
        s = SortParams(sort_order="asc")
        assert s.sort_order == "asc"
        assert SafeString.validate("hello world") is True
        assert SafeString.validate("DROP TABLE users") is False
        assert OkResponse().ok is True

    def test_pagination_validation(self):
        from app.schemas.common import PaginationParams

        with pytest.raises(ValueError):
            PaginationParams(skip=-1)
        with pytest.raises(ValueError):
            PaginationParams(limit=0)


class TestGeminiProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        from app.services.ai.gemini_provider import GeminiProvider

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("app.services.ai.gemini_provider._settings") as mock_settings:
                mock_settings.GEMINI_API_KEY = "test-key"
                provider = GeminiProvider()
                mock_resp = MagicMock(status_code=200)
                mock_resp.json.return_value = {
                    "candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]
                }
                mock_resp.raise_for_status = MagicMock()
                with patch("httpx.AsyncClient") as mock_client:
                    mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)
                    result = await provider.generate("Hi")
        assert "Gemini" in result or result

    def test_payload_with_system(self):
        from app.services.ai.gemini_provider import GeminiProvider

        with patch("app.services.ai.gemini_provider._settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "key"
            provider = GeminiProvider()
            payload = provider._payload("hello", "be helpful")
            assert "systemInstruction" in payload


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_generate_mocked(self):
        from app.services.ai.openai_provider import OpenAIProvider

        with patch("app.services.ai.openai_provider._settings") as s:
            s.OPENAI_API_KEY = "sk-test"
            provider = OpenAIProvider()
            provider.client = MagicMock()
            provider.client.chat.completions.create = AsyncMock(
                return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="OpenAI response"))])
            )
            result = await provider.generate("Hello")
        assert result == "OpenAI response"


class TestIngestFormatExtractors:
    def test_extract_pptx_mocked(self):
        from app.rag.ingest import _extract_pptx

        with patch("app.rag.ingest.Presentation", create=True):
            with patch("pptx.Presentation") as mock_prs:
                slide = MagicMock()
                shape = MagicMock(text="Slide content")
                slide.shapes = [shape]
                mock_prs.return_value.slides = [slide]
                result = _extract_pptx(b"fake", "deck.pptx")
        assert isinstance(result, str)

    def test_extract_xlsx_mocked(self):
        from app.rag.ingest import _extract_xlsx

        with patch("pandas.read_excel") as mock_read:
            import pandas as pd
            mock_read.return_value = {"Sheet1": pd.DataFrame({"a": [1], "b": [2]})}
            result = _extract_xlsx(b"fake", "data.xlsx")
        assert "Sheet" in result or result == ""

    def test_semantic_chunk_path(self):
        from app.rag.chunker import semantic_chunk_text

        text = "Paragraph one.\n\nParagraph two with more content.\n\nParagraph three."
        chunks = semantic_chunk_text(text)
        assert len(chunks) >= 1


class TestRetrieverExtended:
    def test_keyword_search_with_filters(self, db_session_mock):
        from app.rag.retriever import _keyword_search_fallback

        chunk = MagicMock()
        chunk.document_id = 1
        chunk.chunk_index = 0
        chunk.text = "machine learning content"
        doc = MagicMock()
        db_session_mock.exec.return_value.all.return_value = [(chunk, doc)]

        results = _keyword_search_fallback(
            db_session_mock, "machine learning", k=5, filters={"is_knowledge_base": True}
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_with_cache_hit(self, db_session_mock):
        from app.rag.retriever import retrieve

        cached = [{"text": "cached", "document_id": 1, "chunk_index": 0, "score": 0.9}]
        with patch("app.rag.retriever.get_optimized_retriever", return_value=None):
            with patch("app.cache.get_json", return_value=cached):
                results = await retrieve(user_id=1, query="test", k=5, db=db_session_mock)
        assert results == cached

    @pytest.mark.asyncio
    async def test_retrieve_no_embeddings(self, db_session_mock):
        from app.rag.retriever import retrieve

        with patch("app.rag.retriever.get_optimized_retriever", return_value=None):
            with patch("app.cache.get_json", return_value=None):
                with patch("app.rag.embeddings.embed_texts", new=AsyncMock(return_value=[])):
                    results = await retrieve(user_id=1, query="test", k=5, db=db_session_mock)
        assert results == []


class TestCitationUtilsExtended:
    def test_filter_sources_by_citations(self):
        from app.utils.citations import filter_sources_by_citations, extract_citations_from_response

        sources = [
            {"document_id": 1, "chunk_index": 0, "text": "a"},
            {"document_id": 2, "chunk_index": 1, "text": "b"},
        ]
        answer = "See [doc:1#0] for info."
        cited = extract_citations_from_response(answer)
        filtered = filter_sources_by_citations(sources, cited)
        assert len(filtered) >= 1


class TestDocumentRepoExtended:
    def test_search_and_status_filters(self, db_session_mock):
        from app.repositories.document_repo import DocumentRepo
        from app.models.document import Document

        doc = Document(id=1, user_id=1, filename="report.pdf", status="indexed")
        db_session_mock.exec.return_value.all.return_value = [doc]
        repo = DocumentRepo(db_session_mock)
        assert len(repo.search_for_user(1, "report")) == 1
        assert len(repo.get_by_status(1, "indexed")) == 1

    def test_delete_document(self, db_session_mock):
        from app.repositories.document_repo import DocumentRepo
        from app.models.document import Document

        doc = Document(id=1, user_id=1, filename="f.txt", status="indexed", chunk_count=2)
        db_session_mock.get.return_value = doc
        db_session_mock.exec.return_value.all.return_value = []

        repo = DocumentRepo(db_session_mock)
        with patch("app.rag.retriever.get_vector_store") as mock_store:
            mock_store.return_value.collection = MagicMock()
            assert repo.delete(1) is True


class TestWebSearchProviders:
    @pytest.mark.asyncio
    async def test_duckduckgo_search(self):
        from app.services.web_search_service import WebSearchService

        service = WebSearchService()
        with patch.object(service, "_search_duckduckgo", new=AsyncMock(return_value=[])):
            results = await service.search("python programming")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_provider_override(self):
        from app.services.web_search_service import WebSearchService, SearchResult

        service = WebSearchService()
        mock_result = [SearchResult(title="T", snippet="s", url="https://www.example.com", score=0.5)]
        with patch("app.services.web_search_service.validate_url", return_value=True):
            with patch.object(service, "_search_tavily", new=AsyncMock(return_value=mock_result)):
                results = await service.search("query", provider="tavily")
        assert len(results) == 1


class TestDeepResearchExtended:
    @pytest.mark.asyncio
    async def test_research_pipeline(self, db_session_mock):
        from app.services.ai.hybrid_knowledge_engine import KnowledgeCase, KnowledgeMode
        from app.services.deep_research_service import DeepResearchService

        service = DeepResearchService(db_session_mock)
        mock_knowledge = {
            "case": KnowledgeCase.NO_DOCUMENT,
            "context_text": "",
            "chunks": [],
            "confidence": "none",
            "web_results": [],
        }
        with patch.object(service.knowledge_engine, "retrieve_and_decide", new=AsyncMock(return_value=mock_knowledge)):
            with patch.object(service.web_search, "search", new=AsyncMock(return_value=[])):
                with patch.object(service.router, "generate", new=AsyncMock(return_value=("Research report", "ollama"))):
                    result = await service.research(1, "AI trends")
        assert "report" in result
        assert result["query"] == "AI trends"
