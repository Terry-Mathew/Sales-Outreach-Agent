"""
Gradio Application - Web UI for the Sales Outreach Agent.
"""

import gradio as gr
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.pipeline import run_sales_pipeline, PipelineResult


def run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create new loop
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def format_draft_card(draft, index: int) -> str:
    """Format a single draft as an HTML card."""
    score = draft.score or {}
    final_score = score.get("final_score", 0)
    rule_score = score.get("rule_score", 0)
    llm_score = score.get("llm_score", 0)
    
    # Determine score color
    if final_score >= 80:
        score_color = "#22c55e"  # Green
    elif final_score >= 60:
        score_color = "#eab308"  # Yellow
    else:
        score_color = "#ef4444"  # Red
    
    # Get improvement suggestions
    suggestions = score.get("improvement_suggestions", [])
    suggestions_html = ""
    if suggestions:
        suggestions_html = f"""
        <div style="margin-top: 12px; padding: 10px; background: rgba(96, 165, 250, 0.1); border-radius: 6px;">
            <strong style="color: #60A5FA;">💡 Suggestions:</strong>
            <ul style="margin: 5px 0 0 15px; padding: 0;">
                {"".join(f'<li style="color: #94a3b8; font-size: 13px;">{s}</li>' for s in suggestions[:2])}
            </ul>
        </div>
        """
    
    # Subject line
    subject = draft.subject or "AI automation for your team"
    
    return f"""
    <div style="background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #334155; 
                border-radius: 12px; padding: 20px; margin-bottom: 16px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="margin: 0; color: #f1f5f9; font-size: 16px;">
                ✉️ Agent {index}: {draft.agent_name}
            </h3>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span style="background: {score_color}; color: white; padding: 4px 12px; 
                            border-radius: 20px; font-weight: bold; font-size: 14px;">
                    Score: {final_score}
                </span>
            </div>
        </div>
        
        <div style="display: flex; gap: 12px; margin-bottom: 12px;">
            <span style="color: #94a3b8; font-size: 12px; background: #334155; padding: 2px 8px; border-radius: 4px;">
                📊 Rules: {rule_score}
            </span>
            <span style="color: #94a3b8; font-size: 12px; background: #334155; padding: 2px 8px; border-radius: 4px;">
                🤖 LLM: {llm_score}
            </span>
        </div>
        
        <div style="background: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
            <strong style="color: #60A5FA; font-size: 13px;">Subject:</strong>
            <p style="color: #e2e8f0; margin: 4px 0 0 0; font-size: 14px;">{subject}</p>
        </div>
        
        <div style="background: #0f172a; border-radius: 8px; padding: 12px;">
            <strong style="color: #60A5FA; font-size: 13px;">Body:</strong>
            <pre style="color: #cbd5e1; white-space: pre-wrap; font-size: 14px; 
                        font-family: 'Inter', sans-serif; margin: 8px 0 0 0; line-height: 1.6;">{draft.text}</pre>
        </div>
        
        {suggestions_html}
    </div>
    """


def format_result(result: PipelineResult) -> str:
    """Format pipeline result as beautiful HTML."""
    
    # Header with winner
    winner = None
    for draft in result.all_drafts:
        if draft.agent_index == result.chosen_agent_index:
            winner = draft
            break
    
    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .sales-result {{ font-family: 'Inter', sans-serif; }}
    </style>
    
    <div class="sales-result" style="color: #e2e8f0;">
        
        <!-- Winner Card -->
        <div style="background: linear-gradient(145deg, #1e40af, #3b82f6); border-radius: 16px; 
                    padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <span style="font-size: 32px;">🏆</span>
                <div>
                    <h2 style="margin: 0; color: white; font-size: 20px;">Best Performing Draft</h2>
                    <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px;">
                        Agent: <strong>{result.chosen_agent}</strong> | 
                        Final Score: <strong>{result.winning_score}</strong>
                    </p>
                </div>
            </div>
            
            {f'''
            <div style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 12px;">
                <strong style="color: rgba(255,255,255,0.9);">Subject:</strong>
                <p style="color: white; margin: 4px 0;">{result.winning_subject or "AI automation for your team"}</p>
            </div>
            ''' if winner else ''}
        </div>
        
        <!-- All Drafts -->
        <h3 style="color: #f1f5f9; margin-bottom: 16px; font-size: 16px; font-weight: 600;">
            📨 All Generated Drafts
        </h3>
    """
    
    # Add all draft cards
    for i, draft in enumerate(result.all_drafts, 1):
        html += format_draft_card(draft, i)
    
    # Cost summary
    costs = result.costs
    html += f"""
        <!-- Cost Summary -->
        <div style="background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #334155; 
                    border-radius: 12px; padding: 20px; margin-top: 8px;">
            <h3 style="margin: 0 0 12px 0; color: #f1f5f9; font-size: 16px;">💰 Cost Summary</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                <div style="text-align: center;">
                    <div style="color: #60A5FA; font-size: 24px; font-weight: bold;">{costs.get('calls', 0)}</div>
                    <div style="color: #94a3b8; font-size: 12px;">API Calls</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #22c55e; font-size: 24px; font-weight: bold;">${costs.get('estimated_cost', 0):.4f}</div>
                    <div style="color: #94a3b8; font-size: 12px;">Estimated Cost</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #eab308; font-size: 24px; font-weight: bold;">{costs.get('duration_seconds', 0):.1f}s</div>
                    <div style="color: #94a3b8; font-size: 12px;">Duration</div>
                </div>
            </div>
        </div>
    </div>
    """
    
    return html


def run_sales_agent(prospect_description: str) -> str:
    """
    Main handler for Gradio interface.
    
    Args:
        prospect_description: Description of the prospect
        
    Returns:
        Formatted HTML result
    """
    if not prospect_description or not prospect_description.strip():
        return """
        <div style="background: #1e293b; border: 1px solid #ef4444; border-radius: 12px; 
                    padding: 20px; color: #ef4444; text-align: center;">
            ⚠️ Please enter a prospect description to generate emails.
        </div>
        """
    
    try:
        # Run the pipeline
        result = run_async(run_sales_pipeline(prospect_description))
        return format_result(result)
        
    except Exception as e:
        return f"""
        <div style="background: #1e293b; border: 1px solid #ef4444; border-radius: 12px; 
                    padding: 20px; color: #ef4444;">
            <h3 style="margin: 0 0 8px 0;">❌ Error</h3>
            <p style="margin: 0;">{str(e)}</p>
            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">
                Make sure your .env file is configured with a valid OPENAI_API_KEY.
            </p>
        </div>
        """


def create_gradio_app() -> gr.Blocks:
    """Create and configure the Gradio application."""
    
    with gr.Blocks() as demo:
        
        # Header
        gr.HTML(f"""
        <div style="text-align: center; padding: 30px 20px; 
                    background: linear-gradient(145deg, #1e293b, #0f172a);
                    border-radius: 16px; margin-bottom: 20px;
                    border: 1px solid #334155;">
            <h1 style="color: #60A5FA; margin: 0; font-size: 28px; font-weight: 700;">
                🚀 {settings.company_name}
            </h1>
            <h2 style="color: #f1f5f9; margin: 8px 0 0 0; font-size: 18px; font-weight: 400;">
                Sales Outreach Agent
            </h2>
            <p style="color: #94a3b8; margin: 12px 0 0 0; font-size: 14px;">
                Generate, compare, and score sales outreach emails using multi-agent AI
            </p>
        </div>
        """)
        
        # Input section
        with gr.Row():
            with gr.Column():
                prospect_input = gr.Textbox(
                    label="Describe the Prospect",
                    placeholder="Example: CEO of a 50-person marketing agency struggling with manual client reporting and looking to scale operations",
                    lines=4,
                    elem_id="prospect-input"
                )
                
                with gr.Row():
                    generate_btn = gr.Button(
                        "🎯 Generate Emails",
                        variant="primary",
                        scale=2
                    )
                    clear_btn = gr.Button(
                        "🗑️ Clear",
                        variant="secondary",
                        scale=1
                    )
        
        # Output section
        output_html = gr.HTML(
            value="""
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; 
                        padding: 40px; text-align: center; color: #94a3b8;">
                <p style="font-size: 16px; margin: 0;">
                    👆 Enter a prospect description and click <strong>Generate Emails</strong>
                </p>
                <p style="font-size: 14px; margin: 12px 0 0 0; color: #64748b;">
                    The AI will create multiple email drafts and score them automatically
                </p>
            </div>
            """
        )
        
        # Event handlers
        generate_btn.click(
            fn=run_sales_agent,
            inputs=prospect_input,
            outputs=output_html
        )
        
        clear_btn.click(
            fn=lambda: ("", """
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; 
                        padding: 40px; text-align: center; color: #94a3b8;">
                <p style="font-size: 16px; margin: 0;">
                    👆 Enter a prospect description and click <strong>Generate Emails</strong>
                </p>
            </div>
            """),
            inputs=[],
            outputs=[prospect_input, output_html]
        )
    
    return demo


def launch_gradio(share: bool = False):
    """Launch the Gradio application."""
    demo = create_gradio_app()
    demo.launch(
        server_port=settings.gradio_server_port,
        share=share or settings.gradio_share,
    )


if __name__ == "__main__":
    launch_gradio()
