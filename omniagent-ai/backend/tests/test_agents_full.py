"""Agent unit tests with mocked LLM."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.state import AgentState, TraceEntry
from app.agents.planner_agent import plan
from app.agents.verifier_agent import verify
from app.agents.critic_agent import critique
from app.agents.summarizer_agent import summarize
from app.agents.router_agent import route
from app.agents.research_agent import research


@pytest.fixture
def base_state():
    return AgentState(
        user_id=1,
        conversation_id=1,
        query="What is machine learning?",
        model="phi3:mini",
        use_rag=False,
        route=["planner"],
    )


class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_plan_adds_trace(self, base_state):
        base_state.route = ["planner"]
        with patch("app.agents.planner_agent.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="Step 1: Research\nStep 2: Answer")
            result = await plan(base_state)
            assert result.plan is not None
            assert len(result.trace) == 1
            assert result.trace[0].agent == "planner"


class TestVerifierAgent:
    @pytest.mark.asyncio
    async def test_verify_with_draft(self, base_state):
        base_state.route = ["verifier"]
        base_state.draft = "Machine learning is a subset of AI."
        with patch("app.agents.verifier_agent.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="Score: 0.85\nVerified.")
            result = await verify(base_state)
            assert len(result.trace) == 1


class TestCriticAgent:
    @pytest.mark.asyncio
    async def test_critique(self, base_state):
        base_state.route = ["critic"]
        base_state.final = "Some final answer to critique."
        with patch("app.agents.critic_agent.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="Polished answer.")
            result = await critique(base_state)
            assert len(result.trace) == 1


class TestSummarizerAgent:
    @pytest.mark.asyncio
    async def test_summarize(self, base_state):
        base_state.route = ["summarizer"]
        base_state.final = "Long detailed answer about machine learning. " * 50
        with patch("app.agents.summarizer_agent.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="ML is a subset of AI.")
            result = await summarize(base_state)
            assert len(result.trace) == 1


class TestRouterAgent:
    @pytest.mark.asyncio
    async def test_route_sets_agents(self, base_state):
        base_state.route = []
        with patch("app.agents.router_agent.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value='["planner", "research", "verifier"]')
            result = await route(base_state)
            assert len(result.route) >= 1


class TestResearchAgent:
    @pytest.mark.asyncio
    async def test_research_without_rag(self, base_state):
        base_state.route = ["research"]
        base_state.use_rag = False
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value=("Research answer about ML.", "ollama"))
        mock_router = MagicMock()
        mock_router.generate = AsyncMock(return_value=("Research answer about ML.", "ollama"))

        with patch("app.agents.research_agent.get_model_router", return_value=mock_router):
            result = await research(base_state)
            assert result.draft == "Research answer about ML."
            assert len(result.trace) == 1

    @pytest.mark.asyncio
    async def test_research_skipped_when_not_in_route(self, base_state):
        base_state.route = ["planner"]
        result = await research(base_state)
        assert result.draft is None


class TestAgentState:
    def test_trace_entry(self):
        entry = TraceEntry(agent="test", input="in", output="out", latency_ms=100)
        assert entry.latency_ms == 100

    def test_default_context(self):
        state = AgentState(user_id=1, conversation_id=1, query="test")
        assert state.context == []
        assert state.use_rag is True
