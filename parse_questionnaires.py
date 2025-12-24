"""
Improved PDF Questionnaire Parser using pdfplumber
Extracts actual questions from Google Forms PDFs
"""

import os
import re
import json
from typing import List, Dict, Any
import pdfplumber


class ImprovedQuestionnaireParser:
    """Improved parser that extracts actual questions from PDFs."""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = text.strip()
        return text
    
    def find_questions(self, text: str) -> List[Dict[str, Any]]:
        """Find and extract questions from text."""
        questions = []
        seen_questions = set()
        question_id = 1
        
        # Split text into lines for better processing
        lines = text.split('\n')
        
        # Patterns to identify questions
        # 1. Lines ending with question mark
        # 2. Numbered questions (1., 2., etc.)
        # 3. Questions starting with common question words
        
        current_question = None
        current_options = []
        collecting_options = False
        
        for i, line in enumerate(lines):
            line = self.clean_text(line)
            if not line or len(line) < 5:
                continue
            
            # Check if this is a question (ends with ? or starts with question pattern)
            is_question = False
            question_text = None
            
            # Pattern 1: Ends with question mark
            if '?' in line:
                # Extract the question part
                q_match = re.search(r'(.+?\?)', line)
                if q_match:
                    question_text = q_match.group(1).strip()
                    is_question = True
            
            # Pattern 2: Numbered question (1., 2., etc.)
            numbered_match = re.match(r'^(\d+)[\.\)]\s*(.+?)(\?|$)', line, re.IGNORECASE)
            if numbered_match and not is_question:
                question_text = numbered_match.group(2).strip()
                if '?' in question_text or len(question_text) > 10:
                    is_question = True
            
            # Pattern 3: Common question starters
            question_starters = [
                r'^(Do you|How|What|When|Where|Why|Have you|Are you|Did you|Would you|Can you|Please)',
                r'^(Rate|Select|Choose|Indicate|Describe|List|Specify)'
            ]
            for pattern in question_starters:
                if re.match(pattern, line, re.IGNORECASE) and '?' in line:
                    question_text = line
                    is_question = True
                    break
            
            if is_question and question_text:
                # Save previous question if exists
                if current_question:
                    # Determine type and add options if any
                    if current_options:
                        current_question['type'] = 'mcq'
                        current_question['options'] = current_options
                    else:
                        current_question['type'] = 'text'
                        current_question['placeholder'] = 'Please provide your answer'
                    
                    # Only add if not duplicate
                    q_key = current_question['text'].lower()[:50]
                    if q_key not in seen_questions:
                        seen_questions.add(q_key)
                        questions.append(current_question)
                        question_id += 1
                
                # Start new question
                current_question = {
                    'id': f'q{question_id}',
                    'text': question_text
                }
                current_options = []
                collecting_options = True
                continue
            
            # Check if this line contains options (for MCQ)
            if current_question and collecting_options:
                # Look for option patterns:
                # - Letters/numbers followed by text (a), b), 1), 2), etc.)
                # - Checkboxes/radio buttons
                # - Common option words
                
                option_patterns = [
                    r'^[a-zA-Z][\.\)]\s*(.+)$',  # a) option, b) option
                    r'^\d+[\.\)]\s*(.+)$',  # 1) option, 2) option
                    r'^[○●□■]\s*(.+)$',  # Checkbox/radio symbols
                    r'^(Yes|No|Always|Never|Sometimes|Often|Rarely|Daily|Weekly|Monthly|Excellent|Good|Fair|Poor|Very Poor|Strongly Agree|Agree|Neutral|Disagree|Strongly Disagree)$',
                ]
                
                is_option = False
                option_text = None
                
                for pattern in option_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        option_text = match.group(1) if match.lastindex else match.group(0)
                        option_text = self.clean_text(option_text)
                        if len(option_text) > 1 and len(option_text) < 100:
                            is_option = True
                            break
                
                # Also check if line looks like an option (short, common words)
                if not is_option and len(line) < 50:
                    common_options = ['yes', 'no', 'always', 'never', 'sometimes', 'often', 'rarely',
                                     'daily', 'weekly', 'monthly', 'excellent', 'good', 'fair', 'poor',
                                     'strongly agree', 'agree', 'neutral', 'disagree', 'strongly disagree']
                    if any(opt in line.lower() for opt in common_options):
                        is_option = True
                        option_text = line
                
                if is_option and option_text:
                    if option_text not in current_options:
                        current_options.append(option_text)
                elif len(line) > 100:  # Long line, probably not an option
                    collecting_options = False
        
        # Add the last question
        if current_question:
            if current_options:
                current_question['type'] = 'mcq'
                current_question['options'] = current_options
            else:
                current_question['type'] = 'text'
                current_question['placeholder'] = 'Please provide your answer'
            
            q_key = current_question['text'].lower()[:50]
            if q_key not in seen_questions:
                questions.append(current_question)
        
        return questions
    
    def identify_question_type(self, question_text: str, options: List[str]) -> tuple:
        """Identify question type and extract options if needed."""
        question_lower = question_text.lower()
        
        # If we already have options, it's MCQ
        if options:
            return 'mcq', options
        
        # Check for common MCQ patterns
        mcq_keywords = {
            'frequency': ['how often', 'frequency', 'rate', 'how many times'],
            'yes_no': ['yes or no', 'do you', 'have you', 'are you'],
            'rating': ['rate', 'level', 'scale', 'how would you rate'],
            'quality': ['how would you describe', 'quality', 'overall']
        }
        
        # Check if it's likely a text question (has "describe", "explain", "list", etc.)
        text_keywords = ['describe', 'explain', 'list', 'specify', 'details', 'please provide', 'tell us']
        if any(keyword in question_lower for keyword in text_keywords):
            return 'text', None
        
        # Default to text if uncertain
        return 'text', None
    
    def parse_questionnaire(self, pdf_path: str) -> Dict[str, Any]:
        """Parse a PDF questionnaire and extract structured data."""
        filename = os.path.basename(pdf_path)
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {
                'title': title,
                'filename': filename,
                'questions': []
            }
        
        # Find questions
        questions = self.find_questions(text)
        
        # If no questions found, try alternative extraction
        if not questions:
            # Try to find any text with question marks
            question_matches = re.findall(r'([^.!?]*\?)', text)
            for i, q_text in enumerate(question_matches[:20]):  # Limit to 20
                q_text = self.clean_text(q_text)
                if len(q_text) > 10 and len(q_text) < 300:
                    q_type, options = self.identify_question_type(q_text, [])
                    question = {
                        'id': f'q{i+1}',
                        'text': q_text,
                        'type': q_type
                    }
                    if q_type == 'text':
                        question['placeholder'] = 'Please provide your answer'
                    questions.append(question)
        
        return {
            'title': title,
            'filename': filename,
            'questions': questions
        }


def main():
    """Parse all PDF questionnaires."""
    input_dir = 'pdfs'
    output_dir = 'output'
    
    os.makedirs(output_dir, exist_ok=True)
    
    parser = ImprovedQuestionnaireParser()
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF questionnaire(s)")
    print("-" * 50)
    
    # Parse all questionnaires
    questionnaires = []
    for pdf_file in sorted(pdf_files):
        pdf_path = os.path.join(input_dir, pdf_file)
        print(f"Parsing: {pdf_file}")
        
        questionnaire = parser.parse_questionnaire(pdf_path)
        questionnaires.append(questionnaire)
        
        print(f"  → Extracted {len(questionnaire['questions'])} questions")
        # Print first few questions for debugging
        for q in questionnaire['questions'][:3]:
            print(f"    - {q['text'][:60]}...")
    
    print("-" * 50)
    
    # Save questionnaire schemas
    schema_path = os.path.join(output_dir, 'questionnaire_schemas.json')
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(questionnaires, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved questionnaire schemas to: {schema_path}")
    print(f"✓ Total questions extracted: {sum(len(q['questions']) for q in questionnaires)}")


if __name__ == '__main__':
    main()



