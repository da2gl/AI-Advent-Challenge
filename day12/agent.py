"""Smart agent that chains MCP tools automatically using Gemini AI."""

import asyncio
import json
import os
from typing import Optional, Dict, Any

from core.gemini_client import GeminiApiClient, GeminiModel
from mcp_clients.manager import MCPManager
from notifications.macos import MacOSNotifier


class PipelineAgent:
    """Agent that automatically chains tools to accomplish tasks."""

    SYSTEM_INSTRUCTION = """You are an intelligent agent that can chain multiple tools together to accomplish complex tasks.

Available tools:
- Crypto tools: get_crypto_by_symbol, get_crypto_prices, get_trending_crypto, get_market_summary
- Pipeline tools: summarize, saveToFile, readFile

When asked to analyze cryptocurrency:
1. First, get the crypto data using appropriate crypto tool
2. Then, analyze and create a detailed summary with proper structure
3. Finally, save the analysis to a MARKDOWN file (.md) using saveToFile

IMPORTANT:
- Always save reports as .md files (not .txt)
- Format content with markdown: use ## for headers, **bold**, lists, etc.
- Create well-structured reports with sections

Be concise and efficient in your tool usage."""

    def __init__(self, api_key: str, enable_notifications: bool = True):
        """Initialize the pipeline agent.

        Args:
            api_key: Gemini API key
            enable_notifications: Enable macOS notifications (default: True)
        """
        self.gemini_client = GeminiApiClient(api_key)
        self.mcp_manager = MCPManager()
        self.notifier = MacOSNotifier(enabled=enable_notifications)
        self.conversation_history = []

    async def connect_servers(self):
        """Connect to all required MCP servers."""
        print("Connecting to MCP servers...")

        # Connect to crypto server
        try:
            await self.mcp_manager.connect_client("crypto")
            crypto_tools = self.mcp_manager.get_client("crypto").get_tools_as_dict()
            print(f"✓ Connected to Crypto server ({len(crypto_tools)} tools)")
        except Exception as e:
            print(f"✗ Failed to connect to Crypto server: {e}")

        # Connect to pipeline server
        try:
            await self.mcp_manager.connect_client("pipeline")
            pipeline_tools = self.mcp_manager.get_client("pipeline").get_tools_as_dict()
            print(f"✓ Connected to Pipeline server ({len(pipeline_tools)} tools)")
        except Exception as e:
            print(f"✗ Failed to connect to Pipeline server: {e}")

        print()

    async def disconnect_servers(self):
        """Disconnect from all MCP servers."""
        await self.mcp_manager.disconnect_all()

    def _extract_mcp_result(self, result) -> str:
        """Extract clean data from MCP CallToolResult.

        Args:
            result: MCP CallToolResult object

        Returns:
            Clean JSON string or text content
        """
        try:
            if hasattr(result, 'content'):
                content_list = result.content
                if content_list and len(content_list) > 0:
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        return first_content.text

            if hasattr(result, 'structured_content') and result.structured_content:
                return json.dumps(result.structured_content, indent=2)

            if hasattr(result, 'data') and result.data:
                return json.dumps(result.data, indent=2)

            return str(result)
        except Exception:
            return str(result)

    async def execute_task(self, task: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task using tool chaining.

        Args:
            task: Task description (e.g., "Analyze Bitcoin and save to report.md")
            filename: Optional filename to save results (auto-generated if not provided)

        Returns:
            Dictionary with execution results

        Note:
            Reports are automatically saved as markdown (.md) files with proper formatting
        """
        self.notifier.notify_task_start(f"Pipeline: {task}")

        # Add task to conversation history
        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": task}]
        })

        # Get all available tools
        tools = self.mcp_manager.get_all_tools_for_gemini()

        # Function calling loop
        max_iterations = 10
        iteration = 0
        final_result = None

        print(f"Task: {task}\n")

        while iteration < max_iterations:
            iteration += 1

            # Call Gemini with tools
            response = self.gemini_client.generate_content(
                prompt="",
                model=GeminiModel.GEMINI_2_5_FLASH,
                conversation_history=self.conversation_history,
                system_instruction=self.SYSTEM_INSTRUCTION,
                tools=tools,
                temperature=0.7
            )

            # Check for function calls
            if self.gemini_client.has_function_calls(response):
                function_calls = self.gemini_client.extract_function_calls(response)

                # Add model's response to history
                model_content = response['candidates'][0]['content']
                self.conversation_history.append(model_content)

                # Execute each function call
                for func_call in function_calls:
                    tool_name = func_call['name']
                    tool_args = func_call['args']

                    print(f"→ Calling tool: {tool_name}")
                    print(f"  Arguments: {json.dumps(tool_args, indent=2)}")

                    try:
                        # Call MCP tool
                        result = await self.mcp_manager.call_tool(tool_name, tool_args)
                        result_data = self._extract_mcp_result(result)

                        print("  ✓ Tool executed successfully\n")

                        # Add function response to conversation
                        self.conversation_history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"result": result_data}
                                }
                            }]
                        })

                    except Exception as e:
                        print(f"  ✗ Tool execution failed: {e}\n")

                        # Add error response
                        self.conversation_history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"error": str(e)}
                                }
                            }]
                        })

                # Continue loop
                continue

            else:
                # No function calls - get final text response
                assistant_text = self.gemini_client.extract_text(response)
                self.conversation_history.append({
                    "role": "model",
                    "parts": [{"text": assistant_text}]
                })

                final_result = assistant_text
                break

        # Send completion notification
        if final_result:
            summary = final_result[:100] + "..." if len(final_result) > 100 else final_result
            self.notifier.notify_task_success(f"Pipeline: {task}", summary=summary)
            print("✓ Task completed!\n")
            print(f"Result:\n{final_result}\n")
        else:
            self.notifier.notify_task_error(f"Pipeline: {task}", "No final result")
            print("✗ Task failed - no final result\n")

        return {
            "success": final_result is not None,
            "result": final_result,
            "iterations": iteration
        }

    def close(self):
        """Close the Gemini client."""
        self.gemini_client.close()


async def main():
    """Example usage of PipelineAgent."""
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return

    # Create agent
    agent = PipelineAgent(api_key, enable_notifications=True)

    try:
        # Connect to MCP servers
        await agent.connect_servers()

        # Example task 1: Analyze Bitcoin
        await agent.execute_task(
            "Get current Bitcoin data and create a detailed analysis report. "
            "Save the report to a file named 'bitcoin_analysis.txt'"
        )

        # Example task 2: Compare top cryptocurrencies
        await agent.execute_task(
            "Get the top 5 cryptocurrencies by market cap, analyze their "
            "performance, and save a comparison report to 'top_crypto_comparison.txt'"
        )

    finally:
        # Cleanup
        await agent.disconnect_servers()
        agent.close()


if __name__ == "__main__":
    asyncio.run(main())
