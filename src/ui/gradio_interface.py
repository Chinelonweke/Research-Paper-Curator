"""
Research Paper Curator UI - WITH ASK QUESTION + TTS/STT
"""
import gradio as gr
import requests
import os

API_HOST = os.getenv("API_HOST", "http://localhost:8000")
API_HOST = API_HOST.rstrip('/')

print(f"="*70)
print(f"🔗 API URL: {API_HOST}")
print(f"="*70)

def search_papers(query, limit, search_type):
    """Search papers"""
    if not query:
        return "⚠️ Please enter a search query."
    
    try:
        url = f"{API_HOST}/papers/search"
        response = requests.post(
            url,
            json={"query": query, "limit": limit, "search_type": search_type},
            timeout=60
        )
        
        if response.status_code != 200:
            return f"❌ API Error: Status {response.status_code}"
        
        result = response.json()
        papers = result.get("papers", [])
        
        if not papers:
            return f"📭 No papers found for '{query}'"
        
        html = f"""
        <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>Found {len(papers)} papers</h2>
        </div>
        """
        
        for i, paper in enumerate(papers, 1):
            html += f"""
            <div style='border: 2px solid #8b5cf6; padding: 20px; margin: 15px 0; border-radius: 10px; background: #f5f3ff;'>
                <h3 style='color: #6b46c1;'>{i}. {paper.get('title', 'No title')}</h3>
                <p style='color: #7c3aed;'><strong>Authors:</strong> {paper.get('authors', 'Unknown')}</p>
                <p style='color: #1f2937;'>{paper.get('abstract', '')[:500]}...</p>
                <a href="{paper.get('url', '#')}" target="_blank" style='color: #8b5cf6; font-weight: 600;'>📄 View Paper →</a>
            </div>
            """
        
        return html
        
    except requests.exceptions.ConnectionError:
        return f"❌ Cannot connect to API at {API_HOST}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def ask_question(text_question, audio_question):
    """Ask question with text or audio - WITH TTS RESPONSE"""
    question = text_question
    
    if audio_question is not None:
        # TODO: Add speech-to-text processing
        question = text_question if text_question else "Audio processing not yet implemented"
    
    if not question:
        return "⚠️ Please enter a question or record audio.", None
    
    try:
        url = f"{API_HOST}/ask"
        response = requests.post(
            url,
            json={"question": question},
            timeout=120
        )
        
        if response.status_code == 404:
            return """⚠️ Ask endpoint not yet implemented on API.

For now, try searching for papers related to your question!""", None
        
        if response.status_code != 200:
            return f"❌ API Error: Status {response.status_code}", None
        
        result = response.json()
        answer = result.get("answer", "No answer")
        sources = result.get("sources", [])
        audio_url = result.get("audio_url")
        
        # Format answer
        formatted_answer = answer.replace('\n', '<br>')
        
        html = f"""
        <div style='padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>💡 Answer</h2>
            <p style='color: #e0e7ff; font-size: 14px;'>Question: "{question}"</p>
        </div>
        
        <div style='background: white; padding: 25px; border-radius: 10px; border-left: 6px solid #8b5cf6; margin-bottom: 20px;'>
            <div style='color: #1f2937; line-height: 1.8;'>
                {formatted_answer}
            </div>
        </div>
        
        <div style='background: #f5f3ff; padding: 20px; border-radius: 10px; border: 2px solid #c4b5fd;'>
            <h3 style='color: #6b46c1; margin-top: 0;'>📚 Sources</h3>
            <ul style='color: #553c9a;'>
        """
        
        for source in sources:
            html += f"<li>{source}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        # Handle audio
        audio_file = None
        if audio_url:
            try:
                audio_file_url = f"{API_HOST}{audio_url}"
                audio_response = requests.get(audio_file_url, timeout=10)
                if audio_response.status_code == 200:
                    import tempfile
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_audio.write(audio_response.content)
                    temp_audio.close()
                    audio_file = temp_audio.name
            except:
                pass
        
        return html, audio_file
        
    except requests.exceptions.ConnectionError:
        return f"❌ Cannot connect to API at {API_HOST}", None
    except Exception as e:
        return f"❌ Error: {str(e)}", None

def browse_papers(limit):
    """Browse papers"""
    try:
        response = requests.get(f"{API_HOST}/papers?limit={limit}", timeout=30)
        
        if response.status_code != 200:
            return f"❌ Error: {response.status_code}"
        
        result = response.json()
        papers = result.get("papers", [])
        
        html = f"""
        <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px;'>
            <h2 style='color: white;'>📚 {len(papers)} Papers</h2>
        </div>
        """
        
        for i, paper in enumerate(papers, 1):
            html += f"""
            <div style='border: 2px solid #c4b5fd; padding: 18px; margin: 12px 0; border-radius: 8px; background: white;'>
                <h3 style='color: #6b46c1;'>{i}. {paper.get('title', 'No title')}</h3>
                <p style='color: #7c3aed;'><strong>Authors:</strong> {paper.get('authors', 'Unknown')}</p>
                <p style='color: #4b5563;'>{paper.get('abstract', '')[:250]}...</p>
                <a href="{paper.get('url', '#')}" target="_blank" style='color: #8b5cf6;'>View Paper →</a>
            </div>
            """
        
        return html
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def check_status():
    """Check API status"""
    try:
        response = requests.get(f"{API_HOST}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return f"""✅ All Systems Operational!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Status: {data.get('status', 'unknown').upper()}
Database: {data.get('database', 'unknown')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 API URL: {API_HOST}
Status: Connected ✅
"""
        else:
            return f"⚠️ API status {response.status_code}"
            
    except Exception as e:
        return f"""❌ Cannot connect to API

URL: {API_HOST}
Error: {str(e)}

Check: docker ps
"""

custom_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.purple,
    secondary_hue=gr.themes.colors.violet,
)

with gr.Blocks(title="Research Paper Curator", theme=custom_theme) as app:
    
    gr.HTML("""
        <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; color: white; margin-bottom: 30px;'>
            <h1 style='font-size: 42px; margin: 0;'>📚 Research Paper Curator</h1>
            <p style='font-size: 18px; margin: 10px 0;'>Ask questions about AI research papers powered by RAG</p>
            <p style='font-size: 14px;'>Version 1.0.0 • 🎤 TTS/STT Enabled</p>
        </div>
    """)
    
    with gr.Tabs():
        
        with gr.Tab("🔍 Search Papers"):
            gr.Markdown("### Search with Hybrid, Vector, or Keyword methods")
            
            search_query = gr.Textbox(
                label="Search Query",
                placeholder="e.g., 'large language models', 'transformers'",
                lines=2
            )
            
            with gr.Row():
                search_type = gr.Radio(
                    choices=["hybrid", "vector", "keyword"],
                    value="hybrid",
                    label="Search Type"
                )
                search_limit = gr.Slider(5, 50, 10, step=5, label="Results")
            
            search_btn = gr.Button("🔍 Search Papers", variant="primary", size="lg")
            search_output = gr.HTML()
            
            search_btn.click(
                fn=search_papers,
                inputs=[search_query, search_limit, search_type],
                outputs=search_output
            )
        
        with gr.Tab("❓ Ask Questions"):
            gr.Markdown("### Ask with text OR voice • Get answers in text AND voice!")
            gr.Markdown("⏱️ **Note:** May take 30-60 seconds for complex questions")
            
            with gr.Row():
                with gr.Column(scale=2):
                    question_text = gr.Textbox(
                        label="💬 Type your question",
                        placeholder="e.g., What are transformers? How do they work?",
                        lines=3
                    )
                with gr.Column(scale=1):
                    question_audio = gr.Audio(
                        label="🎤 OR Record",
                        sources=["microphone"],
                        type="filepath"
                    )
            
            ask_btn = gr.Button("❓ Get Answer", variant="primary", size="lg")
            
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column(scale=3):
                    answer_html = gr.HTML(label="Answer")
                with gr.Column(scale=1):
                    answer_audio = gr.Audio(
                        label="🔊 Listen",
                        type="filepath"
                    )
            
            ask_btn.click(
                fn=ask_question,
                inputs=[question_text, question_audio],
                outputs=[answer_html, answer_audio]
            )
        
        with gr.Tab("📚 Browse Papers"):
            gr.Markdown("### Browse all papers in the database")
            
            browse_limit = gr.Slider(10, 100, 20, step=10, label="Papers")
            browse_btn = gr.Button("📚 Load Papers", variant="primary", size="lg")
            browse_output = gr.HTML()
            
            browse_btn.click(
                fn=browse_papers,
                inputs=browse_limit,
                outputs=browse_output
            )
        
        with gr.Tab("⚙️ System"):
            gr.Markdown("### System Status")
            
            status_btn = gr.Button("🏥 Check Status", variant="secondary", size="lg")
            status_output = gr.Textbox(label="Status", lines=15)
            
            status_btn.click(fn=check_status, outputs=status_output)

if __name__ == "__main__":
    print("="*70)
    print("🚀 Research Paper Curator UI")
    print(f"📡 API: {API_HOST}")
    print("🎤 TTS/STT: Enabled")
    print("="*70)
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )