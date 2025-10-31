"""Claude helper utilities."""

from __future__ import annotations

import logging
import json
from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam

from ai_investor.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeAnalyst:
    """Wrap Claude Agent SDK interactions for research tasks."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = "claude-3-5-sonnet-latest"

    def summarize_news(self, ticker: str, articles: list[dict]) -> list[dict]:
        """Ask Claude to cluster recent articles into narrative insights."""

        articles_payload = [
            {
                "headline": article.get("title"),
                "summary": article.get("summary"),
                "sentiment": article.get("sentiment", "neutral"),
                "url": article.get("link"),
            }
            for article in articles
        ]
        if not articles_payload:
            return []
        logger.debug("Requesting Claude summary for %s (%d articles)", ticker, len(articles_payload))
        message = self._client.messages.create(
            model=self._model,
            max_tokens=800,
            system="You are an equity analyst producing concise investment insights.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Summarise the following recent stories about {ticker} into 3 bullet "+
                                "points with sentiment (positive/neutral/negative) and highlight "+
                                "implications for long-term investors. Respond as JSON with fields "+
                                "headline, sentiment, summary, catalyst, risk."
                            ).format(ticker=ticker),
                        },
                        {
                            "type": "json",
                            "json": {"articles": articles_payload},
                        },
                    ],
                }
            ],
        )
        try:
            if not message.content:
                return []
            first_block = message.content[0]
            response_text = getattr(first_block, "text", "")
            parsed = json.loads(response_text)
            insights = parsed if isinstance(parsed, list) else parsed.get("insights", [])
            filtered = []
            for item in insights:
                if not isinstance(item, dict):
                    continue
                filtered.append(
                    {
                        "headline": item.get("headline", ""),
                        "sentiment": item.get("sentiment", "neutral"),
                        "summary": item.get("summary", ""),
                        "catalyst": item.get("catalyst"),
                        "risk": item.get("risk"),
                    }
                )
            return filtered
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse Claude response for %s: %s", ticker, exc)
            return []

    def run_with_tools(
        self,
        system_prompt: str,
        initial_message: str,
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """
        Run Claude in an agentic loop with MCP tools.
        
        Args:
            system_prompt: System instruction for Claude
            initial_message: User's initial message
            tools: List of tool definitions in MCP format
            tool_executor: Object with execute(tool_name, tool_input) method
            max_iterations: Maximum number of tool-calling iterations
            
        Returns:
            Dict with 'content' (final response), 'iterations', and 'tool_calls'
        """
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": initial_message,
            }
        ]
        
        iteration = 0
        all_tool_calls: list[dict[str, Any]] = []
        
        logger.info("Starting Claude agent loop with %d tools available", len(tools))
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug("Agent iteration %d/%d", iteration, max_iterations)
            
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=tools,
                )
                
                # Add assistant response to conversation
                assistant_message: MessageParam = {
                    "role": "assistant",
                    "content": response.content,
                }
                messages.append(assistant_message)
                
                # Check if Claude wants to use tools
                tool_use_blocks = [
                    block for block in response.content 
                    if block.type == "tool_use"
                ]
                
                if not tool_use_blocks:
                    # Claude provided final answer without tools
                    text_blocks = [
                        block.text for block in response.content
                        if hasattr(block, "text")
                    ]
                    final_content = "\n".join(text_blocks)
                    logger.info(
                        "Agent completed in %d iterations with %d tool calls",
                        iteration,
                        len(all_tool_calls),
                    )
                    return {
                        "content": final_content,
                        "iterations": iteration,
                        "tool_calls": all_tool_calls,
                        "stop_reason": response.stop_reason,
                    }
                
                # Execute tools and collect results
                tool_results = []
                for tool_use in tool_use_blocks:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    tool_use_id = tool_use.id
                    
                    logger.info(
                        "Executing tool '%s' with input: %s",
                        tool_name,
                        json.dumps(tool_input, default=str)[:100],
                    )
                    
                    try:
                        result = tool_executor.execute(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result, default=str),
                        })
                        
                        all_tool_calls.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "success": True,
                            "result_preview": str(result)[:200],
                        })
                        
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Tool '%s' failed: %s", tool_name, exc)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps({"error": str(exc)}),
                            "is_error": True,
                        })
                        
                        all_tool_calls.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "success": False,
                            "error": str(exc),
                        })
                
                # Add tool results to conversation
                if tool_results:
                    tool_message: MessageParam = {
                        "role": "user",
                        "content": tool_results,
                    }
                    messages.append(tool_message)
                    
            except Exception as exc:  # noqa: BLE001
                logger.error("Error in agent loop iteration %d: %s", iteration, exc)
                return {
                    "content": f"Agent encountered an error: {exc}",
                    "iterations": iteration,
                    "tool_calls": all_tool_calls,
                    "error": str(exc),
                }
        
        # Max iterations reached
        logger.warning("Agent reached max iterations (%d)", max_iterations)
        return {
            "content": "Agent reached maximum iterations without completing.",
            "iterations": iteration,
            "tool_calls": all_tool_calls,
            "stop_reason": "max_iterations",
        }
