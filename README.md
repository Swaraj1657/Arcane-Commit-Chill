# Certificate Verification System

A full-stack application for verifying academic certificates using OCR, AI text extraction, and database verification.

## Project Structure

```
Arcane-Commit-Chill/
├── credible-canvas/          # Frontend (React + TypeScript + Vite)
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/      # UI components
│   │   ├── contexts/        # React contexts (Auth)
│   │   └── integrations/   # Supabase integration
│   └── package.json
│
└── TextExtraction/           # Backend (Python)
    ├── text.py              # Main processing pipeline
    ├── beautifyText.py      # AI text extraction (Groq)
    ├── verify_college.py    # College verification
    ├── consistency_check.py # Cross-certificate validation
    ├── api_server.py        # FastAPI server
    ├── map_to_schema.py     # Database mapping utility
    └── requirements.txt
```

## Features

- **Username-based Authentication**: Sign up and login with username/password
- **Certificate Upload**: Upload PDF, JPG, or PNG certificate files
- **OCR Processing**: Extract text using Google Cloud Vision API
- **AI Text Extraction**: Structure extracted text using Groq AI
- **College Verification**: Verify institutions against approved database
- **Risk Assessment**: Calculate forgery risk scores
- **Status Tracking**: Track verification status (VERIFIED, PENDING, FAILED, etc.)
- **Detailed Results**: View full processing results and extracted data

## Quick Start

### 1. Frontend Setup

```bash
cd credible-canvas
npm install
```

Create `.env` file:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_key
VITE_API_URL=http://localhost:8000
```

Start frontend:
```bash
npm run dev
```

### 2. Backend Setup

```bash
cd TextExtraction
pip install -r requirements.txt
```

Update API keys in:
- `text.py` - Google Cloud Vision API key
- `beautifyText.py` - Groq API key

Install Poppler (for PDF processing):
- Windows: Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
- Update `POPPLER_PATH` in `text.py` if needed

Start backend:
```bash
python api_server.py
```

### 3. Supabase Setup

1. Run SQL schema from `credible-canvas/supabase-schema.sql`
2. Create storage bucket named `certificates`
3. Configure RLS policies as needed

## Database Schema

### user_profiles
- `id` (uuid, references auth.users)
- `username` (text, unique)
- `kyc_completed` (boolean, default false)
- `kyc_verified` (boolean, default false)

### certificates
- Extracted student information (name, roll number, etc.)
- Extracted academic details (degree, branch, semester, etc.)
- Extracted institution information
- Verification metadata (status, risk score, verdict)
- Raw processing data (JSONB)

See `credible-canvas/supabase-schema.sql` for full schema.

## API Endpoints

### POST /api/verify-certificate
Upload and verify a certificate.

**Request:**
- `file`: Certificate file (PDF, JPG, PNG)

**Response:**
```json
{
  "mapped_data": {
    "document_type": "DEGREE",
    "extracted_student_name": "...",
    "verification_status": "VERIFIED",
    "verdict": "LEGITIMATE",
    ...
  },
  "full_processing_result": { ... }
}
```

## Workflow

1. User signs up with username and password
2. User uploads a certificate file
3. File is uploaded to Supabase storage
4. Backend API processes the certificate:
   - OCR text extraction
   - AI text structuring
   - College verification
   - Risk assessment
5. Results are saved to Supabase
6. User views verification results on dashboard

## Verification Process

1. **OCR Extraction**: Extract text from certificate image/PDF
2. **Text Structuring**: Use AI to structure extracted text
3. **College Verification**: Check against approved college database
4. **Logo Verification**: (Optional) Verify institution logos
5. **Risk Assessment**: Calculate confidence scores and risk levels
6. **Status Determination**: Set verification status based on results

## Environment Variables

### Frontend
- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY`: Supabase anon key
- `VITE_API_URL`: Backend API URL

### Backend
- Update `API_KEY` in `text.py` (Google Cloud Vision)
- Update `api_key` in `beautifyText.py` (Groq)

## Troubleshooting

### Backend Issues
- Ensure Poppler is installed and path is correct
- Check API keys are set correctly
- Verify `College-ALL COLLEGE.xlsx` exists in TextExtraction directory

### Frontend Issues
- Check Supabase credentials in `.env`
- Verify API server is running on correct port
- Check browser console for errors

### Database Issues
- Ensure SQL schema is executed in Supabase
- Verify RLS policies are configured
- Check storage bucket exists and is accessible

## License

[Your License Here]

