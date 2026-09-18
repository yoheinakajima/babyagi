"""Quickstart: Use Nano Empire AI x402 tools in your agent."""
from nanoempire import NanoEmpireClient
import asyncio

async def main():
    client = NanoEmpireClient()
    await client.claim_faucet("my_agent")
    print("Agent ready with 100 free x402 credits!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
