# AI-Powered Questionnaire and Lab Test Data Generator

This script uses OpenAI's API to generate intelligent responses to questionnaire questions and creates realistic lab test data based on reference ranges.

## Features

1. **AI-Powered Questionnaire Responses**: Uses GPT models to generate realistic, context-aware answers to health questionnaire questions
2. **Lab Test Data Generation**: Creates sample lab test results within or outside normal ranges based on health status
3. **Multi-Form Support**: Handles all questionnaire forms from the combined glossary
4. **Flexible Health Status**: Generates data for normal, low, or high health status scenarios

## Installation

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install openai python-dotenv numpy
```

## Usage

### Basic Usage

```bash
python generate_ai_data.py --num_patients 10
```

### With Custom Options

```bash
python generate_ai_data.py \
    --num_patients 20 \
    --model gpt-4o-mini \
    --output_dir output
```

### Command Line Arguments

- `--questionnaire_path`: Path to questionnaire glossary JSON (default: `json/combined_questionnaires_glossary.json`)
- `--lab_test_path`: Path to lab test glossary JSON (default: `json/combined_lab_tests_glossary.json`)
- `--num_patients`: Number of patients to generate data for (default: 5)
- `--api_key`: OpenAI API key (optional, can also use environment variable)
- `--model`: OpenAI model to use (default: `gpt-4o-mini`)
- `--output_dir`: Output directory for generated data (default: `output`)

## Output Format

The script generates a JSON file (`generated_patient_data.json`) with the following structure:

```json
{
  "patientId": "PAT_0001",
  "timestamp": "2025-12-24T11:24:29.222625",
  "healthStatus": "normal",
  "questionnaireResponses": {
    "gut_wellness": {
      "q1": "PAT_0001",
      "q2": "No",
      ...
    },
    ...
  },
  "labTestResults": [
    {
      "testGroupName": "LIVER PROFILE",
      "testAttributeName": "SGOT (AST)",
      "value": 35.2,
      "unit": "U/L",
      "minRange": 5,
      "maxRange": 40,
      "status": "Normal"
    },
    ...
  ],
  "metadata": {
    "totalForms": 6,
    "totalLabTests": 15,
    "generatedAt": "2025-12-24T11:24:29.222625"
  }
}
```

## Health Status Distribution

By default, the script generates:
- 70% normal health status
- 15% low values (below normal ranges)
- 15% high values (above normal ranges)

## API Key Setup

**IMPORTANT: Never commit API keys to version control!**

To set up your OpenAI API key:

1. **Option 1: Using .env file (Recommended)**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API key
   OPENAI_API_KEY=your_actual_api_key_here
   ```
   The `.env` file is already in `.gitignore` and won't be committed.

2. **Option 2: Environment variable**
   ```bash
   # Windows (PowerShell)
   $env:OPENAI_API_KEY="your_actual_api_key_here"
   
   # Windows (CMD)
   set OPENAI_API_KEY=your_actual_api_key_here
   
   # Linux/Mac
   export OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Option 3: Command line argument**
   ```bash
   python generate_ai_data.py --api_key your_actual_api_key_here --num_patients 10
   ```

**Security Note**: If you accidentally committed an API key, you should:
1. Rotate/regenerate the key in your OpenAI account
2. Remove it from git history (if needed)
3. Use one of the methods above going forward

## Fallback Mode

If the OpenAI API is unavailable or not configured, the script will use a fallback mode that generates responses using rule-based logic. This ensures the script always works, though responses may be less sophisticated.

## Example Output

After running the script, you'll see:

```
============================================================
AI-Powered Data Generator
============================================================
✓ AI model initialized: gpt-4o-mini
✓ Loaded 315 lab tests from glossary
✓ Loaded questionnaire glossary with 6 forms

Generating data for 5 patients...
------------------------------------------------------------
Generating data for PAT_0001 (status: normal)...
Generating data for PAT_0002 (status: low)...
...
------------------------------------------------------------
✓ Generated data for 5 patients
✓ Saved to: output\generated_patient_data.json

Summary:
  Total patients: 5
  Total questionnaire forms: 30
  Total lab test results: 85
  Average lab tests per patient: 17.0
```

## Notes

- The script intelligently selects relevant lab test groups based on questionnaire responses
- AI responses are context-aware and consider the form type
- Lab test values are generated within realistic ranges based on health status
- All data is timestamped and includes metadata for tracking

