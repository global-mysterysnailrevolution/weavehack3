"""RLM (Recursive Language Model) core implementation for VLA tasks.

Based on: Recursive Language Models (arXiv:2512.24601)
Key concepts:
- Treat long context as external environment
- Programmatic examination and decomposition
- Recursive self-calling over context snippets
"""

from __future__ import annotations

import os
from typing import Any
from dataclasses import dataclass

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.openai_client import get_openai_client


@dataclass
class ContextSnippet:
    """A snippet of context that can be examined programmatically."""
    content: str
    start_idx: int
    end_idx: int
    metadata: dict[str, Any] | None = None


@dataclass
class ExaminationResult:
    """Result of programmatically examining context."""
    relevant: bool
    summary: str
    key_findings: list[str]
    suggested_actions: list[str]
    confidence: float  # 0.0 to 1.0


@weave.op()
def examine_context_snippet(
    snippet: ContextSnippet,
    query: str,
    goal: str,
) -> ExaminationResult:
    """Programmatically examine a context snippet to determine relevance and extract insights.
    
    This is the core RLM operation: treating context as external environment
    and examining it programmatically rather than loading it all into context.
    """
    client = get_openai_client()
    
    prompt = f"""You are examining a snippet of context from a long-running agent task.

Goal: {goal}
Query: {query}

Context Snippet (indices {snippet.start_idx}-{snippet.end_idx}):
{snippet.content}

Examine this snippet and determine:
1. Is it relevant to the current goal/query?
2. What are the key findings?
3. What actions might this suggest?

Respond with JSON:
{{
  "relevant": true/false,
  "summary": "brief summary of what this snippet contains",
  "key_findings": ["list of important findings"],
  "suggested_actions": ["list of suggested next actions based on this snippet"],
  "confidence": 0.0-1.0
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use cheaper model for examination
        messages=[
            {
                "role": "system",
                "content": "You are a context examiner. Analyze snippets programmatically. Always respond with valid JSON."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=500,
    )

    import json
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned empty content")
    result = json.loads(content)
    
    return ExaminationResult(
        relevant=result.get("relevant", False),
        summary=result.get("summary", ""),
        key_findings=result.get("key_findings", []),
        suggested_actions=result.get("suggested_actions", []),
        confidence=result.get("confidence", 0.5),
    )


@weave.op()
def decompose_task(
    task: str,
    context_summary: str,
    current_depth: int,
    max_depth: int,
) -> dict[str, Any]:
    """Decompose a task into subtasks using RLM pattern.
    
    The agent recursively calls itself, treating the task as part of
    an external environment that can be examined and decomposed.
    """
    client = get_openai_client()
    
    prompt = f"""You are a recursive language model agent. Decompose this task into subtasks.

Current Task: {task}
Context Summary: {context_summary}
Current Depth: {current_depth}/{max_depth}

If the task is simple enough, return it as a single subtask.
If it's complex, break it into 2-4 smaller subtasks that can be handled recursively.

Respond with JSON:
{{
  "should_decompose": true/false,
  "reasoning": "why you chose to decompose or not",
  "subtasks": ["list of subtasks if decomposing", "or empty list if not"],
  "next_action": "what to do next if not decomposing"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at task decomposition. Break complex tasks into manageable subtasks. Always respond with valid JSON."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=800,
    )

    import json
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned empty content")
    result = json.loads(content)
    return result


@weave.op()
def select_relevant_snippets(
    all_snippets: list[ContextSnippet],
    query: str,
    goal: str,
    top_k: int = 5,
) -> list[ContextSnippet]:
    """Select most relevant snippets from a large context.
    
    This implements the RLM pattern of examining context programmatically
    rather than loading everything into the model context.
    """
    # Examine each snippet
    examinations = []
    for snippet in all_snippets:
        exam_result = examine_context_snippet(snippet, query, goal)
        examinations.append((exam_result.confidence, snippet, exam_result))
    
    # Sort by relevance confidence
    examinations.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k most relevant
    return [snippet for _, snippet, _ in examinations[:top_k]]


@weave.op()
def process_context_recursively(
    context: str,
    goal: str,
    query: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> dict[str, Any]:
    """Process long context recursively by examining snippets.
    
    This is the core RLM operation: instead of loading entire context,
    we examine it in chunks programmatically and extract what's relevant.
    """
    # Split context into overlapping snippets
    snippets = []
    start = 0
    idx = 0
    
    while start < len(context):
        end = min(start + chunk_size, len(context))
        snippet = ContextSnippet(
            content=context[start:end],
            start_idx=start,
            end_idx=end,
            metadata={"chunk_id": idx}
        )
        snippets.append(snippet)
        start = end - overlap  # Overlap for context continuity
        idx += 1
    
    # Select relevant snippets
    relevant_snippets = select_relevant_snippets(snippets, query, goal, top_k=5)
    
    # Combine relevant snippets
    combined_content = "\n\n---\n\n".join([
        f"[Snippet {s.start_idx}-{s.end_idx}]\n{s.content}"
        for s in relevant_snippets
    ])
    
    return {
        "total_snippets": len(snippets),
        "relevant_snippets": len(relevant_snippets),
        "combined_content": combined_content,
        "snippet_indices": [(s.start_idx, s.end_idx) for s in relevant_snippets],
    }


class RLMContextExaminer:
    """RLM-style context examiner that treats long context as external environment."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def examine(
        self,
        context: str,
        query: str,
        goal: str,
    ) -> dict[str, Any]:
        """Examine long context programmatically using RLM pattern."""
        if len(context) <= self.chunk_size:
            # Small enough to process directly
            snippet = ContextSnippet(
                content=context,
                start_idx=0,
                end_idx=len(context),
            )
            result = examine_context_snippet(snippet, query, goal)
            return {
                "relevant": result.relevant,
                "summary": result.summary,
                "key_findings": result.key_findings,
                "suggested_actions": result.suggested_actions,
            }
        
        # Too long - process recursively
        return process_context_recursively(
            context=context,
            goal=goal,
            query=query,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )
    
    def query_context(
        self,
        context: str,
        question: str,
        goal: str,
    ) -> str:
        """Query context with a specific question using RLM examination."""
        result = self.examine(context, question, goal)
        
        if isinstance(result, dict) and "combined_content" in result:
            # Processed recursively - use combined content
            return result["combined_content"]
        elif isinstance(result, dict) and "summary" in result:
            # Single snippet result
            return result.get("summary", "")
        else:
            return str(result)
