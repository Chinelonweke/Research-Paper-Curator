"""Test Gradio UI."""
import gradio as gr
import requests

print("=" * 60)
print("🎨 TESTING GRADIO UI")
print("=" * 60)

# Test API connection
def test_api():
    """Test if API is reachable."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            return "✅ API is running!", response.json()
        else:
            return "❌ API returned error", response.status_code
    except Exception as e:
        return "❌ Cannot reach API. Is it running?", str(e)


def ask_question(question):
    """Send question to API."""
    if not question:
        return "Please enter a question."
    
    try:
        # For now, just echo back since Q&A not implemented yet
        return f"Question received: {question}\n\n(Q&A endpoint not yet implemented in API)"
    except Exception as e:
        return f"Error: {str(e)}"


def search_papers(query):
    """Search papers."""
    if not query:
        return "Please enter a search query."
    
    try:
        response = requests.post(
            "http://localhost:8000/api/search",
            json={"query": query}
        )
        return f"Search results for: {query}\n\n{response.json()}"
    except Exception as e:
        return f"Error: {str(e)}"


# Check API before starting UI
print("\n1️⃣ Checking API connection...")
api_status, api_data = test_api()
print(f"   {api_status}")
if isinstance(api_data, dict):
    print(f"   Environment: {api_data.get('environment')}")
    print(f"   Database: {api_data.get('database')}")

print("\n2️⃣ Starting Gradio UI...")
print("   URL will open in your browser automatically")

# Create Gradio interface
with gr.Blocks(title="Research Paper Curator") as demo:
    gr.Markdown("# 📚 Research Paper Curator")
    gr.Markdown("### RAG-based Research Paper Q&A System")
    
    with gr.Tab("❓ Ask Questions"):
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="Ask anything about research papers...",
            lines=3
        )
        question_btn = gr.Button("Ask", variant="primary")
        question_output = gr.Textbox(label="Answer", lines=10)
        
        question_btn.click(
            fn=ask_question,
            inputs=question_input,
            outputs=question_output
        )
    
    with gr.Tab("🔍 Search Papers"):
        search_input = gr.Textbox(
            label="Search Query",
            placeholder="Enter keywords to search papers...",
            lines=2
        )
        search_btn = gr.Button("Search", variant="primary")
        search_output = gr.Textbox(label="Results", lines=10)
        
        search_btn.click(
            fn=search_papers,
            inputs=search_input,
            outputs=search_output
        )
    
    with gr.Tab("ℹ️ System Info"):
        info_btn = gr.Button("Check API Status")
        info_output = gr.Textbox(label="Status", lines=5)
        
        info_btn.click(
            fn=lambda: str(test_api()),
            outputs=info_output
        )
    
    gr.Markdown("---")
    gr.Markdown("**Status:** API running on http://localhost:8000")

print("\n" + "=" * 60)
print("🎉 LAUNCHING UI!")
print("=" * 60)

# Launch UI
demo.launch(
    server_port=7860,
    share=False,
    show_error=True
)