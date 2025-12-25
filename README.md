# TMP AI Sales Outreach Agent

**An intelligent, agentic workflow for generating high-performance cold outreach emails.**

This project uses a multi-agent system to draft, evaluate, and optimize sales emails. Instead of relying on a single prompt, it orchestrates three distinct AI personas to generate options, then uses a **Hybrid Scoring System** (Rule-Based + LLM Judge) to mathematically determine the best draft.

## 🚀 Key Features

*   **Multi-Persona Generation**: Simultaneously generates drafts using three specialized agents:
    *   **👔 Professional**: Focuses on value, efficiency, and ROI.
    *   **💡 Engaging**: Uses pattern interrupts, humor, and a conversational tone.
    *   **⚡ Concise**: Ultra-short, bullet-point style for busy executives.
*   **Hybrid Scoring Engine**:
    *   **Rule-Based**: Checks for objective metrics like word count, "you" vs "I" ratio, value keywords, and formatting.
    *   **LLM Judge**: A separate agent evaluates persuasiveness, tone, and clarity.
*   **Cost Tracking**: Monitors and analyzes the estimated API cost per run.
*   **Interactive UI**: Built with **Gradio** for a clean, card-based user interface to test and display results.

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Terry-Mathew/Sales-Outreach-Agent.git
    cd Sales-Outreach-Agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables:**
    Create a `.env` file in the root directory and add your OpenAI API key:
    ```env
    OPENAI_API_KEY=sk-...
    ```

## 🖥️ Usage

Run the Gradio application:

```bash
python app.py
```

Open the provided local URL (usually `http://127.0.0.1:7860`) in your browser.

1.  Enter a description of your prospect (e.g., *"CEO of a marketing agency looking to automate workflows"*).
2.  Click **Generate Emails**.
3.  The system will display the **winning draft**, along with the scores and content for all generated options.

## 📂 Project Structure

*   `app.py`: The entry point. Handles the Gradio UI and invokes the agent pipeline.
*   `tmpai_sales_agent.py`: Contains the core logic:
    *   Agent definitions (Professional, Engaging, Concise).
    *   `QualityScorer` class (Rule-based logic).
    *   `email_judge` (LLM evaluator).
    *   Orchestration logic (`run_tmpai_sales`).
*   `requirements.txt`: Python dependencies.

## 🧠 How It Works

1.  **Drafting**: The Orchestrator sends the prompt to all three SDR Agents in parallel.
2.  **Rule Scoring**: Each draft is analyzed for structure, length, and keywords using Python logic.
3.  **LLM Scoring**: The "Search & Judge" agent reviews the draft for qualitative nuances.
4.  **Selection**: A final weighted score (40% Rules / 60% LLM) determines the winner.
