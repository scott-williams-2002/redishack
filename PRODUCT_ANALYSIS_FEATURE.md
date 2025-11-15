# Product Marketing Analysis Feature - CopilotKit AG-UI Integration

This document describes the new **Product Marketing Analysis** feature that uses CopilotKit's AG-UI (Agents<->Users) protocol to dynamically render custom UI components from agent tool calls.

## Overview

The feature allows the AI agent to analyze products for manipulative marketing tactics and render a visually appealing custom `ProductCard` component directly in the CopilotKit chat sidebar. This demonstrates the power of AG-UI for creating dynamic, context-aware user interfaces driven by agent tool calls.

## Architecture

### Frontend Components

#### 1. **ProductCard Component** (`src/components/ProductCard.tsx`)
A React component that displays:
- Product name and link
- Product image
- Product description
- List of identified manipulative marketing tactics
- A user question asking for confirmation or denial

**Styling**: Uses Tailwind CSS with a red-themed design to emphasize the critical nature of marketing tactic analysis.

#### 2. **Page Integration** (`src/app/page.tsx`)
The main page component includes:
- `useCopilotAction` hook for `analyze_product_marketing`
- Configured to render the `ProductCard` component when the agent calls the tool
- Parses tactics from pipe-delimited string format

### Backend Components

#### 1. **Product Analyzer Tool** (`agent/tools/product_analyzer.py`)
A LangChain tool that:
- Accepts product details and suspected manipulative tactics
- Generates structured response data
- Returns data formatted for frontend rendering

**Tool Signature**:
```python
@tool
def analyze_product_marketing(
    product_name: str,
    product_link: str,
    image_url: str,
    description: str,
    suspected_tactics: str,
) -> dict
```

#### 2. **Agent Integration** (`agent/agent.py`)
- Imports the `analyze_product_marketing` tool
- Adds it to the `backend_tools` list
- Tool is available for the agent to call during conversations

## How It Works

### Flow Diagram

```
User Message
    ↓
Agent (LLM) processes request
    ↓
Agent identifies need to call analyze_product_marketing tool
    ↓
Tool executes and returns structured data
    ↓
CopilotKit AG-UI matches tool name to useCopilotAction hook
    ↓
ProductCard component renders in chat sidebar
    ↓
User sees custom UI with product analysis
```

### Step-by-Step Example

1. **User asks the agent**: "Analyze this product for manipulative marketing tactics: Amazon Echo Dot, with limited-time offer badge and fake scarcity messaging"

2. **Agent processes the request** and calls the `analyze_product_marketing` tool with:
   - `product_name`: "Amazon Echo Dot"
   - `product_link`: "https://amazon.com/..."
   - `image_url`: "https://..."
   - `description`: "Smart speaker with voice control"
   - `suspected_tactics`: "Artificial scarcity, Limited-time offer badge, Social proof manipulation"

3. **Tool returns structured data**:
   ```json
   {
     "productName": "Amazon Echo Dot",
     "productLink": "https://amazon.com/...",
     "imageUrl": "https://...",
     "description": "Smart speaker with voice control",
     "manipulativeTactics": "Artificial scarcity|Limited-time offer badge|Social proof manipulation",
     "userQuestion": "Do you agree that 'Amazon Echo Dot' uses these manipulative marketing tactics?..."
   }
   ```

4. **CopilotKit AG-UI** matches the tool call to the `useCopilotAction` hook named `analyze_product_marketing`

5. **ProductCard component renders** in the chat sidebar with:
   - Product image and link
   - Description
   - Red-highlighted list of tactics
   - Question for user confirmation

## Usage

### Running the Development Server

From the root of the repository:

```bash
npm run dev
```

This command:
- Starts the Next.js UI development server on `http://localhost:3000`
- Starts the LangGraph agent backend on `http://localhost:8123`
- Both run concurrently with live reload

### Interacting with the Feature

1. Open `http://localhost:3000` in your browser
2. The CopilotKit sidebar opens on the right side
3. Ask the agent to analyze a product, for example:
   - "Analyze this product for manipulative marketing: [product details]"
   - "What marketing tactics does [product name] use?"
   - "Check if this product uses deceptive marketing"

4. The agent will:
   - Identify manipulative tactics
   - Call the `analyze_product_marketing` tool
   - Render the custom `ProductCard` component in the chat

5. Review the rendered component and confirm or deny the analysis

## Customization

### Modifying the ProductCard Component

Edit `src/components/ProductCard.tsx` to:
- Change colors and styling
- Add additional product information
- Modify the user question
- Add interactive elements (buttons, forms, etc.)

### Adding More Tactics

The `suspected_tactics` parameter accepts a comma-separated list. Modify the agent's system prompt to instruct it to identify specific tactics relevant to your use case.

### Extending the Tool

Edit `agent/tools/product_analyzer.py` to:
- Add more sophisticated analysis logic
- Integrate with external APIs for product data
- Store analysis results in Redis or a database
- Generate more detailed reports

## Technical Details

### AG-UI Protocol

CopilotKit uses the AG-UI (Agents<->Users) protocol to:
1. Define tools in the backend agent
2. Register UI renderers in the frontend using `useCopilotAction`
3. Match tool calls to UI renderers by tool name
4. Pass tool arguments to the UI renderer

### Tool Parameters

The `useCopilotAction` hook parameters must match the tool's parameters:
- `productName` (string)
- `productLink` (string)
- `imageUrl` (string)
- `description` (string)
- `manipulativeTactics` (string, pipe-delimited)
- `userQuestion` (string)

### Rendering Logic

The `render` function in `useCopilotAction`:
```typescript
render: ({ args }) => {
  const tactics = typeof args.manipulativeTactics === 'string' 
    ? args.manipulativeTactics.split('|').filter((t: string) => t.trim())
    : args.manipulativeTactics;
  
  return (
    <ProductCard
      productName={args.productName}
      productLink={args.productLink}
      imageUrl={args.imageUrl}
      description={args.description}
      manipulativeTactics={tactics}
      userQuestion={args.userQuestion}
    />
  );
}
```

## Files Modified/Created

### Created
- `src/components/ProductCard.tsx` - Custom UI component
- `agent/tools/product_analyzer.py` - Backend tool

### Modified
- `src/app/page.tsx` - Added `useCopilotAction` hook for `analyze_product_marketing`
- `agent/agent.py` - Imported and added tool to `backend_tools`

## Next Steps

1. **Test the feature** by running `npm run dev` and interacting with the agent
2. **Customize the ProductCard** styling to match your brand
3. **Extend the tool** with more sophisticated analysis logic
4. **Add more tools** following the same AG-UI pattern
5. **Deploy** to production with proper environment variables

## Resources

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [AG-UI Protocol](https://docs.ag-ui.com/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [Tailwind CSS](https://tailwindcss.com/)

## Troubleshooting

### ProductCard not rendering
- Ensure the tool name matches exactly: `analyze_product_marketing`
- Check that all required parameters are provided
- Verify the `useCopilotAction` hook is registered before the component renders

### Tool not being called
- Check the agent's system prompt to ensure it knows about the tool
- Verify the tool is in the `backend_tools` list in `agent.py`
- Check the LangGraph CLI output for errors

### Styling issues
- Ensure Tailwind CSS is properly configured in `tailwind.config.ts`
- Check that `@copilotkit/react-ui/styles.css` is imported in `layout.tsx`
- Verify no CSS conflicts with existing styles
