# Quick Start - Get Demo Working NOW

## Step 1: Test Your Setup (30 seconds)

```bash
python scripts/quick_test.py
```

This will check:
- ✅ Environment variables
- ✅ Weave initialization
- ✅ Core modules
- ✅ Workspace
- ✅ WebDriver (optional)

## Step 2: Run Quick Demo (1 minute)

```bash
python scripts/quick_demo.py
```

This runs a **mock demo** that:
- Creates 3 iterations logged to Weave
- Shows improvement (0.65 → 0.82 → 0.91)
- Works immediately without browser automation

## Step 3: Check Weave Dashboard

1. Go to: `https://wandb.ai/{your-entity}/weavehacks-rvla/weave`
2. You should see 3 `mock_iteration` calls
3. Click on each to see the improvement

## Step 4: View Marimo Dashboard

1. **Publish Marimo notebook:**
   ```bash
   cd marimo
   marimo run weave_dashboard.py
   # Then publish via marimo.app
   ```

2. **Or view locally:**
   ```bash
   cd marimo
   marimo edit weave_dashboard.py
   ```

3. **Set in Vercel:**
   - Add `MARIMO_PROXY_URL` to Vercel env vars
   - Point to your published notebook

## Step 5: Run Full Demo (if browser automation works)

```bash
python scripts/hackathon_demo.py
```

This runs the **real agent** with actual web navigation.

## Environment Variables Needed

Create `.env` file:

```bash
OPENAI_API_KEY=sk-...
WANDB_API_KEY=your_key
WANDB_PROJECT=weavehacks-rvla
WANDB_ENTITY=your_username
BROWSERBASE_API_KEY=bb_...  # Optional
BROWSERBASE_PROJECT_ID=...  # Optional
```

## Troubleshooting

### Weave not working?
- Check `WANDB_API_KEY` is set
- Check `WANDB_PROJECT` is set
- Try: `wandb login` in terminal

### Browser automation not working?
- That's OK! Use `quick_demo.py` instead
- It uses mock data but still logs to Weave
- Shows the same improvement pattern

### Marimo not showing data?
- Make sure you've run at least one iteration
- Check Weave project name matches
- Refresh the Marimo notebook

## For Hackathon Demo

**Use `quick_demo.py` for the live demo** - it's:
- ✅ Fast (runs in seconds)
- ✅ Reliable (no browser dependencies)
- ✅ Shows clear improvement
- ✅ Logs to Weave
- ✅ Can be visualized in Marimo

Then show the **real agent** as a bonus if time permits!
