"""Demo application for MCP tool chaining agent."""

import asyncio
import os
import sys

from agent import PipelineAgent


async def demo_crypto_analysis():
    """Demonstrate cryptocurrency analysis pipeline."""
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-key-here'")
        return

    # Create agent
    print("=" * 70)
    print("MCP TOOL CHAINING AGENT - Cryptocurrency Analysis Pipeline")
    print("=" * 70)
    print()

    agent = PipelineAgent(api_key, enable_notifications=True)

    try:
        # Connect to MCP servers
        await agent.connect_servers()

        # Demo 1: Bitcoin Analysis
        print("\n" + "=" * 70)
        print("DEMO 1: Bitcoin Analysis")
        print("=" * 70)
        result1 = await agent.execute_task(
            "Get current Bitcoin (BTC) data including price, market cap, and "
            "24h change. Create a comprehensive analysis report and save it "
            "to 'bitcoin_analysis.md'"
        )

        if result1["success"]:
            print(f"✓ Completed in {result1['iterations']} iterations")
        else:
            print("✗ Failed to complete task")

        # Demo 2: Top Cryptocurrencies Comparison
        print("\n" + "=" * 70)
        print("DEMO 2: Top Cryptocurrencies Comparison")
        print("=" * 70)
        result2 = await agent.execute_task(
            "Get the top 5 cryptocurrencies by market cap. Compare their "
            "prices, market caps, and 24h price changes. Create a comparison "
            "report and save it to 'top_crypto_comparison.md'"
        )

        if result2["success"]:
            print(f"✓ Completed in {result2['iterations']} iterations")
        else:
            print("✗ Failed to complete task")

        # Demo 3: Trending Cryptocurrencies
        print("\n" + "=" * 70)
        print("DEMO 3: Trending Cryptocurrencies Analysis")
        print("=" * 70)
        result3 = await agent.execute_task(
            "Get currently trending cryptocurrencies. Analyze why they might "
            "be trending and save the analysis to 'trending_crypto.md'"
        )

        if result3["success"]:
            print(f"✓ Completed in {result3['iterations']} iterations")
        else:
            print("✗ Failed to complete task")

        # Demo 4: Market Overview
        print("\n" + "=" * 70)
        print("DEMO 4: Cryptocurrency Market Overview")
        print("=" * 70)
        result4 = await agent.execute_task(
            "Get the global cryptocurrency market summary including total "
            "market cap, 24h volume, and market dominance. Create a market "
            "overview report and save it to 'market_overview.md'"
        )

        if result4["success"]:
            print(f"✓ Completed in {result4['iterations']} iterations")
        else:
            print("✗ Failed to complete task")

        # Summary
        print("\n" + "=" * 70)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 70)
        total_tasks = 4
        successful_tasks = sum([
            result1["success"],
            result2["success"],
            result3["success"],
            result4["success"]
        ])

        print(f"Total tasks: {total_tasks}")
        print(f"Successful: {successful_tasks}")
        print(f"Failed: {total_tasks - successful_tasks}")

        if successful_tasks > 0:
            print("\nGenerated reports in 'output/' directory:")
            print("  - bitcoin_analysis.md")
            print("  - top_crypto_comparison.md")
            print("  - trending_crypto.md")
            print("  - market_overview.md")

        print("\n" + "=" * 70)
        print("✓ All demonstrations completed!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Shutting down...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nDisconnecting from MCP servers...")
        await agent.disconnect_servers()
        agent.close()
        print("✓ Cleanup complete")


async def interactive_mode():
    """Run agent in interactive mode."""
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-key-here'")
        return

    # Create agent
    print("=" * 70)
    print("MCP TOOL CHAINING AGENT - Interactive Mode")
    print("=" * 70)
    print()

    agent = PipelineAgent(api_key, enable_notifications=True)

    try:
        # Connect to MCP servers
        await agent.connect_servers()

        print("Enter your tasks (or 'quit' to exit):")
        print("Example: Analyze Ethereum and save to eth_report.txt")
        print()

        while True:
            try:
                task = input("\nTask: ").strip()

                if not task:
                    continue

                if task.lower() in ['quit', 'exit', 'q']:
                    break

                # Execute task
                result = await agent.execute_task(task)

                if result["success"]:
                    print(f"\n✓ Task completed in {result['iterations']} iterations")
                else:
                    print("\n✗ Task failed")

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break

    finally:
        # Cleanup
        print("\nDisconnecting from MCP servers...")
        await agent.disconnect_servers()
        agent.close()
        print("✓ Cleanup complete")


def print_usage():
    """Print usage information."""
    print("Usage:")
    print("  python main.py demo       - Run demonstration scenarios")
    print("  python main.py interactive - Run in interactive mode")
    print("  python main.py            - Run demonstration scenarios (default)")


async def main():
    """Main entry point."""
    # Parse command line arguments
    mode = "demo"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    if mode == "demo":
        await demo_crypto_analysis()
    elif mode == "interactive":
        await interactive_mode()
    elif mode in ["help", "-h", "--help"]:
        print_usage()
    else:
        print(f"Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
