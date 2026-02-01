# Weave Evaluation Pipeline

This implements formal evaluations using Weave's `Model` and `Evaluation` classes to systematically test and improve the RLM-VLA agent.

## What It Does

1. **Wraps the agent as a Weave Model** - Tracks version, configuration, and behavior
2. **Creates test datasets** - Structured test cases with expected outcomes
3. **Defines scoring functions** - Custom scorers for success, efficiency, etc.
4. **Runs evaluations** - Tests the model against the dataset
5. **Tracks improvements** - Compare performance across iterations

## Quick Start

### Run an Evaluation

```bash
python scripts/run_evaluation.py
```

This will:
- Create a Weave Model from your agent
- Load or create a test dataset
- Run the agent on each test case
- Score the results
- Display results and link to Weave dashboard

### Use in Code

```python
from rvla.evaluation import (
    RLMVLAModel,
    create_pricing_evaluation_dataset,
    run_evaluation,
)

# Initialize Weave
import weave
weave.init("your-entity/your-project")

# Create model
model = RLMVLAModel(
    model_name="gpt-4o",
    enable_multi_agent=False,
)

# Create dataset
dataset = create_pricing_evaluation_dataset()

# Run evaluation
results = run_evaluation(model, dataset, name="my_eval")
```

## Available Datasets

### 1. Pricing Extraction Dataset
Tests agent's ability to:
- Navigate to shopbiolinkdepot.org
- Extract product prices
- Search Google for comparisons
- Verify vendor legitimacy
- Save structured results

### 2. General Navigation Dataset
Tests basic web navigation:
- Navigate to websites
- Extract information
- Take screenshots
- Describe observations

## Scoring Functions

### `task_success_score`
Checks if the agent:
- Reported success
- Met minimum step requirements
- Completed required events
- Passed target criteria

### `efficiency_score`
Measures:
- Steps taken vs. ideal steps
- Success rate
- Efficiency ratio

### `MultiTaskBinaryClassificationF1`
Built-in Weave scorer for F1 scores across multiple tasks.

## Viewing Results

After running an evaluation, you'll get:
1. **Terminal output** - Summary of results
2. **Weave dashboard link** - Full traces, charts, and analysis
3. **Structured results** - JSON with scores and metrics

## Integration with Self-Improvement

The evaluation results can be used by:
- `SelfImprovingAgent` - Learn from successful runs
- `PromptDatabase` - Store successful strategies
- `_analyze_openclaw_output` - Generate improvement suggestions

## Example Output

```
======================================================================
WEAVE EVALUATION - RLM-VLA AGENT
======================================================================

Initialized Weave: globalmysterysnailrevolution-provigen-ai/weavehacks-rvla

Creating RLM-VLA Model...
✅ Model created

Creating pricing extraction dataset...
✅ Dataset created: pricing_extraction
   Examples: 2

Running evaluation...
This may take a few minutes as the agent completes each task...

======================================================================
EVALUATION RESULTS
======================================================================

Evaluation: pricing_extraction_eval
Dataset: pricing_extraction
Model: gpt-4o

Summary:
  success_rate: 0.85
  efficiency_score: 0.72
  f1_score: 0.78

✅ Evaluation complete!

View results in Weave: https://wandb.ai/.../weave
```

## Next Steps

1. **Add more test cases** - Expand datasets with more scenarios
2. **Create custom scorers** - Add domain-specific scoring functions
3. **Compare model versions** - Test different prompts/configurations
4. **Track over time** - Run evaluations regularly to measure improvement

## Documentation

- [Weave Evaluation Guide](https://docs.wandb.ai/weave/guides/evaluation/build_an_evaluation)
- [Weave Models](https://docs.wandb.ai/weave/guides/core-types/models)
- [Weave Scorers](https://docs.wandb.ai/weave/guides/evaluation/scorers)
