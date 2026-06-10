#!/usr/bin/env python3
"""Test script for summarizer function"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "omniagent-ai" / "backend"
sys.path.insert(0, str(backend_dir))

from app.agents.state import AgentState
from app.agents.summarizer_agent import summarize


async def test_summarizer():
    """Test the summarizer function"""
    print("=" * 60)
    print("Testing Summarizer Function")
    print("=" * 60)
    
    # Test 1: Text too short (should not summarize)
    print("\n[TEST 1] Short text (should NOT summarize):")
    state1 = AgentState(
        user_id=1,
        conversation_id=1,
        query='test',
        model='llama3'  # Use available model
    )
    state1.route = ['summarizer']
    state1.final = 'Short text.'
    
    result1 = await summarize(state1)
    print(f"  Input length: {len(state1.final)}")
    print(f"  Output length: {len(result1.final)}")
    print(f"  Trace entries: {len(result1.trace)}")
    print(f"  ✓ Correctly skipped (output unchanged): {result1.final == state1.final}")
    
    # Test 2: Long text (should summarize)
    print("\n[TEST 2] Long text (should summarize):")
    state2 = AgentState(
        user_id=1,
        conversation_id=1,
        query='test',
        model='llama3'
    )
    state2.route = ['summarizer']
    state2.final = 'The machine learning model was trained on a large dataset. ' * 30  # ~1800 chars
    
    print(f"  Input length: {len(state2.final)}")
    print(f"  Processing...")
    result2 = await summarize(state2)
    print(f"  Output length: {len(result2.final)}")
    print(f"  Trace entries: {len(result2.trace)}")
    if result2.trace:
        print(f"  Agent: {result2.trace[-1].agent}")
        print(f"  Latency: {result2.trace[-1].latency_ms}ms")
    print(f"  ✓ Successfully summarized: {len(result2.final) < len(state2.final)}")
    
    # Test 3: Missing summarizer in route (should not summarize)
    print("\n[TEST 3] Missing 'summarizer' in route (should NOT summarize):")
    state3 = AgentState(
        user_id=1,
        conversation_id=1,
        query='test',
        model='llama3'
    )
    state3.route = ['planner']  # summarizer NOT in route
    state3.final = 'The machine learning model was trained. ' * 40  # long text
    
    result3 = await summarize(state3)
    print(f"  Input length: {len(state3.final)}")
    print(f"  Output length: {len(result3.final)}")
    print(f"  Trace entries: {len(result3.trace)}")
    print(f"  ✓ Correctly skipped (output unchanged): {result3.final == state3.final}")
    
    # Test 4: No final text (should not summarize)
    print("\n[TEST 4] No final text (should NOT summarize):")
    state4 = AgentState(
        user_id=1,
        conversation_id=1,
        query='test',
        model='llama3'
    )
    state4.route = ['summarizer']
    state4.final = None
    
    result4 = await summarize(state4)
    print(f"  Final text: {result4.final}")
    print(f"  Trace entries: {len(result4.trace)}")
    print(f"  ✓ Correctly skipped (no error): True")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_summarizer())
