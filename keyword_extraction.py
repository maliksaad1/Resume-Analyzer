import google.generativeai as genai
from typing import Dict
import json

class KeywordExtractor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def analyze_match(self, resume_text: str, job_desc: str) -> str:
        prompt = """
        You are a professional resume analyzer and ATS (Applicant Tracking System) expert. Analyze the provided resume and job description with extreme attention to detail. Follow these strict guidelines:

        1. Job Description Analysis:
        - Extract ALL required skills, qualifications, and experience levels
        - Identify primary (must-have) vs secondary (nice-to-have) requirements
        - Note specific certifications, education requirements, and years of experience
        - Consider industry-specific terminology and standards

        2. Resume Analysis:
        - Extract ALL skills, qualifications, and experiences mentioned
        - Check for proper keyword placement and density
        - Evaluate formatting and structure for ATS readability
        - Look for quantifiable achievements and metrics

        3. Detailed Comparison:
        - Exact matches (case-insensitive)
        - Related/similar terms (e.g., "Python" matches "Python programming")
        - Experience level alignment
        - Education and certification matches
        - Industry-specific terminology usage

        4. Calculate match percentage based on:
        - Presence of primary requirements (weighted 70%)
        - Presence of secondary requirements (weighted 30%)
        - Proper keyword placement and context
        - Experience level alignment
        - Overall qualification match

        5. ATS Compatibility Analysis:
        - Format and structure (20% of score)
        - Keyword density and placement (30% of score)
        - Use of standard section headings (15% of score)
        - Proper formatting and special characters (15% of score)
        - File type and parsing compatibility (20% of score)

        RESUME:
        {}

        JOB DESCRIPTION:
        {}

        Return ONLY a JSON object with these fields:
        {{
            "match_percentage": <calculated based on weighted requirements>,
            "matching_keywords": ["keyword1 (with context)", "keyword2 (with context)", ...],
            "missing_keywords": ["missing1 (importance level)", "missing2 (importance level)", ...],
            "suggestions": [
                "specific actionable suggestion1",
                "specific actionable suggestion2",
                ...
            ],
            "ats_compatibility": {{
                "score": <calculated based on multiple factors>,
                "will_pass_ats": <boolean based on score threshold of 75>,
                "issues": [
                    "specific formatting issue1",
                    "specific keyword placement issue2",
                    ...
                ],
                "improvements": [
                    "specific actionable improvement1",
                    "specific actionable improvement2",
                    ...
                ]
            }}
        }}

        Rules for scoring:
        1. Match percentage must reflect actual alignment with job requirements
        2. ATS score must consider all formatting and keyword placement factors
        3. Suggestions must be specific and actionable
        4. Issues must identify exact problems in the resume
        5. Each score must be justified by specific findings
        6. Consider industry standards and best practices
        """.format(resume_text, job_desc)

        try:
            # Set temperature to 0.1 for slight variation while maintaining consistency
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Slight randomness for more natural variation
                    top_p=0.8,       # More focused on likely responses
                    top_k=40,        # Allow for more variation in word choice
                    candidate_count=1
                )
            )
        
            
            # Clean and validate response
            cleaned_response = response.text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3]
            
            # Validate JSON structure
            parsed_json = json.loads(cleaned_response)
            
            # Additional validation
            required_fields = ['match_percentage', 'matching_keywords', 'missing_keywords', 
                            'suggestions', 'ats_compatibility']
            for field in required_fields:
                if field not in parsed_json:
                    raise ValueError(f"Missing required field: {field}")
                
            if not isinstance(parsed_json['match_percentage'], (int, float)):
                raise ValueError("match_percentage must be a number")
                
            if parsed_json['match_percentage'] < 0 or parsed_json['match_percentage'] > 100:
                raise ValueError("match_percentage must be between 0 and 100")
            
            # Validate ATS compatibility structure
            ats_fields = ['score', 'will_pass_ats', 'issues', 'improvements']
            for field in ats_fields:
                if field not in parsed_json['ats_compatibility']:
                    raise ValueError(f"Missing ATS compatibility field: {field}")
            
            return cleaned_response
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from model: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error in analysis: {str(e)}")