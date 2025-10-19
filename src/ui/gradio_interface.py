"""
Complete Gradio user interface with STT and TTS support.
FIXED Browse Papers functionality with better error handling.
"""
import gradio as gr
import requests
from typing import Tuple, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
from src.core.config import settings
from src.core.logging_config import app_logger


class GradioUI:
    """Complete Gradio interface for RAG system with voice I/O."""
    
    def __init__(self, api_url: Optional[str] = None):
        """Initialize Gradio UI."""
        api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
        self.api_url = api_url or f"http://{api_host}:{settings.api_port}"
        app_logger.info(f"Gradio UI initialized with API URL: {self.api_url}")
        
        self._whisper_model = None
        self.audio_dir = Path(tempfile.gettempdir()) / "research_paper_audio"
        self.audio_dir.mkdir(exist_ok=True)
        
        self._check_api_health()
    
    def _check_api_health(self) -> bool:
        """Check if API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                app_logger.info("✅ API is healthy")
                return True
            else:
                app_logger.warning(f"⚠️ API returned status: {response.status_code}")
                return False
        except Exception as e:
            app_logger.error(f"❌ Cannot connect to API: {e}")
            return False
    
    def transcribe_audio_simple(self, audio_file) -> str:
        """Transcribe audio using Whisper."""
        if audio_file is None:
            return ""
        
        try:
            import whisper
            import os
            
            if not isinstance(audio_file, str):
                return ""
            
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                return ""
            
            if self._whisper_model is None:
                self._whisper_model = whisper.load_model("base")
            
            result = self._whisper_model.transcribe(audio_file, language="en")
            
            if result and isinstance(result, dict) and "text" in result:
                text = result["text"].strip()
                app_logger.info(f"✅ Transcribed: {text}")
                return text
            return ""
            
        except Exception as e:
            app_logger.error(f"Transcription error: {e}")
            return ""
    
    def synthesize_speech(self, text: str) -> Optional[str]:
        """Convert text to speech using gTTS."""
        if not text or not text.strip():
            return None
        
        try:
            from gtts import gTTS
            
            clean_text = text.replace("**", "").replace("*", "").replace("#", "")
            clean_text = clean_text.replace("\n\n", ". ").replace("\n", " ")
            clean_text = " ".join(clean_text.split())
            
            if len(clean_text) > 2000:
                truncated = clean_text[:2000]
                last_period = truncated.rfind('. ')
                if last_period > 1500:
                    clean_text = truncated[:last_period + 1]
                else:
                    clean_text = truncated
                clean_text += " For more details, please read the full text on screen."
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.audio_dir / f"answer_{timestamp}.mp3"
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            tts.save(str(output_file))
            
            app_logger.info(f"✅ Speech synthesized")
            return str(output_file)
            
        except Exception as e:
            app_logger.error(f"TTS error: {e}")
            return None
    
    def ask_question(
        self,
        question: str,
        audio_input,
        top_k: int,
        use_cache: bool,
        categories: str,
        enable_tts: bool
    ) -> Tuple[str, str, str, Optional[str]]:
        """Send question to API and format response with optional TTS."""
        try:
            if audio_input is not None:
                transcribed = self.transcribe_audio_simple(audio_input)
                if transcribed:
                    question = transcribed
            
            if not question or not question.strip():
                return "❌ Please enter a question or record audio.", "", "", None
            
            payload = {"question": question, "top_k": top_k, "use_cache": use_cache}
            if categories and categories.strip():
                payload["filter_categories"] = [c.strip() for c in categories.split(",")]
            
            response = requests.post(f"{self.api_url}/api/qa", json=payload, timeout=120)
            
            if response.status_code != 200:
                return f"❌ API Error: {response.json().get('detail', 'Unknown error')}", "", "", None
            
            data = response.json()
            answer = f"**Answer:**\n\n{data.get('answer', 'No answer generated')}"
            
            if data.get('cache_hit'):
                answer = "🔄 **(Cached Result)**\n\n" + answer
            
            sources_md = self._format_sources(data.get('sources', []))
            metadata_md = self._format_metadata(data)
            
            audio_output = None
            if enable_tts:
                answer_text = data.get('answer', '')
                audio_output = self.synthesize_speech(answer_text)
            
            return answer, sources_md, metadata_md, audio_output
            
        except Exception as e:
            app_logger.error(f"UI Error: {e}", exc_info=True)
            return f"❌ Error: {str(e)}", "", "", None
    
    def search_papers(self, query: str, top_k: int, search_type: str) -> str:
        """Search papers."""
        try:
            if not query or not query.strip():
                return "❌ Please enter a search query."
            
            app_logger.info(f"🔍 Search: '{query}'")
            
            response = requests.post(
                f"{self.api_url}/api/search",
                json={"query": query, "top_k": top_k},
                timeout=60
            )
            
            if response.status_code != 200:
                return f"❌ Search Error: {response.json().get('detail', 'Unknown error')}"
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return f"No results found for: **{query}**"
            
            results_md = f"## 🔍 Search Results: *{query}*\n\n**Found {len(results)} results**\n\n---\n\n"
            
            for i, result in enumerate(results, 1):
                results_md += f"### {i}. {result.get('title', 'N/A')}\n\n"
                results_md += f"**arXiv ID:** {result.get('arxiv_id', 'N/A')}\n\n"
                
                authors = result.get('authors', [])
                if authors:
                    results_md += f"**Authors:** {', '.join(authors[:3])}"
                    if len(authors) > 3:
                        results_md += " *et al.*"
                    results_md += "\n\n"
                
                abstract = result.get('abstract', '')
                if abstract:
                    results_md += f"**Abstract:** {abstract[:300]}...\n\n"
                results_md += "---\n\n"
            
            return results_md
            
        except Exception as e:
            app_logger.error(f"Search error: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    def list_papers(self, limit: int, category: str) -> str:
        """List papers - COMPLETELY REWRITTEN WITH DETAILED DEBUGGING."""
        try:
            app_logger.info(f"=" * 60)
            app_logger.info(f"📋 LIST PAPERS REQUEST")
            app_logger.info(f"Limit: {limit}, Category: '{category}'")
            app_logger.info(f"API URL: {self.api_url}")
            
            # Build parameters
            params = {"limit": int(limit), "skip": 0}
            if category and category.strip():
                params["category"] = category.strip()
            
            app_logger.info(f"Request params: {params}")
            
            # Make API call
            url = f"{self.api_url}/api/papers"
            app_logger.info(f"Calling: {url}")
            
            response = requests.get(url, params=params, timeout=30)
            
            app_logger.info(f"Response status code: {response.status_code}")
            app_logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check response status
            if response.status_code != 200:
                error_msg = f"❌ API returned status {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text[:200]}"
                app_logger.error(error_msg)
                return error_msg
            
            # Parse JSON response
            try:
                data = response.json()
                app_logger.info(f"Response data type: {type(data)}")
                app_logger.info(f"Response data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            except Exception as json_error:
                app_logger.error(f"Failed to parse JSON: {json_error}")
                app_logger.error(f"Response text: {response.text[:500]}")
                return f"❌ Failed to parse API response: {json_error}"
            
            # Extract papers
            if not isinstance(data, dict):
                app_logger.error(f"Response is not a dictionary: {type(data)}")
                return f"❌ Invalid response format"
            
            papers = data.get('papers', [])
            total = data.get('total', 0)
            
            app_logger.info(f"Papers in response: {len(papers)}")
            app_logger.info(f"Total in database: {total}")
            
            if not papers or len(papers) == 0:
                app_logger.warning(f"No papers in response even though total={total}")
                if total > 0:
                    return f"⚠️ Database has {total} papers but none were returned. Check API."
                else:
                    return "📭 No papers found in database."
            
            # Format papers
            app_logger.info(f"Formatting {len(papers)} papers...")
            
            papers_md = f"## 📚 Papers Database\n\n"
            papers_md += f"**Showing {len(papers)} of {total} papers**\n\n"
            papers_md += "---\n\n"
            
            for i, paper in enumerate(papers, 1):
                try:
                    title = paper.get('title', 'N/A')
                    arxiv_id = paper.get('arxiv_id', 'N/A')
                    authors = paper.get('authors', [])
                    categories = paper.get('categories', [])
                    pub_date = paper.get('published_date', '')
                    abstract = paper.get('abstract', '')
                    pdf_url = paper.get('pdf_url', '')
                    
                    papers_md += f"### {i}. {title}\n\n"
                    papers_md += f"**arXiv ID:** {arxiv_id}\n\n"
                    
                    if authors and isinstance(authors, list):
                        authors_str = ', '.join(authors[:3])
                        if len(authors) > 3:
                            authors_str += " *et al.*"
                        papers_md += f"**Authors:** {authors_str}\n\n"
                    
                    if categories and isinstance(categories, list):
                        papers_md += f"**Categories:** {', '.join(categories)}\n\n"
                    
                    if pub_date:
                        papers_md += f"**Published:** {pub_date[:10]}\n\n"
                    
                    if abstract:
                        papers_md += f"**Abstract:** {abstract[:250]}...\n\n"
                    
                    if pdf_url:
                        papers_md += f"[📄 View PDF]({pdf_url})\n\n"
                    
                    papers_md += "---\n\n"
                    
                except Exception as paper_error:
                    app_logger.error(f"Error formatting paper {i}: {paper_error}")
                    papers_md += f"### {i}. [Error formatting paper]\n\n---\n\n"
            
            app_logger.info(f"✅ Successfully formatted {len(papers)} papers")
            app_logger.info(f"=" * 60)
            
            return papers_md
            
        except requests.exceptions.Timeout:
            error = "⏱️ Request timed out"
            app_logger.error(error)
            return error
        except requests.exceptions.ConnectionError as e:
            error = f"❌ Cannot connect to API: {e}"
            app_logger.error(error)
            return error
        except Exception as e:
            error = f"❌ Unexpected error: {type(e).__name__}: {str(e)}"
            app_logger.error(error, exc_info=True)
            return error
    
    def get_system_stats(self) -> str:
        """Get system statistics."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code != 200:
                return "❌ Cannot retrieve stats"
            stats = response.json()
            stats_md = "## 📊 System Statistics\n\n"
            stats_md += f"- **Status:** {stats.get('status', 'Unknown')}\n"
            stats_md += f"- **Environment:** {stats.get('environment', 'Unknown')}\n"
            stats_md += f"- **Database:** {stats.get('database', 'Unknown')}\n"
            return stats_md
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_health_status(self) -> str:
        """Get health status."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code != 200:
                return "❌ Cannot retrieve health"
            health = response.json()
            health_md = "## ✅ System Health: **HEALTHY**\n\n"
            health_md += f"- **Status:** {health.get('status', 'Unknown')}\n"
            health_md += f"- **Database:** {health.get('database', 'Unknown')}\n"
            return health_md
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _format_sources(self, sources: List[dict]) -> str:
        """Format sources."""
        if not sources:
            return "No sources available."
        sources_md = "## 📚 Sources\n\n"
        for i, source in enumerate(sources, 1):
            sources_md += f"### [{i}] {source.get('title', 'N/A')}\n\n"
            sources_md += f"**arXiv ID:** {source.get('arxiv_id', 'N/A')}\n\n---\n\n"
        return sources_md
    
    def _format_metadata(self, data: dict) -> str:
        """Format metadata."""
        meta_md = "## ⚙️ Processing Details\n\n"
        meta_md += "- **Status:** Complete\n"
        meta_md += f"- **Model:** {settings.groq_model}\n"
        meta_md += f"- **Provider:** {settings.llm_provider}\n"
        meta_md += f"- **Keywords:** {data.get('keywords_used', 'N/A')}\n"
        return meta_md
    
    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface."""
        with gr.Blocks(title=settings.app_name, theme=gr.themes.Soft(primary_hue="purple")) as interface:
            
            gr.HTML(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;">
                <h1>📚 {settings.app_name}</h1>
                <p>Ask questions about AI research papers powered by RAG</p>
                <p><i>Version {settings.app_version} • 🎤 STT + 🔊 TTS Enabled</i></p>
            </div>
            """)
            
            with gr.Tabs():
                with gr.Tab("🤔 Ask Questions"):
                    gr.Markdown("### Ask questions with text OR voice • Get answers in text AND voice!")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            question_input = gr.Textbox(label="Type your question", placeholder="e.g., What are transformers?", lines=3)
                            gr.Markdown("**🎤 OR Record:**")
                            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Click to Record")
                            
                            with gr.Row():
                                top_k_slider = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Sources")
                                use_cache_check = gr.Checkbox(label="Cache", value=True)
                            
                            categories_input = gr.Textbox(label="Categories (optional)", placeholder="cs.AI", lines=1)
                            enable_tts_check = gr.Checkbox(label="🔊 Voice Output", value=False, info="2000 chars, ~4 min")
                            
                            submit_btn = gr.Button("🔍 ASK", variant="primary", size="lg")
                            clear_btn = gr.Button("Clear", variant="secondary")
                            
                            gr.Examples(
                                examples=[
                                    ["What are transformers?", 5, True, "", False],
                                    ["Explain attention", 5, True, "cs.AI", True],
                                ],
                                inputs=[question_input, top_k_slider, use_cache_check, categories_input, enable_tts_check],
                            )
                        
                        with gr.Column(scale=3):
                            answer_output = gr.Markdown(label="📝 Answer", value="*Answer here...*")
                            audio_output = gr.Audio(label="🔊 Listen", type="filepath")
                    
                    with gr.Row():
                        with gr.Column():
                            sources_output = gr.Markdown(label="📚 Sources", value="")
                        with gr.Column():
                            metadata_output = gr.Markdown(label="⚙️ Meta", value="")
                    
                    submit_btn.click(
                        fn=self.ask_question,
                        inputs=[question_input, audio_input, top_k_slider, use_cache_check, categories_input, enable_tts_check],
                        outputs=[answer_output, sources_output, metadata_output, audio_output]
                    )
                    clear_btn.click(
                        fn=lambda: ("", None, "", "", "", None),
                        outputs=[question_input, audio_input, answer_output, sources_output, metadata_output, audio_output]
                    )
                    question_input.submit(
                        fn=self.ask_question,
                        inputs=[question_input, audio_input, top_k_slider, use_cache_check, categories_input, enable_tts_check],
                        outputs=[answer_output, sources_output, metadata_output, audio_output]
                    )
                
                with gr.Tab("🔎 Search Papers"):
                    gr.Markdown("### Search papers")
                    with gr.Row():
                        with gr.Column(scale=1):
                            search_query = gr.Textbox(label="Query", placeholder="transformers", lines=2)
                            search_top_k = gr.Slider(minimum=1, maximum=50, value=10, step=1, label="Results")
                            search_type = gr.Radio(choices=["hybrid", "vector", "keyword"], value="hybrid", label="Type")
                            search_btn = gr.Button("🔍 Search", variant="primary", size="lg")
                        with gr.Column(scale=2):
                            search_results = gr.Markdown(label="Results", value="*Enter query...*")
                    search_btn.click(fn=self.search_papers, inputs=[search_query, search_top_k, search_type], outputs=search_results)
                
                with gr.Tab("📖 Browse Papers"):
                    gr.Markdown("### Browse all papers")
                    with gr.Row():
                        with gr.Column(scale=1):
                            list_limit = gr.Slider(minimum=5, maximum=100, value=20, step=5, label="Number")
                            list_category = gr.Textbox(label="Category", placeholder="cs.AI", lines=1)
                            list_btn = gr.Button("📋 LIST PAPERS", variant="primary", size="lg")
                        with gr.Column(scale=2):
                            papers_list = gr.Markdown(label="Papers", value="*Click LIST PAPERS...*")
                    list_btn.click(fn=self.list_papers, inputs=[list_limit, list_category], outputs=papers_list)
                
                with gr.Tab("⚙️ System"):
                    gr.Markdown("### System status")
                    with gr.Row():
                        stats_btn = gr.Button("📊 Stats", variant="primary")
                        health_btn = gr.Button("🏥 Health", variant="secondary")
                    with gr.Row():
                        with gr.Column():
                            stats_output = gr.Markdown(label="Stats", value="Click Stats")
                        with gr.Column():
                            health_output = gr.Markdown(label="Health", value="Click Health")
                    stats_btn.click(fn=self.get_system_stats, outputs=stats_output)
                    health_btn.click(fn=self.get_health_status, outputs=health_output)
            
            gr.HTML("""
            <div style="text-align: center; padding: 20px; color: #666;">
                <p>🎤 Whisper STT • 🔊 Google TTS (2000 chars)</p>
                <p>Built with ❤️ for AI Research</p>
            </div>
            """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch interface."""
        interface = self.create_interface()
        ui_port = getattr(settings, 'ui_port', 7860)
        ui_share = getattr(settings, 'ui_share', False)
        app_logger.info(f"🚀 Launching UI on port {ui_port}")
        interface.launch(server_name="0.0.0.0", server_port=ui_port, share=ui_share, **kwargs)


def main():
    """Main entry point."""
    ui = GradioUI()
    ui.launch()


if __name__ == "__main__":
    main()