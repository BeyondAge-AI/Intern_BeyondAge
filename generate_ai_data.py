"""
AI-Powered Questionnaire Response and Lab Test Data Generator

This script uses an intelligent AI model to:
1. Generate realistic responses to questionnaire questions
2. Create sample lab test data based on reference ranges

Requirements:
    pip install openai python-dotenv numpy

Usage:
    python generate_ai_data.py --num_patients 10 --api_key YOUR_API_KEY
"""

import os
import json
import random
import argparse
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Try to import OpenAI, fallback to mock if not available
try:
    import openai
    # Check if it's the new API (v1.0+)
    if hasattr(openai, 'OpenAI'):
        from openai import OpenAI
        OPENAI_AVAILABLE = True
    else:
        # Old API version
        OPENAI_AVAILABLE = False
        print("Warning: OpenAI library version too old. Please upgrade: pip install --upgrade openai")
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. Install with: pip install openai")


class AIGenerator:
    """Uses AI model to generate intelligent responses."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        # Get API key from parameter, environment variable, or .env file
        # Never hardcode API keys in source code!
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print(f"✓ AI model initialized: {model}")
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None
        else:
            print("Warning: Using fallback response generation (no AI model)")
    
    def generate_response(self, question: Dict[str, Any], context: str = "") -> Any:
        """Generate an intelligent response to a question using AI."""
        
        # If no AI client, use fallback
        if not self.client:
            return self._fallback_response(question)
        
        try:
            question_text = question.get("text", "")
            question_type = question.get("type", "text")
            
            # Build prompt based on question type
            if question_type == "multiple_choice":
                options = question.get("options", [])
                prompt = f"""You are a healthcare patient filling out a medical questionnaire. 
Answer the following question by selecting ONE option from the provided choices.
Be realistic and consider the context of a typical patient.

Question: {question_text}
Options: {', '.join(options)}

Context: {context}

Respond with ONLY the selected option text, nothing else."""
            
            elif question_type == "checkbox":
                options = question.get("options", [])
                prompt = f"""You are a healthcare patient filling out a medical questionnaire.
Answer the following question by selecting ALL applicable options from the list.
Be realistic - select 0-3 options that are relevant.

Question: {question_text}
Options: {', '.join(options)}

Context: {context}

Respond with a comma-separated list of selected options, or "None" if none apply."""
            
            elif question_type == "multiple_choice_grid":
                rows = question.get("rows", [])
                columns = question.get("columns", [])
                prompt = f"""You are a healthcare patient filling out a medical questionnaire.
For each row item, select the most appropriate column option.

Question: {question_text}
Rows: {', '.join(rows)}
Columns: {', '.join(columns)}

Context: {context}

Respond with a JSON object mapping each row to a column, like: {{"Row1": "Column1", "Row2": "Column2"}}"""
            
            else:  # text type
                placeholder = question.get("placeholder", "Your answer")
                prompt = f"""You are a healthcare patient filling out a medical questionnaire.
Provide a brief, realistic answer to the following question.

Question: {question_text}
Placeholder hint: {placeholder}

Context: {context}

Respond with a concise, realistic answer (1-2 sentences max)."""
            
            # Call AI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates realistic medical questionnaire responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Parse checkbox responses
            if question_type == "checkbox":
                if answer.lower() == "none":
                    return []
                return [opt.strip() for opt in answer.split(",") if opt.strip() in options]
            
            # Parse grid responses
            if question_type == "multiple_choice_grid":
                try:
                    return json.loads(answer)
                except:
                    # Fallback: create simple mapping
                    return {row: random.choice(columns) for row in rows}
            
            return answer
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._fallback_response(question)
    
    def _fallback_response(self, question: Dict[str, Any]) -> Any:
        """Fallback response generation without AI."""
        question_type = question.get("type", "text")
        
        if question_type == "multiple_choice":
            options = question.get("options", [])
            return random.choice(options) if options else "Yes"
        
        elif question_type == "checkbox":
            options = question.get("options", [])
            num_selected = random.randint(0, min(3, len(options)))
            return random.sample(options, num_selected) if num_selected > 0 else []
        
        elif question_type == "multiple_choice_grid":
            rows = question.get("rows", [])
            columns = question.get("columns", [])
            return {row: random.choice(columns) for row in rows}
        
        else:  # text
            text_templates = [
                "No specific concerns at this time",
                "Occasionally, but manageable",
                "Yes, I have noticed this",
                "Not applicable to my situation",
                "Varies from day to day"
            ]
            return random.choice(text_templates)


class LabTestDataGenerator:
    """Generates realistic lab test data based on reference ranges."""
    
    def __init__(self, glossary_path: str):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            self.glossary = json.load(f)
        
        self.all_tests = self.glossary.get("testsGlossary", {}).get("allTests", [])
        print(f"✓ Loaded {len(self.all_tests)} lab tests from glossary")
    
    def generate_test_value(self, test: Dict[str, Any], health_status: str = "normal") -> float:
        """Generate a realistic test value within or outside reference range."""
        min_range = test.get("minRange")
        max_range = test.get("maxRange")
        
        if min_range is None or max_range is None:
            return 0.0
        
        # Health status affects value distribution
        if health_status == "normal":
            # Generate value within normal range (slight variation)
            value = np.random.normal(
                loc=(min_range + max_range) / 2,
                scale=(max_range - min_range) / 6
            )
            # Clamp to range
            value = max(min_range, min(max_range, value))
        
        elif health_status == "low":
            # Generate value below normal range
            value = min_range - abs(np.random.normal(0, (max_range - min_range) * 0.2))
            value = max(0, value)  # Don't go negative unless range allows
        
        elif health_status == "high":
            # Generate value above normal range
            value = max_range + abs(np.random.normal(0, (max_range - min_range) * 0.2))
        
        else:  # random
            # Random value, can be in or out of range
            value = np.random.normal(
                loc=(min_range + max_range) / 2,
                scale=(max_range - min_range) / 2
            )
            value = max(0, value)
        
        # Round to appropriate decimal places
        if abs(value) < 1:
            return round(value, 2)
        elif abs(value) < 10:
            return round(value, 1)
        else:
            return round(value, 0)
    
    def generate_lab_panel(self, test_groups: Optional[List[str]] = None, 
                           num_tests: Optional[int] = None,
                           health_status: str = "normal") -> List[Dict[str, Any]]:
        """Generate a panel of lab test results."""
        
        if test_groups:
            # Filter tests by group
            available_tests = [
                t for t in self.all_tests 
                if t.get("testGroupName") in test_groups
            ]
        else:
            available_tests = self.all_tests
        
        # Select tests
        if num_tests:
            selected_tests = random.sample(
                available_tests, 
                min(num_tests, len(available_tests))
            )
        else:
            # Select a reasonable subset (10-20 tests)
            num_to_select = random.randint(10, min(20, len(available_tests)))
            selected_tests = random.sample(available_tests, num_to_select)
        
        # Generate results
        results = []
        for test in selected_tests:
            value = self.generate_test_value(test, health_status)
            
            # Determine if value is within normal range
            min_range = test.get("minRange")
            max_range = test.get("maxRange")
            is_normal = (min_range is not None and max_range is not None and 
                        min_range <= value <= max_range) if (min_range is not None and max_range is not None) else True
            
            results.append({
                "testGroupName": test.get("testGroupName"),
                "testAttributeName": test.get("testAttributeName"),
                "value": value,
                "unit": test.get("unit", ""),
                "minRange": min_range,
                "maxRange": max_range,
                "status": "Normal" if is_normal else ("High" if value > max_range else "Low")
            })
        
        return results


class DataGenerator:
    """Main class to generate questionnaire responses and lab test data."""
    
    def __init__(self, questionnaire_path: str, lab_test_path: str, 
                 api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.questionnaire_path = questionnaire_path
        self.lab_test_path = lab_test_path
        
        # Load data
        with open(questionnaire_path, 'r', encoding='utf-8') as f:
            self.questionnaire_data = json.load(f)
        
        # Initialize generators
        self.ai_generator = AIGenerator(api_key, model)
        self.lab_generator = LabTestDataGenerator(lab_test_path)
        
        print(f"✓ Loaded questionnaire glossary with {self.questionnaire_data['metadata']['totalForms']} forms")
    
    def generate_patient_data(self, patient_id: str, 
                              health_status: str = "normal") -> Dict[str, Any]:
        """Generate complete patient data: questionnaire responses + lab tests."""
        
        # Generate questionnaire responses
        questionnaire_responses = {}
        forms_data = []
        
        questions_glossary = self.questionnaire_data.get("questionsGlossary", {})
        by_form = questions_glossary.get("byForm", {})
        
        for form_key, form_data in by_form.items():
            form_title = form_data.get("formTitle", "")
            questions = form_data.get("questions", [])
            
            form_responses = {
                "formTitle": form_title,
                "formKey": form_key,
                "answers": {}
            }
            
            # Build context from form title
            context = f"Patient filling out {form_title}"
            
            for question in questions:
                # Skip patient ID questions (we'll use our own)
                if "patient id" in question.get("text", "").lower():
                    form_responses["answers"][question["id"]] = patient_id
                else:
                    answer = self.ai_generator.generate_response(question, context)
                    form_responses["answers"][question["id"]] = answer
            
            forms_data.append(form_responses)
            questionnaire_responses[form_key] = form_responses["answers"]
        
        # Generate lab test data
        # Select relevant test groups based on questionnaire responses
        test_groups = self._select_relevant_test_groups(questionnaire_responses)
        lab_results = self.lab_generator.generate_lab_panel(
            test_groups=test_groups,
            health_status=health_status
        )
        
        return {
            "patientId": patient_id,
            "timestamp": datetime.now().isoformat(),
            "healthStatus": health_status,
            "questionnaireResponses": questionnaire_responses,
            "labTestResults": lab_results,
            "metadata": {
                "totalForms": len(forms_data),
                "totalLabTests": len(lab_results),
                "generatedAt": datetime.now().isoformat()
            }
        }
    
    def _select_relevant_test_groups(self, responses: Dict[str, Any]) -> List[str]:
        """Select relevant test groups based on questionnaire responses."""
        # Default comprehensive panel
        default_groups = [
            "GENERAL PATHOLOGY",
            "LIVER PROFILE",
            "RENAL PROFILE",
            "LIPID PROFILE",
            "DIABETES",
            "THYROID",
            "VITAMINS"
        ]
        
        # Analyze responses to add relevant groups
        all_responses = " ".join([
            str(v) if isinstance(v, str) else json.dumps(v)
            for form_responses in responses.values()
            for v in form_responses.values()
        ]).lower()
        
        relevant_groups = default_groups.copy()
        
        if any(word in all_responses for word in ["hormone", "menstrual", "fertility"]):
            relevant_groups.extend(["FERTILITY (FEMALE)", "FERTILITY (MALE)", "ADRENAL HORMONES"])
        
        if any(word in all_responses for word in ["allergy", "allergic", "sensitivity"]):
            relevant_groups.append("ALLERGY - SPECIFIC IgE")
        
        if any(word in all_responses for word in ["heart", "cardiac", "chest"]):
            relevant_groups.append("CARDIAC MARKERS")
        
        if any(word in all_responses for word in ["joint", "arthritis", "pain"]):
            relevant_groups.extend(["ARTHRITIS", "AUTOIMMUNE"])
        
        return list(set(relevant_groups))  # Remove duplicates
    
    def generate_dataset(self, num_patients: int, 
                        health_status_distribution: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Generate dataset for multiple patients."""
        
        if health_status_distribution is None:
            health_status_distribution = {
                "normal": 0.7,
                "low": 0.15,
                "high": 0.15
            }
        
        dataset = []
        
        for i in range(num_patients):
            # Select health status based on distribution
            rand = random.random()
            cumulative = 0
            health_status = "normal"
            for status, prob in health_status_distribution.items():
                cumulative += prob
                if rand <= cumulative:
                    health_status = status
                    break
            
            patient_id = f"PAT_{i+1:04d}"
            print(f"Generating data for {patient_id} (status: {health_status})...")
            
            patient_data = self.generate_patient_data(patient_id, health_status)
            dataset.append(patient_data)
        
        return dataset


def main():
    parser = argparse.ArgumentParser(
        description='Generate AI-powered questionnaire responses and lab test data'
    )
    parser.add_argument(
        '--questionnaire_path',
        type=str,
        default='json/combined_questionnaires_glossary.json',
        help='Path to questionnaire glossary JSON'
    )
    parser.add_argument(
        '--lab_test_path',
        type=str,
        default='json/combined_lab_tests_glossary.json',
        help='Path to lab test glossary JSON'
    )
    parser.add_argument(
        '--num_patients',
        type=int,
        default=5,
        help='Number of patients to generate data for'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default=None,
        help='OpenAI API key (or set OPENAI_API_KEY env variable)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini',
        help='OpenAI model to use (default: gpt-4o-mini)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='output',
        help='Output directory for generated data'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize generator
    print("=" * 60)
    print("AI-Powered Data Generator")
    print("=" * 60)
    
    generator = DataGenerator(
        args.questionnaire_path,
        args.lab_test_path,
        api_key=args.api_key,
        model=args.model
    )
    
    # Generate dataset
    print(f"\nGenerating data for {args.num_patients} patients...")
    print("-" * 60)
    
    dataset = generator.generate_dataset(args.num_patients)
    
    # Save results
    output_file = os.path.join(args.output_dir, 'generated_patient_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print("-" * 60)
    print(f"✓ Generated data for {len(dataset)} patients")
    print(f"✓ Saved to: {output_file}")
    
    # Print summary
    total_forms = sum(len(p["questionnaireResponses"]) for p in dataset)
    total_lab_tests = sum(len(p["labTestResults"]) for p in dataset)
    
    print(f"\nSummary:")
    print(f"  Total patients: {len(dataset)}")
    print(f"  Total questionnaire forms: {total_forms}")
    print(f"  Total lab test results: {total_lab_tests}")
    print(f"  Average lab tests per patient: {total_lab_tests / len(dataset):.1f}")


if __name__ == '__main__':
    main()

