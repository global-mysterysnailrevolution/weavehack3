"""RLM recursive decomposition engine for VLA tasks."""

from __future__ import annotations

import os
from typing import Any
from dataclasses import dataclass, field

import weave
from openai import OpenAI

from rvla.rlm_core import decompose_task, RLMContextExaminer


@dataclass
class DecompositionNode:
    """A node in the recursive decomposition tree."""
    task: str
    depth: int
    parent: DecompositionNode | None = None
    children: list[DecompositionNode] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None


@weave.op()
def recursive_decompose(
    task: str,
    context_summary: str,
    current_depth: int,
    max_depth: int,
    parent_node: DecompositionNode | None = None,
) -> DecompositionNode:
    """Recursively decompose a task following RLM pattern.
    
    The agent calls itself recursively, treating tasks as part of
    an external environment that can be examined and decomposed.
    """
    # Create node for this task
    node = DecompositionNode(
        task=task,
        depth=current_depth,
        parent=parent_node,
        status="in_progress",
    )
    
    # Check if we should decompose further
    if current_depth >= max_depth:
        node.status = "completed"
        node.result = {"action": "execute", "task": task}
        return node
    
    # Decompose the task
    decomposition = decompose_task(task, context_summary, current_depth, max_depth)
    
    if decomposition.get("should_decompose", False):
        # Recursively decompose subtasks
        subtasks = decomposition.get("subtasks", [])
        for subtask in subtasks:
            child_node = recursive_decompose(
                task=subtask,
                context_summary=context_summary,
                current_depth=current_depth + 1,
                max_depth=max_depth,
                parent_node=node,
            )
            node.children.append(child_node)
        
        node.status = "completed"
        node.result = {
            "type": "decomposed",
            "subtasks": [child.task for child in node.children],
            "reasoning": decomposition.get("reasoning", ""),
        }
    else:
        # Task is simple enough - mark as executable
        node.status = "completed"
        node.result = {
            "type": "executable",
            "action": decomposition.get("next_action", "execute"),
            "task": task,
        }
    
    return node


@weave.op()
def execute_decomposition_tree(
    root_node: DecompositionNode,
    executor_func: callable,
) -> dict[str, Any]:
    """Execute a decomposition tree, calling executor for each leaf node."""
    results = []
    
    def traverse(node: DecompositionNode):
        if not node.children:
            # Leaf node - execute
            if node.result and node.result.get("type") == "executable":
                result = executor_func(node.task, node.depth)
                node.result["execution_result"] = result
                results.append({
                    "task": node.task,
                    "depth": node.depth,
                    "result": result,
                })
        else:
            # Internal node - traverse children
            for child in node.children:
                traverse(child)
    
    traverse(root_node)
    
    return {
        "root_task": root_node.task,
        "total_nodes": count_nodes(root_node),
        "leaf_nodes": len([n for n in get_all_nodes(root_node) if not n.children]),
        "results": results,
    }


def count_nodes(node: DecompositionNode) -> int:
    """Count total nodes in decomposition tree."""
    count = 1
    for child in node.children:
        count += count_nodes(child)
    return count


def get_all_nodes(node: DecompositionNode) -> list[DecompositionNode]:
    """Get all nodes in decomposition tree."""
    nodes = [node]
    for child in node.children:
        nodes.extend(get_all_nodes(child))
    return nodes


class RLMDecomposer:
    """RLM-style recursive decomposer for VLA tasks."""
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.context_examiner = RLMContextExaminer()
    
    def decompose_and_execute(
        self,
        task: str,
        context: str,
        executor_func: callable,
    ) -> dict[str, Any]:
        """Decompose task recursively and execute using RLM pattern."""
        # Examine context to get summary
        context_summary = self.context_examiner.query_context(
            context=context,
            question="What is the current state and relevant information?",
            goal=task,
        )
        
        # Recursively decompose
        root_node = recursive_decompose(
            task=task,
            context_summary=context_summary[:500],  # Limit summary size
            current_depth=0,
            max_depth=self.max_depth,
        )
        
        # Execute decomposition tree
        execution_result = execute_decomposition_tree(root_node, executor_func)
        
        return {
            "decomposition_tree": root_node,
            "execution": execution_result,
            "context_summary": context_summary,
        }
