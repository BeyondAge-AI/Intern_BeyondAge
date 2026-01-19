"""
Patient Profile Generator

This script generates patient profiles using OpenAI API, combining:
- Lab test glossary (combined_lab_tests_glossary.json)
- Questionnaire glossary (combined_questionnaires_glossary.json)

Usage:
    python generate_patient_profiles.py --num_profiles 10
"""

import os
import json
import argparse
import sys
from pathlib import Path
from openai import OpenAI


def load_json_file(file_path: str) -> dict:
    """Load and return JSON file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_patient_profile(client: OpenAI, lab_tests: dict, questionnaires: dict, profile_number: int) -> str:
    """Generate a single patient profile using OpenAI API."""
    
    # Extract sample test group names
    test_groups = lab_tests.get('testGroups', [])
    sample_groups = [group.get('groupName', '') for group in test_groups[:15]]  # First 15 groups
    
    # Extract questionnaire categories
    forms = questionnaires.get('forms', [])
    questionnaire_categories = [form.get('category', '') for form in forms]
    
    # Create a prompt that includes the lab tests and questionnaire data
    prompt = f"""You are a medical professional creating a detailed patient profile. Generate a realistic patient profile in the exact format shown below, incorporating relevant information from the lab tests glossary and questionnaires provided.

Format the profile exactly like this example:

### *Patient Profile: [Patient Name]*

* *Demographics:* [Age, gender, brief background]

* *Chief Complaints:* [Main symptoms and concerns]

* *Metabolic Concerns:* [Metabolic-related issues if applicable]

* *Hormonal Symptoms:* [Hormonal-related symptoms if applicable]

* *Lifestyle & Symptoms:* [Lifestyle factors and related symptoms]

* *Dietary Triggers:* [Food sensitivities or dietary issues if applicable]

* *Lab Profile (Metabolic):* [Include 2-3 relevant metabolic lab tests with values and reference ranges]

* *Lab Profile (Hormonal):* [Include 2-3 relevant hormonal lab tests with values and reference ranges]

* *Lab Profile (Thyroid):* [Include thyroid tests if applicable]

* *Nutritional Status:* [Include relevant vitamin/mineral levels if applicable]

* *Inflammatory Markers:* [Include inflammatory markers if applicable]

* *Clinical Summary:* [Comprehensive summary connecting all findings]

Available Lab Test Categories (sample):
{', '.join(sample_groups)}

Available Questionnaire Categories:
{', '.join(set(questionnaire_categories))}

Lab Tests Glossary Summary:
- Total test groups: {lab_tests.get('metadata', {}).get('totalTestGroups', 0)}
- Total tests: {lab_tests.get('metadata', {}).get('totalTests', 0)}

Questionnaires Available:
- Total forms: {questionnaires.get('metadata', {}).get('totalForms', 0)}
- Total questions: {questionnaires.get('metadata', {}).get('totalQuestions', 0)}

Generate a unique, realistic patient profile with:
1. A realistic Indian name
2. Age between 30-65 years
3. Relevant lab test values (some normal, some abnormal) with proper reference ranges
4. Symptoms that correlate with the lab findings
5. A coherent clinical picture that connects symptoms, lab values, and questionnaire responses

Make sure lab values are realistic and include proper units and reference ranges in parentheses like: *Test Name* is *value* (Ref: range).

Use common lab tests such as:
- Metabolic: HbA1c, Fasting Blood Glucose, Fasting Insulin, Lipid Profile (Total Cholesterol, LDL, HDL, Triglycerides)
- Hormonal: Testosterone (Total/Free), Estradiol, Progesterone, Cortisol, DHEA-S
- Thyroid: TSH, Free T3, Free T4
- Vitamins: Vitamin D, Vitamin B12, Folate
- Inflammatory: hs-CRP, ESR"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical professional creating detailed patient profiles based on lab tests and questionnaire data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating profile {profile_number}: {e}", flush=True)
        return None


def main():
    print("Script started", flush=True)
    parser = argparse.ArgumentParser(
        description='Generate patient profiles using OpenAI API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python generate_patient_profiles.py --num_profiles 5 --api_key YOUR_API_KEY
  python generate_patient_profiles.py --num_profiles 10
  
Note: If --api_key is not provided, the script will look for OPENAI_API_KEY environment variable.
        """
    )
    parser.add_argument(
        '--num_profiles',
        type=int,
        required=True,
        help='Number of patient profiles to generate'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default=None,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='Patient_profiles',
        help='Directory to save patient profiles'
    )
    
    args = parser.parse_args()
    print(f"Arguments parsed: num_profiles={args.num_profiles}", flush=True)
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not provided. Use --api_key or set OPENAI_API_KEY environment variable.", flush=True)
        return
    print("API key found", flush=True)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    print(f"✓ OpenAI client initialized", flush=True)
    
    # Load JSON files
    json_dir = Path("json")
    lab_tests_path = json_dir / "combined_lab_tests_glossary.json"
    questionnaires_path = json_dir / "combined_questionnaires_glossary.json"
    
    if not lab_tests_path.exists():
        print(f"Error: Lab tests glossary not found at {lab_tests_path}")
        return
    
    if not questionnaires_path.exists():
        print(f"Error: Questionnaires glossary not found at {questionnaires_path}")
        return
    
    print("Loading JSON files...", flush=True)
    lab_tests = load_json_file(str(lab_tests_path))
    questionnaires = load_json_file(str(questionnaires_path))
    print(f"✓ Loaded lab tests glossary ({lab_tests.get('metadata', {}).get('totalTests', 0)} tests)", flush=True)
    print(f"✓ Loaded questionnaires glossary ({questionnaires.get('metadata', {}).get('totalQuestions', 0)} questions)", flush=True)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Find the next profile number
    existing_profiles = list(output_dir.glob("patient_profile_*.md"))
    if existing_profiles:
        # Extract numbers and find max
        numbers = []
        for profile in existing_profiles:
            try:
                num = int(profile.stem.split("_")[-1])
                numbers.append(num)
            except:
                pass
        start_num = max(numbers) + 1 if numbers else 1
    else:
        start_num = 1
    
    print(f"\nGenerating {args.num_profiles} patient profile(s)...", flush=True)
    print("-" * 50, flush=True)
    
    # Generate profiles
    for i in range(args.num_profiles):
        profile_num = start_num + i
        print(f"Generating profile {i+1}/{args.num_profiles} (patient_profile_{profile_num:02d}.md)...", flush=True)
        
        profile_content = generate_patient_profile(client, lab_tests, questionnaires, profile_num)
        
        if profile_content:
            # Save profile
            profile_path = output_dir / f"patient_profile_{profile_num:02d}.md"
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_content)
            print(f"  ✓ Saved to {profile_path}", flush=True)
        else:
            print(f"  ✗ Failed to generate profile {profile_num}", flush=True)
    
    print("-" * 50, flush=True)
    print(f"✓ Completed! Generated {args.num_profiles} profile(s) in {output_dir}", flush=True)


if __name__ == '__main__':
    main()

