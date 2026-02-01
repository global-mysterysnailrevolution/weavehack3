"""RLM for visual/video context - handling screenshots and frames as snippets."""

from __future__ import annotations

import base64
import os
from typing import Any
from dataclasses import dataclass
from PIL import Image
import io

import weave

# Ensure Weave is initialized
from rvla.weave_init import ensure_weave_init
ensure_weave_init()

from rvla.openai_client import get_openai_client


@dataclass
class VisualSnippet:
    """A visual snippet (screenshot crop or video frame)."""
    image_base64: str
    bbox: tuple[int, int, int, int] | None = None  # (x, y, width, height) if cropped
    frame_index: int | None = None  # For video
    metadata: dict[str, Any] | None = None


@weave.op()
def crop_screenshot(
    screenshot_base64: str,
    bbox: tuple[int, int, int, int],
) -> str:
    """Crop a screenshot to create a visual snippet.
    
    For RLM, we examine visual context in chunks (crops) rather than
    loading the entire screenshot every time.
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Crop
        x, y, width, height = bbox
        cropped = image.crop((x, y, x + width, y + height))
        
        # Encode back to base64
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG")
        cropped_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return cropped_base64
    except Exception as e:
        print(f"[WARN] Failed to crop screenshot: {e}")
        return screenshot_base64  # Return original on error


@weave.op()
def examine_visual_snippet(
    snippet: VisualSnippet,
    query: str,
    goal: str,
) -> dict[str, Any]:
    """Examine a visual snippet programmatically using GPT-4o vision.
    
    This is the RLM pattern for vision: examine visual context in chunks
    rather than loading entire screenshots.
    """
    client = get_openai_client()
    
    prompt = f"""Examine this visual snippet in the context of the goal: {goal}

Query: {query}

Analyze what you see in this image snippet and determine:
1. Is it relevant to the goal/query?
2. What elements are visible?
3. What actions might this suggest?

Respond with JSON:
{{
  "relevant": true/false,
  "description": "what you see in this snippet",
  "elements": ["list of UI elements visible"],
  "suggested_actions": ["actions this snippet suggests"],
  "confidence": 0.0-1.0
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",  # Use vision model
        messages=[
            {
                "role": "system",
                "content": "You are a visual context examiner. Analyze image snippets programmatically. Always respond with valid JSON."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{snippet.image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
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
    return result


@weave.op()
def divide_screenshot_into_snippets(
    screenshot_base64: str,
    grid_size: tuple[int, int] = (3, 3),  # 3x3 grid = 9 snippets
) -> list[VisualSnippet]:
    """Divide a screenshot into visual snippets for RLM examination.
    
    Instead of analyzing entire screenshot, we examine it in chunks.
    """
    try:
        # Decode image
        image_data = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        
        # Calculate snippet size
        cols, rows = grid_size
        snippet_width = width // cols
        snippet_height = height // rows
        
        snippets = []
        for row in range(rows):
            for col in range(cols):
                x = col * snippet_width
                y = row * snippet_height
                bbox = (x, y, snippet_width, snippet_height)
                
                # Crop snippet
                cropped_base64 = crop_screenshot(screenshot_base64, bbox)
                
                snippet = VisualSnippet(
                    image_base64=cropped_base64,
                    bbox=bbox,
                    metadata={
                        "grid_position": (row, col),
                        "grid_size": grid_size,
                    }
                )
                snippets.append(snippet)
        
        return snippets
    except Exception as e:
        print(f"[WARN] Failed to divide screenshot: {e}")
        # Return full screenshot as single snippet
        return [VisualSnippet(image_base64=screenshot_base64)]


@weave.op()
def select_relevant_visual_snippets(
    snippets: list[VisualSnippet],
    query: str,
    goal: str,
    top_k: int = 3,
) -> list[VisualSnippet]:
    """Select most relevant visual snippets using RLM examination."""
    examinations = []
    
    for snippet in snippets:
        exam_result = examine_visual_snippet(snippet, query, goal)
        confidence = exam_result.get("confidence", 0.5)
        relevant = exam_result.get("relevant", False)
        
        # Score: confidence if relevant, 0 if not
        score = confidence if relevant else 0.0
        examinations.append((score, snippet, exam_result))
    
    # Sort by score
    examinations.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k
    return [snippet for _, snippet, _ in examinations[:top_k]]


class VisualRLMExaminer:
    """RLM examiner for visual/video context."""
    
    def __init__(self, grid_size: tuple[int, int] = (3, 3)):
        self.grid_size = grid_size
    
    def examine_screenshot(
        self,
        screenshot_base64: str,
        query: str,
        goal: str,
    ) -> dict[str, Any]:
        """Examine a screenshot using RLM pattern: divide and examine snippets."""
        # Divide into snippets
        snippets = divide_screenshot_into_snippets(
            screenshot_base64,
            grid_size=self.grid_size,
        )
        
        # Select relevant snippets
        relevant = select_relevant_visual_snippets(
            snippets,
            query=query,
            goal=goal,
            top_k=3,
        )
        
        # Combine results
        results = []
        for snippet in relevant:
            exam = examine_visual_snippet(snippet, query, goal)
            results.append({
                "bbox": snippet.bbox,
                "description": exam.get("description", ""),
                "elements": exam.get("elements", []),
                "suggested_actions": exam.get("suggested_actions", []),
            })
        
        return {
            "total_snippets": len(snippets),
            "relevant_snippets": len(relevant),
            "findings": results,
            "combined_description": " | ".join([r["description"] for r in results]),
        }
