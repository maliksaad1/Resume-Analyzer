import PyPDF2
import re
import io
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract
import fitz  # PyMuPDF
import logging
import unicodedata
import docx2txt
import pdf2docx
import tempfile
import os

class TextProcessor:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def extract_text(self, uploaded_file):
        """Extract text from various file formats"""
        file_type = uploaded_file.type
        self.logger.info(f"Processing file of type: {file_type}")
        
        try:
            if file_type == "application/pdf":
                return self.extract_text_from_pdf(uploaded_file)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self.extract_text_from_docx(uploaded_file)
            elif file_type == "text/plain":
                return uploaded_file.getvalue().decode()
            elif file_type == "application/msword":  # Old .doc format
                return self.extract_text_from_doc(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            self.logger.error(f"Text extraction failed: {str(e)}")
            raise

    def extract_text_from_pdf(self, uploaded_file):
        """Try multiple PDF extraction methods"""
        try:
            pdf_bytes = uploaded_file.read()
            text = ""
            
            # Try all PDF extraction methods
            extraction_methods = [
                self._extract_with_pymupdf,
                self._extract_with_pdfplumber,
                self._extract_with_pdfminer,
                self._extract_with_pypdf2
            ]
            
            for method in extraction_methods:
                try:
                    pdf_file = io.BytesIO(pdf_bytes)
                    text = method(pdf_file)
                    if text.strip():
                        return self.clean_extracted_text(text)
                except Exception as e:
                    self.logger.warning(f"{method.__name__} failed: {str(e)}")
                    continue
            
            # If all methods fail, try PDF to DOCX conversion
            if not text.strip():
                self.logger.info("Attempting PDF to DOCX conversion...")
                text = self._convert_pdf_to_docx_and_extract(pdf_bytes)
                if text.strip():
                    return self.clean_extracted_text(text)
            
            if not text.strip():
                raise ValueError("Could not extract text using any available method, including PDF to DOCX conversion.")
            
            return self.clean_extracted_text(text)
            
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {str(e)}")
            raise ValueError(f"Could not process PDF: {str(e)}")

    def _convert_pdf_to_docx_and_extract(self, pdf_bytes):
        """Convert PDF to DOCX and extract text"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "temp.pdf")
            docx_path = os.path.join(temp_dir, "temp.docx")
            
            # Save PDF bytes to temporary file
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Convert PDF to DOCX
            try:
                converter = pdf2docx.Converter(pdf_path)
                converter.convert(docx_path)
                converter.close()
                
                # Extract text from DOCX
                text = docx2txt.process(docx_path)
                return text
            except Exception as e:
                self.logger.error(f"PDF to DOCX conversion failed: {str(e)}")
                return ""

    def _extract_with_pymupdf(self, pdf_file):
        """Extract text using PyMuPDF"""
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _extract_with_pdfplumber(self, pdf_file):
        """Extract text using pdfplumber"""
        with pdfplumber.open(pdf_file) as pdf:
            return " ".join(page.extract_text() or "" for page in pdf.pages)

    def _extract_with_pdfminer(self, pdf_file):
        """Extract text using PDFMiner"""
        return pdfminer_extract(pdf_file)

    def _extract_with_pypdf2(self, pdf_file):
        """Extract text using PyPDF2"""
        reader = PyPDF2.PdfReader(pdf_file)
        return " ".join(page.extract_text() or "" for page in reader.pages)

    def extract_text_from_docx(self, uploaded_file):
        """Extract text from DOCX file"""
        try:
            # Save the uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # Extract text from the temporary file
            text = docx2txt.process(tmp_file_path)
            
            # Clean up
            os.unlink(tmp_file_path)
            
            return self.clean_extracted_text(text)
        except Exception as e:
            self.logger.error(f"DOCX extraction failed: {str(e)}")
            raise ValueError(f"Could not process DOCX: {str(e)}")

    def clean_extracted_text(self, text):
        """Clean the extracted text"""
        if not text:
            return ""
            
        try:
            # Remove Unicode control characters
            text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
            
            # Replace multiple newlines with single newline
            text = re.sub(r'\n\s*\n', '\n', text)
            
            # Replace multiple spaces with single space
            text = re.sub(r'\s+', ' ', text)
            
            # Remove leading/trailing whitespace
            text = text.strip()
            
            return text
        except Exception as e:
            self.logger.error(f"Text cleaning failed: {str(e)}")
            return text

    def preprocess_text(self, text):
        """Preprocess text for analysis"""
        if not text:
            raise ValueError("No text to process")
        
        try:
            # Basic cleaning
            cleaned_text = self.clean_extracted_text(text)
            
            # Remove special characters but keep important punctuation
            cleaned_text = re.sub(r'[^\w\s\-\.,;:]', ' ', cleaned_text)
            
            # Normalize whitespace
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            # Log the length of processed text
            self.logger.info(f"Processed text length: {len(cleaned_text)}")
            
            return cleaned_text
        except Exception as e:
            self.logger.error(f"Text preprocessing failed: {str(e)}")
            raise ValueError(f"Failed to preprocess text: {str(e)}")