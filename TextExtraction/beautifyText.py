import json
from groq import Groq

# 🔑 Put your Groq API key here
client = Groq(
    api_key="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"
)

SYSTEM_PROMPT = """
You are an expert Academic Document Understanding AI.

Rules:
- Use ONLY the information explicitly present in the input text.
- Do NOT assume formats, column names, relationships, or missing values.
- Do NOT infer, normalize, expand, or correct data.
- If a value is missing, unclear, or partially visible, return null.
- Preserve wording as close to the original text as possible.
- Beautification is limited to whitespace cleanup and obvious OCR noise removal ONLY.
- Do NOT add external knowledge.
- Return ONLY valid JSON.
- If required fields cannot be extracted, return an empty JSON object {}.

"""
def beautify_academic_document(ocr_text: str) -> dict:
    user_prompt = f"""
Analyze the following OCR text from an academic document.

Tasks:
1. Identify the document type (Marksheet, Degree Certificate, Provisional Certificate, Other).
2. Extract and normalize all meaningful information.
3. Separate:
   - student_details
   - academic_details
   - institution_details
   - subjects (if any)
   - summary / result
   - certificate_metadata
4. Do not rely on fixed column names.
5. Return ONLY valid JSON.

RAW OCR TEXT:
<<<
{ocr_text}
>>>
"""

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # ✅ UPDATED MODEL
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.1
)


    content = response.choices[0].message.content.strip()

    # 🛡️ SAFETY JSON EXTRACTION
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON returned by Groq:\n{content}")

    json_str = content[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned by Groq:\n{json_str}") from e


# ==========================
# USAGE
# ==========================
if __name__ == "__main__":
    raw_ocr_text = """
   
"""

    raw_ocr_text = raw_ocr_text.strip()

    structured_data = beautify_academic_document(raw_ocr_text)
    print(json.dumps(structured_data, indent=2))
