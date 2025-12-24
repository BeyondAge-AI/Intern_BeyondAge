"""
PDF Questionnaire Parser and Synthetic Data Generator

This script reads PDF questionnaires, extracts questions, and generates synthetic response data.

Requirements:
    pip install PyPDF2 numpy

Usage:
    python questionnaire_generator.py --input_dir ./pdfs --output_dir ./output --num_responses 100
"""

import os
import re
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import PyPDF2
import numpy as np


class QuestionnaireParser:
    """Parses PDF questionnaires and extracts questions."""
    
    def __init__(self):
        self.question_patterns = [
            r'\d+\.\s*(.+?)(?=\d+\.|$)',
            r'[QQ]uestion\s*\d+[:\.]?\s*(.+?)(?=[QQ]uestion|\d+\.|$)',
            r'(?:^|\n)([A-Z][^.!?]*\?)',
            r'Do you[^?]*\?',
            r'How [^?]*\?',
            r'Have you[^?]*\?',
            r'Are you[^?]*\?',
            r'What [^?]*\?',
            r'Please [^?]*\?'
        ]
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""
    
    def identify_question_type(self, text: str, question_text: str) -> tuple:
        """Identify if question is MCQ or text, and extract options."""
        text_lower = text.lower()
        question_lower = question_text.lower()
        
        # Check for common MCQ patterns
        mcq_patterns = {
            'frequency': {
                'keywords': ['never', 'always', 'rarely', 'sometimes', 'often'],
                'options': ['Never', 'Rarely', 'Sometimes', 'Often', 'Always']
            },
            'yes_no': {
                'keywords': ['yes', 'no'],
                'options': ['Yes', 'No', 'Sometimes']
            },
            'how_often': {
                'keywords': ['how often', 'frequency'],
                'options': ['Daily', 'Weekly', 'Monthly', 'Rarely', 'Never']
            },
            'how_many': {
                'keywords': ['how many', 'number of'],
                'options': ['0-1', '2-3', '4-5', '6+']
            },
            'rating': {
                'keywords': ['rate', 'level', 'severity'],
                'options': ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
            },
            'quality': {
                'keywords': ['quality', 'describe'],
                'options': ['Excellent', 'Good', 'Fair', 'Poor', 'Very Poor']
            }
        }
        
        # Check each pattern
        for pattern_name, pattern_data in mcq_patterns.items():
            if any(keyword in question_lower or keyword in text_lower 
                   for keyword in pattern_data['keywords']):
                return 'mcq', pattern_data['options']
        
        return 'text', None
    
    def clean_question_text(self, text: str) -> str:
        """Clean and format question text."""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        return text
    
    def parse_questionnaire(self, pdf_path: str) -> Dict[str, Any]:
        """Parse a PDF questionnaire and extract structured data."""
        # Extract filename for title
        filename = os.path.basename(pdf_path)
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        title = title.title()
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {
                'title': title,
                'filename': filename,
                'questions': []
            }
        
        questions = []
        seen_questions = set()
        question_id = 1
        
        # Try each pattern to find questions
        for pattern in self.question_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                question_text = match.group(1) if match.lastindex else match.group(0)
                question_text = self.clean_question_text(question_text)
                
                # Filter valid questions
                if (10 < len(question_text) < 500 and 
                    question_text not in seen_questions and
                    '?' in question_text):
                    
                    seen_questions.add(question_text)
                    
                    # Identify question type and options
                    q_type, options = self.identify_question_type(text, question_text)
                    
                    question = {
                        'id': f'q{question_id}',
                        'text': question_text,
                        'type': q_type
                    }
                    
                    if q_type == 'mcq' and options:
                        question['options'] = options
                    else:
                        question['placeholder'] = 'Please provide your answer'
                    
                    questions.append(question)
                    question_id += 1
                    
                    if len(questions) >= 20:  # Limit to 20 questions per questionnaire
                        break
            
            if questions:
                break
        
        # If no questions found, add default questions
        if not questions:
            questions = [
                {
                    'id': 'q1',
                    'text': 'How would you describe your overall health?',
                    'type': 'mcq',
                    'options': ['Excellent', 'Good', 'Fair', 'Poor', 'Very Poor']
                },
                {
                    'id': 'q2',
                    'text': 'Do you have any specific concerns?',
                    'type': 'text',
                    'placeholder': 'Please describe your concerns'
                }
            ]
        
        return {
            'title': title,
            'filename': filename,
            'questions': questions
        }


class SyntheticDataGenerator:
    """Generates synthetic questionnaire response data."""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        
        self.text_response_templates = {
            'food': [
                'Dairy products, spicy foods',
                'Gluten, processed foods',
                'No specific triggers identified',
                'Coffee, carbonated drinks',
                'Red meat, fried foods',
                'Beans, legumes',
                'None that I know of',
                'Lactose, high-fat foods',
                'Sugar, artificial sweeteners',
                'Wheat, soy products'
            ],
            'activity': [
                'Running, cycling, swimming',
                'Yoga, pilates',
                'Weight training, CrossFit',
                'Walking, hiking',
                'Team sports (basketball, soccer)',
                'No regular exercise',
                'Dancing, aerobics',
                'Martial arts, boxing'
            ],
            'general': [
                'Yes, occasionally',
                'No, not at this time',
                'Sometimes, depending on the situation',
                'Regularly',
                'Not applicable',
                'Varies from week to week',
                'Only during certain seasons'
            ]
        }
    
    def generate_mcq_response(self, options: List[str]) -> str:
        """Generate a weighted random MCQ response."""
        n = len(options)
        
        # Create weights favoring middle options (normal distribution)
        mid = n / 2
        weights = [np.exp(-((i - mid) ** 2) / (2 * (mid / 2) ** 2)) for i in range(n)]
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        return np.random.choice(options, p=weights)
    
    def generate_text_response(self, question_text: str) -> str:
        """Generate a realistic text response based on question content."""
        question_lower = question_text.lower()
        
        # Choose appropriate template based on question content
        if any(word in question_lower for word in ['food', 'eat', 'trigger', 'diet']):
            templates = self.text_response_templates['food']
        elif any(word in question_lower for word in ['exercise', 'activity', 'physical', 'sport']):
            templates = self.text_response_templates['activity']
        else:
            templates = self.text_response_templates['general']
        
        return random.choice(templates)
    
    def generate_responses(self, questionnaire: Dict[str, Any], num_responses: int) -> List[Dict[str, Any]]:
        """Generate synthetic responses for a questionnaire."""
        responses = []
        
        for i in range(num_responses):
            # Generate random timestamp within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            response = {
                'responseId': f"resp_{questionnaire['filename'].replace('.pdf', '')}_{i + 1}",
                'questionnaireName': questionnaire['title'],
                'timestamp': timestamp.isoformat(),
                'answers': {}
            }
            
            # Generate answer for each question
            for question in questionnaire['questions']:
                if question['type'] == 'mcq':
                    response['answers'][question['id']] = self.generate_mcq_response(question['options'])
                else:
                    response['answers'][question['id']] = self.generate_text_response(question['text'])
            
            responses.append(response)
        
        return responses
    
    def generate_dataset(self, questionnaires: List[Dict[str, Any]], num_responses: int) -> List[Dict[str, Any]]:
        """Generate complete synthetic dataset for all questionnaires."""
        dataset = []
        
        for questionnaire in questionnaires:
            responses = self.generate_responses(questionnaire, num_responses)
            
            dataset.append({
                'questionnaire': questionnaire['title'],
                'filename': questionnaire['filename'],
                'totalResponses': num_responses,
                'totalQuestions': len(questionnaire['questions']),
                'responses': responses
            })
        
        return dataset


def main():
    parser = argparse.ArgumentParser(
        description='Parse PDF questionnaires and generate synthetic response data'
    )
    parser.add_argument(
        '--input_dir',
        type=str,
        required=True,
        help='Directory containing PDF questionnaires'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./output',
        help='Directory to save output JSON files'
    )
    parser.add_argument(
        '--num_responses',
        type=int,
        default=10,
        help='Number of synthetic responses to generate per questionnaire'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize parser and generator
    questionnaire_parser = QuestionnaireParser()
    data_generator = SyntheticDataGenerator(seed=args.seed)
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(args.input_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {args.input_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF questionnaire(s)")
    print("-" * 50)
    
    # Parse all questionnaires
    questionnaires = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(args.input_dir, pdf_file)
        print(f"Parsing: {pdf_file}")
        
        questionnaire = questionnaire_parser.parse_questionnaire(pdf_path)
        questionnaires.append(questionnaire)
        
        print(f"  → Extracted {len(questionnaire['questions'])} questions")
    
    print("-" * 50)
    
    # Save questionnaire schemas
    schema_path = os.path.join(args.output_dir, 'questionnaire_schemas.json')
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(questionnaires, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved questionnaire schemas to: {schema_path}")
    
    # Generate synthetic data
    print(f"\nGenerating {args.num_responses} synthetic responses per questionnaire...")
    synthetic_data = data_generator.generate_dataset(questionnaires, args.num_responses)
    
    # Save synthetic data
    data_path = os.path.join(args.output_dir, 'synthetic_responses.json')
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(synthetic_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved synthetic response data to: {data_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("GENERATION SUMMARY")
    print("=" * 50)
    for data in synthetic_data:
        print(f"\n{data['questionnaire']}")
        print(f"  Questions: {data['totalQuestions']}")
        print(f"  Responses: {data['totalResponses']}")
        print(f"  Total data points: {data['totalQuestions'] * data['totalResponses']}")
    
    print(f"\n✓ All files saved to: {args.output_dir}")


if __name__ == '__main__':
    main()