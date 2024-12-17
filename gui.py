import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from text_processing import TextProcessor
from keyword_extraction import KeywordExtractor
import json
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

class ModernButton(ttk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(style='Modern.TButton')

class ResumeAnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Resume Keyword Analyzer")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Load environment variables
        load_dotenv()
        
        # Initialize with Google API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in .env file")
            
        self.keyword_extractor = KeywordExtractor(api_key)
        self.text_processor = TextProcessor()
        
        # Configure styles
        self.setup_styles()
        self.setup_gui()

    def setup_styles(self):
        # Configure modern styles
        style = ttk.Style()
        style.configure('Modern.TButton',
                       padding=10,
                       font=('Helvetica', 10))
        
        style.configure('Title.TLabel',
                       font=('Helvetica', 16, 'bold'),
                       padding=10,
                       background='#f0f0f0')
                       
        style.configure('Subtitle.TLabel',
                       font=('Helvetica', 12),
                       padding=5,
                       background='#f0f0f0')
                       
        style.configure('Results.TLabel',
                       font=('Helvetica', 11),
                       padding=5,
                       background='#ffffff')

    def setup_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_container, 
                         text="Resume Keyword Analyzer",
                         style='Title.TLabel')
        title.pack(pady=(0, 20))

        # Left Panel (Upload and Job Description)
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Upload Section
        upload_frame = ttk.LabelFrame(left_panel, text="Resume Upload", padding=10)
        upload_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_label = ttk.Label(upload_frame, 
                                  text="No file selected",
                                  style='Subtitle.TLabel')
        self.file_label.pack(pady=5)
        
        ModernButton(upload_frame, 
                    text="Upload Resume",
                    command=self.upload_resume).pack(pady=5)
        
        # Job Description Section
        jd_frame = ttk.LabelFrame(left_panel, text="Job Description", padding=10)
        jd_frame.pack(fill=tk.BOTH, expand=True)
        
        self.jd_text = ScrolledText(jd_frame, 
                                  height=10,
                                  font=('Helvetica', 10),
                                  wrap=tk.WORD)
        self.jd_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ModernButton(left_panel,
                    text="Analyze Match",
                    command=self.analyze).pack(pady=20)

        # Right Panel (Results)
        self.results_frame = ttk.LabelFrame(main_container, 
                                          text="Analysis Results",
                                          padding=10)
        self.results_frame.pack(side=tk.RIGHT,
                              fill=tk.BOTH,
                              expand=True,
                              padx=(10, 0))
        
        # Initial message in results
        self.initial_msg = ttk.Label(self.results_frame,
                                   text="Upload a resume and enter job description to see analysis",
                                   style='Subtitle.TLabel',
                                   wraplength=300)
        self.initial_msg.pack(pady=20)

    def upload_resume(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt")]
        )
        if file_path:
            try:
                file_name = Path(file_path).name
                self.file_label.config(text=f"Selected: {file_name}")
            
                # Extract and preprocess text
                if file_path.endswith('.pdf'):
                    self.resume_text = self.text_processor.extract_text_from_pdf(file_path)
                else:
                    with open(file_path, 'r') as file:
                        self.resume_text = file.read()
                
                self.resume_text = self.text_processor.preprocess_text(self.resume_text)
                
                # Show extracted text in a new window
                self.show_extracted_text(self.resume_text)
                
                messagebox.showinfo("Success", "Resume uploaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process file: {str(e)}")
    
    def show_extracted_text(self, text):
        # Create a new window
        text_window = tk.Toplevel(self.root)
        text_window.title("Extracted Resume Text")
        text_window.geometry("600x400")
        
        # Add text area
        text_area = ScrolledText(text_window, wrap=tk.WORD, width=60, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Insert text
        text_area.insert("1.0", "=== Extracted Resume Text ===\n\n")
        text_area.insert(tk.END, text)
        
        # Add confirmation button
        def confirm():
            if messagebox.askyesno("Confirm", "Is the extracted text correct?"):
                text_window.destroy()
            else:
                messagebox.showwarning("Warning", 
                    "Please try uploading the file again or use a different format")
                self.resume_text = None
                self.file_label.config(text="No file selected")
                text_window.destroy()
        
        ttk.Button(text_window, 
                  text="Confirm Text", 
                  command=confirm).pack(pady=10)

    def display_results(self, analysis):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Create results container with white background
        results_container = ttk.Frame(self.results_frame)
        results_container.pack(fill=tk.BOTH, expand=True)
        
        # Match Percentage with progress bar
        match_frame = ttk.Frame(results_container)
        match_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(match_frame,
                 text="Match Percentage:",
                 style='Subtitle.TLabel').pack(side=tk.LEFT, padx=5)
        
        progress = ttk.Progressbar(match_frame,
                                 length=200,
                                 mode='determinate')
        progress.pack(side=tk.LEFT, padx=5)
        progress['value'] = analysis['match_percentage']
        
        ttk.Label(match_frame,
                 text=f"{analysis['match_percentage']}%",
                 style='Subtitle.TLabel').pack(side=tk.LEFT, padx=5)
        
        # Matching Keywords
        keyword_frame = ttk.LabelFrame(results_container, text="Matching Keywords", padding=10)
        keyword_frame.pack(fill=tk.X, pady=10)
        
        keywords_text = ScrolledText(keyword_frame, height=3, wrap=tk.WORD)
        keywords_text.insert("1.0", ", ".join(analysis['matching_keywords']))
        keywords_text.config(state='disabled')
        keywords_text.pack(fill=tk.X)
        
        # Missing Keywords
        missing_frame = ttk.LabelFrame(results_container, text="Missing Keywords", padding=10)
        missing_frame.pack(fill=tk.X, pady=10)
        
        missing_text = ScrolledText(missing_frame, height=3, wrap=tk.WORD)
        missing_text.insert("1.0", ", ".join(analysis['missing_keywords']))
        missing_text.config(state='disabled')
        missing_text.pack(fill=tk.X)
        
        # Suggestions
        suggestions_frame = ttk.LabelFrame(results_container, text="Improvement Suggestions", padding=10)
        suggestions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        suggestions_text = ScrolledText(suggestions_frame, wrap=tk.WORD)
        suggestions_text.insert("1.0", "\n".join(analysis['suggestions']))
        suggestions_text.config(state='disabled')
        suggestions_text.pack(fill=tk.BOTH, expand=True)

    def analyze(self):
        if not hasattr(self, 'resume_text'):
            messagebox.showerror("Error", "Please upload a resume first")
            return
            
        job_desc = self.jd_text.get("1.0", tk.END).strip()
        if not job_desc:
            messagebox.showerror("Error", "Please enter a job description")
            return
        
        try:
            # Show loading message
            for widget in self.results_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.results_frame,
                     text="Analyzing...",
                     style='Subtitle.TLabel').pack(pady=20)
            self.root.update()
            
            # Perform analysis
            result_str = self.keyword_extractor.analyze_match(self.resume_text, job_desc)
            analysis = json.loads(result_str)
            
            # Display results
            self.display_results(analysis)
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def run(self):
        self.root.mainloop()