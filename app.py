import streamlit as st
import json
from pathlib import Path
from text_processing import TextProcessor
from keyword_extraction import KeywordExtractor
import os
from dotenv import load_dotenv

class ResumeAnalyzer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize with Google API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in .env file")
            
        self.keyword_extractor = KeywordExtractor(api_key)
        self.text_processor = TextProcessor()

    def analyze_resume(self, resume_text: str, job_desc: str):
        try:
            # Perform analysis
            result_str = self.keyword_extractor.analyze_match(resume_text, job_desc)
            return json.loads(result_str)
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")

def main():
    st.set_page_config(
        page_title="Match My Resume",
        page_icon="📄",
        layout="wide"
    )

    # Initialize the analyzer
    analyzer = ResumeAnalyzer()

    # Title
    st.title("Smart Job Matching: See How Well Your Resume Fits")
    st.markdown("---")

    # Create two columns
    col1, col2 = st.columns([1, 1])

    with col1:
        # File upload section
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Supported formats: PDF, DOCX, DOC, TXT"
        )
        
        # Create a placeholder for messages right after file upload
        message_placeholder = st.empty()
        
        if uploaded_file:
            try:
                with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                    text = analyzer.text_processor.extract_text(uploaded_file)
                
                # Process text and store in session state
                processed_text = analyzer.text_processor.preprocess_text(text)
                st.session_state['resume_text'] = processed_text
                
                # Success message before job description
                message_placeholder.success("Text extraction successful!")
                
                # Job Description
                st.subheader("Job Description")
                job_desc = st.text_area("Enter the job description", height=200)
                
                # Show extraction details after job description
                st.info(f"Extracted {len(text)} characters")
                
                # Show extracted text after job description
                st.subheader("Extracted Text")
                with st.expander("View Extracted Text", expanded=False):
                    st.text_area("", processed_text, height=200)
                    st.info(f"Processed text length: {len(processed_text)} characters")
                
            except Exception as e:
                # Clear any previous content in the placeholder
                message_placeholder.empty()
                # Display error messages before job description
                with message_placeholder.container():
                    st.error(f"Error processing file: {str(e)}")
                    st.warning("Please try uploading a different file or save it as a text file. If the issue persists, ensure the file is not corrupted.")
                
                # Job Description after error messages
                st.subheader("Job Description")
                job_desc = st.text_area("Enter the job description", height=200)
        
        else:
            # Job Description when no file is uploaded
            st.subheader("Job Description")
            job_desc = st.text_area("Enter the job description", height=200)

    with col2:
        # Analysis Results
        st.subheader("Analysis Results")
        
        if st.button("Analyze Match", type="primary"):
            if not uploaded_file:
                st.error("Please upload a resume first")
            elif not job_desc:
                st.error("Please enter a job description")
            else:
                try:
                    with st.spinner("Analyzing..."):
                        analysis = analyzer.analyze_resume(st.session_state['resume_text'], job_desc)
                    
                    # Display results
                    col2_1, col2_2 = st.columns(2)
                    
                    with col2_1:
                        st.metric("Match Percentage", f"{analysis['match_percentage']}%")
                        st.progress(analysis['match_percentage'] / 100)
                    
                    with col2_2:
                        ats_score = analysis['ats_compatibility']['score']
                        will_pass = analysis['ats_compatibility']['will_pass_ats']
                        st.metric(
                            "ATS Compatibility", 
                            f"{ats_score}%",
                            delta="Will Pass ✅" if will_pass else "Needs Improvement ⚠️"
                        )
                        st.progress(ats_score / 100)
                    
                    # Keywords and Suggestions
                    with st.expander("Matching Keywords", expanded=True):
                        st.write(", ".join(analysis['matching_keywords']))
                    
                    with st.expander("Missing Keywords", expanded=True):
                        st.write(", ".join(analysis['missing_keywords']))
                    
                    with st.expander("Improvement Suggestions", expanded=True):
                        for suggestion in analysis['suggestions']:
                            st.write(f"• {suggestion}")
                    
                    # ATS-specific feedback
                    with st.expander("ATS Optimization", expanded=True):
                        # if analysis['ats_compatibility']['issues']:
                        #     st.subheader("Issues Detected")
                        #     for issue in analysis['ats_compatibility']['issues']:
                        #         st.write(f"⚠️ {issue}")
                        
                        st.subheader("Recommended Checks")
                        for improvement in analysis['ats_compatibility']['improvements']:
                            st.write(f"📝 {improvement}")
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()
