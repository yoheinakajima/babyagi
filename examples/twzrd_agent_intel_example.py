#!/usr/bin/env python3
"""
TWZRD Agent Intel integration for BabyAGI.

Demonstrates how to add trust verification to BabyAGI's task execution loop
using the TWZRD Agent Intel MCP server. Before an agent processes a task that
involves payments or sensitive actions, its trust score is checked.

The TWZRD Agent Intel server provides:
  - score_agent(wallet)       — 0-100 trust score + behavioral risk flags (free)
  - preflight_check(wallet)   — PASS/FAIL gate for x402 payment flows (free)
  - get_trust_receipt(wallet) — signed on-chain trust receipt (HTTP 402 paid)

MCP endpoint: https://intel.twzrd.xyz/mcp  (streamable-http, no auth required)

Install:
    pip install mcp openai

Usage:
    python examples/twzrd_agent_intel_example.py
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


TWZRD_MCP_URL = "https://intel.twzrd.xyz/mcp"


async def check_trust(wallet: str) -> tuple[int, bool]:
    """
    Check agent trust score and preflight status.

    Returns:
        (score, passed): score is 0-100, passed is True if preflight PASS
    """
    async with streamablehttp_client(TWZRD_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            score_result = await session.call_tool("score_agent", {"wallet": wallet})
            preflight_result = await session.call_tool("preflight_check", {"wallet": wallet})

    score_text = score_result.content[0].text if score_result.content else "{}"
    preflight_text = preflight_result.content[0].text if preflight_result.content else ""

    # Parse score (returned as JSON string with "score" key)
    import json
    try:
        score_data = json.loads(score_text)
        score = score_data.get("score", 0)
    except (json.JSONDecodeError, AttributeError):
        score = 0

    passed = "PASS" in preflight_text.upper()
    return score, passed


class TrustAwareBabyAGI:
    """
    A BabyAGI-style task loop with TWZRD trust verification.

    Agents must pass a trust check before executing payment-sensitive tasks.
    Tasks with `requires_payment: True` are gated on trust score >= threshold.
    """

    TRUST_THRESHOLD = 60  # Minimum trust score to execute payment tasks

    def __init__(self, agent_wallet: str):
        self.agent_wallet = agent_wallet
        self.task_list = []
        self._trust_score = None
        self._preflight_passed = None

    async def verify_trust(self) -> bool:
        """Verify the agent's trust score. Cached after first call."""
        if self._trust_score is None:
            print(f"  Checking TWZRD trust for {self.agent_wallet[:8]}...")
            self._trust_score, self._preflight_passed = await check_trust(self.agent_wallet)
            print(f"  Trust score: {self._trust_score} | Preflight: {'PASS' if self._preflight_passed else 'FAIL'}")
        return self._preflight_passed and self._trust_score >= self.TRUST_THRESHOLD

    def add_task(self, task_name: str, requires_payment: bool = False):
        self.task_list.append({
            "task_name": task_name,
            "requires_payment": requires_payment,
        })

    async def run(self):
        print(f"\nStarting TrustAwareBabyAGI for agent: {self.agent_wallet[:8]}...")
        while self.task_list:
            task = self.task_list.pop(0)
            task_name = task["task_name"]
            requires_payment = task["requires_payment"]

            print(f"\n--- Task: {task_name} ---")

            if requires_payment:
                trusted = await self.verify_trust()
                if not trusted:
                    print(f"  BLOCKED: Agent trust score {self._trust_score} "
                          f"< threshold {self.TRUST_THRESHOLD} or preflight FAIL. "
                          "Skipping payment task.")
                    continue
                print(f"  AUTHORIZED: Trust score {self._trust_score} >= {self.TRUST_THRESHOLD}")

            # Execute task (plug in your LLM execution logic here)
            print(f"  Executing: {task_name}")
            await self._execute_task(task_name)

        print("\nAll tasks complete.")

    async def _execute_task(self, task_name: str):
        """Placeholder for actual task execution (connect your LLM here)."""
        await asyncio.sleep(0.1)  # Simulate work
        print(f"  Done: {task_name}")


async def main():
    # Example: BabyAGI agent that needs to make x402 payments
    agent_wallet = "4LkEFjHsF2ubC8K4oF2r3rCFqPZQVGBjL9mV6xkNPZdf"

    agi = TrustAwareBabyAGI(agent_wallet=agent_wallet)

    # Mix of free and payment-gated tasks
    agi.add_task("Search for Solana DeFi news", requires_payment=False)
    agi.add_task("Fetch premium market data via x402 API", requires_payment=True)
    agi.add_task("Summarize findings", requires_payment=False)
    agi.add_task("Purchase detailed analytics report", requires_payment=True)

    await agi.run()


if __name__ == "__main__":
    asyncio.run(main())
