"""Redis-based prompt database for storing and retrieving learned prompts.

This module implements a system that:
1. Extracts problem patterns from Weave traces
2. Stores improved prompts with structured metadata
3. Retrieves relevant prompts based on task context
4. Makes learned prompts available as tools for OpenClaw
"""

from __future__ import annotations

import os
import json
import hashlib
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import weave
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from rvla.weave_init import ensure_weave_init
ensure_weave_init()


@weave.op()
def extract_problem_patterns_from_weave_trace(
    trace_data: dict[str, Any],
    goal: str,
) -> list[ProblemPattern]:
    """Extract problem patterns from a Weave trace.
    
    Analyzes the trace to identify:
    - What went wrong
    - What patterns indicate problems
    - What indicates success
    """
    patterns: list[ProblemPattern] = []
    
    # Extract events/actions from trace
    events = trace_data.get("events", [])
    output_tail = trace_data.get("output_tail", [])
    analysis = trace_data.get("analysis", {})
    
    # Combine output for analysis
    full_output = "\n".join(output_tail) if isinstance(output_tail, list) else str(output_tail)
    lower = full_output.lower()
    
    # Check for common problem patterns
    problem_checks = {
        "navigation_failure": {
            "indicators": ["error", "failed", "timeout", "could not", "unable to"],
            "context_keywords": ["navigate", "visit", "go to", "open"],
        },
        "missing_search": {
            "indicators": ["no search", "did not search", "missing search"],
            "context_keywords": ["search", "google", "bing", "find"],
        },
        "incomplete_output": {
            "indicators": ["incomplete", "missing", "did not save", "no output"],
            "context_keywords": ["save", "output", "json", "file", "document"],
        },
        "missing_screenshots": {
            "indicators": ["no screenshot", "did not capture", "missing image"],
            "context_keywords": ["screenshot", "image", "capture", "photo"],
        },
        "pricing_extraction_failure": {
            "indicators": ["no price", "could not extract", "missing price"],
            "context_keywords": ["price", "pricing", "cost", "$"],
        },
    }
    
    for problem_type, config in problem_checks.items():
        # Check if problem indicators are present
        has_indicators = any(ind in lower for ind in config["indicators"])
        has_context = any(kw in goal.lower() for kw in config["context_keywords"])
        
        if has_indicators or (has_context and analysis.get("score", 1.0) < 0.7):
            success_indicators = [
                ind.replace("no ", "").replace("missing ", "").replace("did not ", "")
                for ind in config["indicators"]
            ]
            patterns.append(ProblemPattern(
                problem_type=problem_type,
                context=goal[:200],
                error_indicators=config["indicators"],
                success_indicators=success_indicators + config["context_keywords"],
                frequency=1,
            ))
    
    # Extract from analysis if available
    if analysis:
        analysis_patterns = extract_problem_patterns_from_analysis(analysis, goal)
        # Merge with existing patterns
        for ap in analysis_patterns:
            # Check if pattern already exists
            existing = next(
                (p for p in patterns if p.problem_type == ap.problem_type),
                None
            )
            if existing:
                existing.frequency += 1
            else:
                patterns.append(ap)
    
    return patterns


@dataclass
class ProblemPattern:
    """Structured representation of a problem identified from Weave traces."""
    problem_type: str  # e.g., "navigation_failure", "missing_search", "incomplete_output"
    context: str  # Task context where this problem occurred
    error_indicators: list[str]  # Keywords/patterns that indicate this problem
    success_indicators: list[str]  # What indicates success for this problem type
    frequency: int = 1  # How many times this pattern was observed


@dataclass
class LearnedPrompt:
    """A learned prompt with metadata for retrieval."""
    prompt_id: str  # Unique identifier (hash of original prompt + context)
    original_prompt: str  # The original prompt that had issues
    improved_prompt: str  # The improved version
    problem_patterns: list[ProblemPattern]  # Problems this prompt addresses
    task_context: str  # Context where this prompt is applicable
    task_type: str  # e.g., "pricing_extraction", "web_navigation", "data_collection"
    success_rate: float  # 0.0 to 1.0
    created_at: str  # ISO timestamp
    metadata: dict[str, Any]  # Additional metadata (suggestions, scores, etc.)
    usage_count: int = 0  # How many times this prompt has been used
    last_used: Optional[str] = None  # ISO timestamp


class PromptDatabase:
    """Redis-based database for storing and retrieving learned prompts."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize the prompt database with Redis connection."""
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._client: Optional[Redis] = None
        self._connected = False
        
        if self.redis_url:
            try:
                # Clean up Redis URL format if needed
                clean_url = self._clean_redis_url(self.redis_url)
                self._client = Redis.from_url(clean_url, decode_responses=True)
                # Test connection
                self._client.ping()
                self._connected = True
                print(f"[OK] PromptDatabase connected to Redis")
            except (RedisConnectionError, Exception) as e:
                print(f"[WARN] PromptDatabase Redis connection failed: {e}. Using in-memory storage.")
                self._connected = False
                self._client = None
                self._in_memory_store: dict[str, str] = {}
        else:
            print("[INFO] PromptDatabase: No REDIS_URL provided. Using in-memory storage.")
            self._in_memory_store: dict[str, str] = {}
    
    def _clean_redis_url(self, url: str) -> str:
        """Clean up Redis URL format if needed."""
        # Handle format: redis://:<PASSWORD>:<PORT>/0
        if url.startswith("redis://:") and ":" in url[9:]:
            parts = url.replace("redis://:", "").split(":")
            if len(parts) >= 2:
                password = parts[0]
                port_and_db = parts[1]
                port = port_and_db.split("/")[0]
                db = port_and_db.split("/")[1] if "/" in port_and_db else "0"
                host = os.getenv("REDIS_HOST", "redis-17120.c289.us-west-1-2.ec2.cloud.redislabs.com")
                return f"redis://:{password}@{host}:{port}/{db}"
        return url
    
    def _key(self, prompt_id: str) -> str:
        """Generate Redis key for a prompt."""
        return f"prompt:db:{prompt_id}"
    
    def _index_key(self, field: str, value: str) -> str:
        """Generate Redis key for an index."""
        return f"prompt:index:{field}:{value}"
    
    def _store(self, key: str, value: str) -> None:
        """Store a value in Redis or in-memory."""
        if self._connected and self._client:
            self._client.set(key, value)
        else:
            self._in_memory_store[key] = value
    
    def _get(self, key: str) -> Optional[str]:
        """Get a value from Redis or in-memory."""
        if self._connected and self._client:
            return self._client.get(key)
        else:
            return self._in_memory_store.get(key)
    
    def _delete(self, key: str) -> None:
        """Delete a key from Redis or in-memory."""
        if self._connected and self._client:
            self._client.delete(key)
        else:
            self._in_memory_store.pop(key, None)
    
    def _get_all_keys(self, pattern: str) -> list[str]:
        """Get all keys matching a pattern."""
        if self._connected and self._client:
            return [key for key in self._client.scan_iter(match=pattern)]
        else:
            return [key for key in self._in_memory_store.keys() if pattern.replace("*", "") in key]
    
    def store_prompt(self, learned_prompt: LearnedPrompt) -> None:
        """Store a learned prompt in the database."""
        key = self._key(learned_prompt.prompt_id)
        value = json.dumps(asdict(learned_prompt), indent=2)
        self._store(key, value)
        
        # Create indexes for fast retrieval
        # Index by task type
        task_index_key = self._index_key("task_type", learned_prompt.task_type)
        if self._connected and self._client:
            self._client.sadd(task_index_key, learned_prompt.prompt_id)
        else:
            # In-memory index
            if not hasattr(self, "_task_index"):
                self._task_index: dict[str, set[str]] = {}
            if learned_prompt.task_type not in self._task_index:
                self._task_index[learned_prompt.task_type] = set()
            self._task_index[learned_prompt.task_type].add(learned_prompt.prompt_id)
        
        print(f"[OK] Stored prompt: {learned_prompt.prompt_id[:8]}... ({learned_prompt.task_type})")
    
    def get_prompt(self, prompt_id: str) -> Optional[LearnedPrompt]:
        """Retrieve a prompt by ID."""
        key = self._key(prompt_id)
        value = self._get(key)
        if not value:
            return None
        
        data = json.loads(value)
        # Reconstruct ProblemPattern objects
        data["problem_patterns"] = [
            ProblemPattern(**pp) for pp in data["problem_patterns"]
        ]
        return LearnedPrompt(**data)
    
    def find_relevant_prompts(
        self,
        task_context: str,
        task_type: Optional[str] = None,
        min_success_rate: float = 0.7,
        limit: int = 5,
    ) -> list[LearnedPrompt]:
        """Find relevant prompts based on task context and type."""
        candidates: list[LearnedPrompt] = []
        
        # First, try to find by task type
        if task_type:
            task_index_key = self._index_key("task_type", task_type)
            if self._connected and self._client:
                prompt_ids = self._client.smembers(task_index_key)
            else:
                prompt_ids = list(getattr(self, "_task_index", {}).get(task_type, set()))
            
            for prompt_id in prompt_ids:
                prompt = self.get_prompt(prompt_id)
                if prompt and prompt.success_rate >= min_success_rate:
                    candidates.append(prompt)
        
        # If no task type match, search all prompts
        if not candidates:
            pattern = self._key("*")
            keys = self._get_all_keys(pattern)
            for key in keys:
                prompt_id = key.replace("prompt:db:", "")
                prompt = self.get_prompt(prompt_id)
                if prompt and prompt.success_rate >= min_success_rate:
                    candidates.append(prompt)
        
        # Score candidates by context similarity
        scored = []
        task_lower = task_context.lower()
        for prompt in candidates:
            score = 0.0
            context_lower = prompt.task_context.lower()
            
            # Exact context match
            if context_lower in task_lower or task_lower in context_lower:
                score += 10.0
            
            # Keyword overlap
            task_words = set(task_lower.split())
            context_words = set(context_lower.split())
            overlap = len(task_words & context_words)
            score += overlap * 0.5
            
            # Problem pattern relevance
            for pattern in prompt.problem_patterns:
                for indicator in pattern.error_indicators:
                    if indicator.lower() in task_lower:
                        score += 1.0
            
            # Success rate bonus
            score += prompt.success_rate * 2.0
            
            # Usage count bonus (more used = more trusted)
            score += min(prompt.usage_count * 0.1, 2.0)
            
            scored.append((score, prompt))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        return [prompt for _, prompt in scored[:limit]]
    
    def update_usage(self, prompt_id: str) -> None:
        """Update usage statistics for a prompt."""
        prompt = self.get_prompt(prompt_id)
        if prompt:
            prompt.usage_count += 1
            prompt.last_used = datetime.utcnow().isoformat()
            self.store_prompt(prompt)
    
    @staticmethod
    def extract_problem_patterns_from_analysis(
        analysis: dict[str, Any],
        goal: str,
    ) -> list[ProblemPattern]:
        """Extract problem patterns from OpenClaw analysis output."""
        patterns: list[ProblemPattern] = []
        
        # Map analysis fields to problem types
        problem_mappings = {
            ("search_hits", 0): ("missing_search", ["google", "search", "bing"]),
            ("image_hits", 0): ("missing_screenshots", ["screenshot", "image", "photo"]),
            ("doc_hits", 0): ("incomplete_output", ["json", "file", "save", "document"]),
            ("pricing_hits", 0): ("missing_pricing_data", ["price", "pricing", "$", "usd"]),
            ("vendor_hits", 0): ("missing_vendor_verification", ["vendor", "ebay", "amazon"]),
            ("error_hits", lambda x: x > 0): ("error_occurred", ["error", "failed", "exception"]),
        }
        
        for (field, condition), (problem_type, indicators) in problem_mappings.items():
            value = analysis.get(field, 0)
            if callable(condition):
                matches = condition(value)
            else:
                matches = value == condition
            
            if matches:
                patterns.append(ProblemPattern(
                    problem_type=problem_type,
                    context=goal[:200],  # First 200 chars of goal
                    error_indicators=indicators,
                    success_indicators=[ind.replace("missing_", "").replace("_", " ") for ind in indicators],
                    frequency=1,
                ))
        
        return patterns
    
    def create_learned_prompt(
        self,
        original_prompt: str,
        improved_prompt: str,
        analysis: dict[str, Any],
        goal: str,
        task_type: str = "general",
        metadata: Optional[dict[str, Any]] = None,
        trace_data: Optional[dict[str, Any]] = None,
    ) -> LearnedPrompt:
        """Create a LearnedPrompt from analysis results and optionally Weave trace data."""
        # Generate unique ID
        prompt_hash = hashlib.sha256(
            f"{original_prompt}:{goal}".encode()
        ).hexdigest()[:16]
        
        # Extract problem patterns from analysis
        problem_patterns = self.extract_problem_patterns_from_analysis(analysis, goal)
        
        # If trace data is available, extract additional patterns from Weave trace
        if trace_data:
            weave_patterns = extract_problem_patterns_from_weave_trace(trace_data, goal)
            # Merge patterns, avoiding duplicates
            existing_types = {p.problem_type for p in problem_patterns}
            for wp in weave_patterns:
                if wp.problem_type not in existing_types:
                    problem_patterns.append(wp)
                else:
                    # Update frequency if pattern already exists
                    existing = next(p for p in problem_patterns if p.problem_type == wp.problem_type)
                    existing.frequency += wp.frequency
        
        # Calculate success rate from analysis score
        success_rate = analysis.get("score", 0.0)
        
        return LearnedPrompt(
            prompt_id=prompt_hash,
            original_prompt=original_prompt,
            improved_prompt=improved_prompt,
            problem_patterns=problem_patterns,
            task_context=goal[:500],  # First 500 chars
            task_type=task_type,
            success_rate=success_rate,
            usage_count=0,
            last_used=None,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
    
    def get_prompt_tool_for_openclaw(
        self,
        task_context: str,
        task_type: Optional[str] = None,
    ) -> Optional[str]:
        """Get a relevant learned prompt formatted as a tool/instruction for OpenClaw."""
        prompts = self.find_relevant_prompts(
            task_context=task_context,
            task_type=task_type,
            min_success_rate=0.6,
            limit=1,
        )
        
        if not prompts:
            return None
        
        prompt = prompts[0]
        self.update_usage(prompt.prompt_id)
        
        # Format as a tool/instruction
        tool_text = f"""LEARNED PROMPT TOOL (from past successful runs):

Task Context: {prompt.task_context[:200]}...

Improved Prompt Strategy:
{prompt.improved_prompt}

Problems This Addresses:
{chr(10).join(f"- {pp.problem_type}: {', '.join(pp.error_indicators[:3])}" for pp in prompt.problem_patterns[:3])}

Success Rate: {prompt.success_rate:.0%}
Usage Count: {prompt.usage_count}

Apply this strategy to your current task."""
        
        return tool_text


# Global instance
_prompt_db: Optional[PromptDatabase] = None


def get_prompt_database() -> PromptDatabase:
    """Get or create the global prompt database instance."""
    global _prompt_db
    if _prompt_db is None:
        _prompt_db = PromptDatabase()
    return _prompt_db
