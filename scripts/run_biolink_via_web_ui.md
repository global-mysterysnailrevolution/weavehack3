# Running Biolink Pricing via Web UI

You can also run this task through the web UI, which provides real-time visualization and better monitoring.

## Steps

1. **Start the backend:**
   ```bash
   cd api
   python main.py
   ```

2. **Start the frontend:**
   ```bash
   cd web
   npm run dev
   ```

3. **Open the web UI:**
   - Navigate to `http://localhost:3000`
   - The app will automatically use your environment variables

4. **Run the task:**
   - Paste the task from `demos/biolink_pricing_task.txt` into the goal input
   - Click "Start Agent"
   - Watch real-time execution in the dashboard

## Advantages of Web UI

- ✅ Real-time log streaming
- ✅ Screenshot viewer
- ✅ Action history visualization
- ✅ Weave trace integration
- ✅ Better error visibility

## Task Description

Copy this into the goal input:

```
Navigate to https://www.shopbiolinkdepot.org/ and find all products with listed prices. For each product:

1. Take a screenshot of the product page showing the price
2. Search Google for the product name to find actual market prices
3. Compare product images from Google results to confirm it's the same item
4. Identify if the item is only available on eBay or from legitimate vendors
5. Document the pricing difference between shopbiolinkdepot.org and actual market prices
6. Save all findings to a structured JSON file
```

The agent will automatically:
- Navigate to the store
- Extract product information
- Search Google for each product
- Compare prices and images
- Document findings
