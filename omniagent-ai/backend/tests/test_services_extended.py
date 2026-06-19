"""Extended service layer tests for coverage."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auth_service import AuthService
from app.services.background_job_service import BackgroundJobService
from app.services.api_key_service import APIKeyService
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.task_service import TaskService
from app.services.search_service import SearchService
from app.services.audit_service import AuditService
from app.schemas.auth import SignupRequest, LoginRequest, PasswordChangeRequest
from app.models.user import User
from app.models.background_job import BackgroundJob
from app.models.api_key import APIKey
from app.models.task import Task
from app.core.security import hash_password


class TestAuthService:
    def test_signup_and_login_flow(self, db_session_mock):
        user_store = {}

        def by_email(email):
            return user_store.get(email)

        def add(user):
            user.id = 1
            user_store[user.email] = user
            return user

        db_session_mock.add = MagicMock()
        db_session_mock.commit = MagicMock()
        db_session_mock.refresh = MagicMock()

        service = AuthService(db_session_mock)
        service.users = MagicMock()
        service.users.by_email = by_email
        service.users.add = add
        service.audit = MagicMock()

        tokens = service.signup(SignupRequest(email="new@example.com", password="securepass123"))
        assert tokens.access_token

        tokens2 = service.login(LoginRequest(email="new@example.com", password="securepass123"))
        assert tokens2.access_token

    def test_login_wrong_password(self, db_session_mock):
        user = User(email="u@example.com", hashed_password=hash_password("correct123"))
        service = AuthService(db_session_mock)
        service.users = MagicMock()
        service.users.by_email.return_value = user
        service.audit = MagicMock()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            service.login(LoginRequest(email="u@example.com", password="wrongpass123"))
        assert exc.value.status_code == 401

    def test_change_password(self, db_session_mock):
        user = User(id=1, email="u@example.com", hashed_password=hash_password("oldpass123"))
        service = AuthService(db_session_mock)
        service.users = MagicMock()
        service.users.add = MagicMock()

        result = service.change_password(
            user,
            PasswordChangeRequest(current_password="oldpass123", new_password="newpass456789"),
        )
        assert "success" in result["message"]


class TestBackgroundJobService:
    def test_create_and_update_job(self, db_session_mock):
        job = BackgroundJob(id=1, user_id=1, job_type="ingest", status="pending")
        db_session_mock.exec.return_value.first.return_value = job

        service = BackgroundJobService(db_session_mock)
        created = service.create_job(1, "ingest")
        assert created.status == "pending"

        updated = service.update_status(1, "processing", progress=50)
        assert updated.status == "processing"
        assert updated.progress == 50

    def test_cancel_job(self, db_session_mock):
        job = BackgroundJob(id=1, user_id=1, job_type="ingest", status="pending")
        db_session_mock.exec.return_value.first.return_value = job
        service = BackgroundJobService(db_session_mock)
        assert service.cancel_job(1) is True

    def test_get_pending_jobs(self, db_session_mock):
        db_session_mock.exec.return_value.all.return_value = []
        service = BackgroundJobService(db_session_mock)
        assert service.get_pending_jobs("ingest") == []


class TestAPIKeyService:
    def test_create_and_verify_key(self, db_session_mock):
        stored = {}

        def add(obj):
            obj.id = 1
            stored["hash"] = obj.key_hash
            return obj

        db_session_mock.add = add
        db_session_mock.commit = MagicMock()
        db_session_mock.refresh = MagicMock()

        service = APIKeyService(db_session_mock)
        raw_key, api_key = service.create_key(1, "test-key")
        assert len(raw_key) > 20

        key_obj = APIKey(id=1, user_id=1, key_hash=stored["hash"], is_active=True)
        db_session_mock.exec.return_value.first.return_value = key_obj
        valid, obj = service.verify_key(raw_key)
        assert valid is True

    def test_verify_invalid_key(self, db_session_mock):
        db_session_mock.exec.return_value.first.return_value = None
        service = APIKeyService(db_session_mock)
        valid, obj = service.verify_key("invalid-key")
        assert valid is False


class TestKnowledgeService:
    @pytest.mark.asyncio
    async def test_add_relationship(self, db_session_mock):
        service = KnowledgeService(db_session_mock)
        rel = service.add_relationship(1, "doc:1", "discusses", "AI", "document", "topic")
        assert rel.relation == "discusses"
        db_session_mock.commit.assert_called()

    @pytest.mark.asyncio
    async def test_generate_study_material(self, db_session_mock):
        service = KnowledgeService(db_session_mock)
        json_resp = '{"flashcards": [{"q": "Q?", "a": "A"}], "quizzes": [], "actions": ["Review"]}'
        with patch("app.services.knowledge_service.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value=json_resp)
            materials = await service.generate_study_material(1, 1, "AI text content")
        assert len(materials) >= 1

    @pytest.mark.asyncio
    async def test_run_workflow(self, db_session_mock):
        service = KnowledgeService(db_session_mock)
        with patch.object(service, "generate_study_material", new=AsyncMock(return_value=[])):
            with patch("app.services.knowledge_service.ollama") as mock_ollama:
                mock_ollama.generate = AsyncMock(return_value="AI, ML, RAG")
                await service.run_workflow(1, 1, "Sample document text")


class TestMemoryServiceExtended:
    def test_store_and_get_counts(self, db_session_mock):
        from app.models.memory import MemoryEntry

        entry = MemoryEntry(id=1, user_id=1, memory_type="short_term", content="test")
        db_session_mock.refresh = MagicMock()

        service = MemoryService(db_session_mock)
        service.store_short_term(1, "User likes Python")
        db_session_mock.add.assert_called()

    def test_get_learned_facts(self, db_session_mock):
        db_session_mock.exec.return_value.all.return_value = []
        service = MemoryService(db_session_mock)
        facts = service.get_learned_facts(1)
        assert facts == []


class TestTaskService:
    def test_create_and_list_tasks(self, db_session_mock):
        from app.schemas.task import TaskCreate

        service = TaskService(db_session_mock)
        with patch.object(service.repo, "add", side_effect=lambda t: t):
            task = service.create(1, TaskCreate(title="Test", description="Description"))
            assert task.title == "Test"


class TestAuditService:
    def test_log_action(self, db_session_mock):
        service = AuditService(db_session_mock)
        service.log(action="test", entity="user", user_id=1)
        db_session_mock.add.assert_called()
        db_session_mock.commit.assert_called()


class TestSearchService:
    def test_search_conversations(self, db_session_mock):
        service = SearchService(db_session_mock)
        db_session_mock.exec.return_value.all.return_value = []
        results = service.search_conversations(1, "query")
        assert isinstance(results, list)

    def test_conversation_stats(self, db_session_mock):
        service = SearchService(db_session_mock)
        db_session_mock.exec.return_value.all.return_value = []
        stats = service.get_conversation_stats(1)
        assert "total_conversations" in stats
