# Setting Up OpenAI API Key

## Quick Setup

1. **Create a `.env` file** in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **Note**: Replace `your_openai_api_key_here` with your actual API key from OpenAI.

2. The `.env` file is already in `.gitignore`, so it won't be committed.

3. Run the script:
   ```bash
   python generate_ai_data.py --num_patients 10
   ```

## Why This Error Happened

GitHub detected your API key in the code and blocked the push to protect your secret. This is a security feature called "Push Protection" that prevents accidentally exposing secrets in public repositories.

## What to Do

The API key has been removed from the code. You now need to:

1. **If you haven't pushed yet**: Just commit the updated file (without the key)
2. **If you already have the key in git history**: You may want to rotate your API key in OpenAI dashboard for security

## Alternative: Use Environment Variable

Instead of `.env` file, you can set it as an environment variable:

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="your_key_here"
python generate_ai_data.py --num_patients 10
```

**Windows CMD:**
```cmd
set OPENAI_API_KEY=your_key_here
python generate_ai_data.py --num_patients 10
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_key_here
python generate_ai_data.py --num_patients 10
```

