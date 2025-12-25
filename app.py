import gradio as gr
import asyncio
from tmpai_sales_agent import run_tmpai_sales

def run_async(coro):
    return asyncio.run(coro)

def run_sales_agent(prompt):
    try:
        result = run_async(run_tmpai_sales(prompt, human_approval=False))

        # ---- BEAUTIFUL CARD UI ----
        md = """
<style>
body { background: #0F172A; color: #E2E8F0; }
.card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 22px;
}
.card h2 { color: #60A5FA; margin-top: 0; }
.card pre { white-space: pre-wrap; font-size: 15px; }
</style>
"""

        # Best draft card
        md += f"""
<div class="card">
<h2>🏆 Best Performing Draft</h2>
<p><b>Chosen Agent:</b> {result['chosen_agent']}</p>
<p><b>Final Hybrid Score:</b> {result['score']}</p>
</div>
"""

        # All drafts
        for d in result["scored_details"]:
            md += f"""
<div class="card">
<h2>✉️ Agent {d['agent_index']} — Score: {d['score']['final_score']}</h2>
<pre>{d['text']}</pre>
</div>
"""

        # Cost summary
        c = result["costs"]
        md += f"""
<div class="card">
<h2>💰 Cost Summary</h2>
<p><b>API Calls:</b> {c['calls']}</p>
<p><b>Estimated Cost:</b> ${c['estimated_cost']}</p>
</div>
"""

        return md

    except Exception as e:
        return f"❌ Error: {str(e)}"

# UI Layout
with gr.Blocks() as demo:
    gr.HTML("""
    <div style="text-align:center; padding:20px;">
        <h1 style="color:#60A5FA;">TMP AI Consulting – Sales Automation Agent</h1>
        <p style="color:#E2E8F0;">Generate, compare, and score sales outreach emails using agentic AI.</p>
    </div>
    """)

    inp = gr.Textbox(
        label="Describe the prospect",
        placeholder="Example: CEO needing automation for marketing",
        lines=4
    )

    btn = gr.Button("Generate Emails")
    out = gr.HTML("Results will appear here...")

    btn.click(run_sales_agent, inputs=inp, outputs=out)

demo.launch()