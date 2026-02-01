"""Enhanced context management for ultralong VLA tasks."""

from __future__ import annotations

import os
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
import json

import weave
from openai import OpenAI


@dataclass
class Event:
    """Structured event with metadata for better context management."""
    timestamp: str
    type: str  # "observe", "act", "plan", "subcall", "analysis"
    content: str
    importance: float = 0.5  # 0.0 to 1.0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@weave.op()
def summarize_events(events: list[Event], max_tokens: int = 500) -> str:
    """Summarize a list of events into a compressed representation."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    if not events:
        return "No events to summarize."
    
    # Convert events to text
    events_text = "\n".join([
        f"[{e.timestamp}] {e.type}: {e.content}"
        for e in events
    ])
    
    prompt = f"""Summarize these events into a concise representation (max {max_tokens} tokens):

{events_text}

Provide a summary that captures:
1. Key actions taken
2. Important observations
3. Progress toward goals
4. Any failures or issues

Keep it concise but informative."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use cheaper model for summarization
        messages=[
            {"role": "system", "content": "You are a helpful summarizer. Create concise summaries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    
    return response.choices[0].message.content


@weave.op()
def embed_event(event: Event) -> list[float]:
    """Generate embedding for an event for semantic search."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    text = f"{event.type}: {event.content}"
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    
    return response.data[0].embedding


@weave.op()
def retrieve_relevant_events(
    query: str,
    events: list[Event],
    top_k: int = 5,
) -> list[Event]:
    """Retrieve most relevant events using semantic similarity."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    if not events:
        return []
    
    # Generate query embedding
    query_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    query_embedding = query_response.data[0].embedding
    
    # Calculate similarities (simple cosine similarity)
    import numpy as np
    
    scored_events = []
    for event in events:
        if event.embedding:
            # Cosine similarity
            similarity = np.dot(query_embedding, event.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(event.embedding)
            )
            scored_events.append((similarity, event))
        else:
            # If no embedding, use importance score
            scored_events.append((event.importance, event))
    
    # Sort by score and return top_k
    scored_events.sort(key=lambda x: x[0], reverse=True)
    return [event for _, event in scored_events[:top_k]]


class ContextManager:
    """Manages context for ultralong VLA tasks with compression and retrieval."""
    
    def __init__(self, max_recent_events: int = 20, compression_threshold: int = 50):
        self.max_recent_events = max_recent_events
        self.compression_threshold = compression_threshold
        self.events: list[Event] = []
        self.summaries: list[str] = []
    
    def add_event(
        self,
        event_type: str,
        content: str,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        """Add a new event to the context."""
        event = Event(
            timestamp=datetime.now().isoformat(),
            type=event_type,
            content=content,
            importance=importance,
            metadata=metadata or {},
        )
        
        # Generate embedding for important events
        if importance > 0.7:
            try:
                event.embedding = embed_event(event)
            except Exception as e:
                print(f"[WARN] Failed to embed event: {e}")
        
        self.events.append(event)
        
        # Compress if we have too many events
        if len(self.events) > self.compression_threshold:
            self._compress_old_events()
        
        return event
    
    def _compress_old_events(self) -> None:
        """Compress old events into summaries."""
        if len(self.events) <= self.max_recent_events:
            return
        
        # Keep recent events, compress older ones
        recent_events = self.events[-self.max_recent_events:]
        old_events = self.events[:-self.max_recent_events]
        
        if old_events:
            try:
                summary = summarize_events(old_events)
                self.summaries.append(summary)
                self.events = recent_events
                print(f"[INFO] Compressed {len(old_events)} events into summary")
            except Exception as e:
                print(f"[WARN] Failed to compress events: {e}")
    
    def get_context(
        self,
        query: str | None = None,
        include_recent: bool = True,
        include_summaries: bool = True,
        include_relevant: bool = True,
    ) -> list[str]:
        """Get context for LLM, including recent events, summaries, and relevant past events."""
        context = []
        
        # Add summaries of old events
        if include_summaries and self.summaries:
            context.append("=== Summarized History ===")
            for i, summary in enumerate(self.summaries[-3:], 1):  # Last 3 summaries
                context.append(f"Summary {i}: {summary}")
        
        # Add relevant past events if query provided
        if include_relevant and query:
            relevant = retrieve_relevant_events(query, self.events, top_k=5)
            if relevant:
                context.append("\n=== Relevant Past Events ===")
                for event in relevant:
                    context.append(f"[{event.timestamp}] {event.type}: {event.content}")
        
        # Add recent events
        if include_recent:
            context.append("\n=== Recent Events ===")
            for event in self.events[-self.max_recent_events:]:
                context.append(f"[{event.timestamp}] {event.type}: {event.content}")
        
        return context
    
    def get_events_for_llm(self, query: str | None = None) -> list[str]:
        """Get formatted events for LLM input."""
        context = self.get_context(query=query)
        return context
