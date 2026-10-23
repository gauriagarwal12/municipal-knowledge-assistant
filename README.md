# Cedarhaven Municipal Knowledge Assistant

An AI-powered municipal knowledge assistant that helps residents find information about municipal services, bylaw enforcement, permits, and licensing using the provided Cedarhaven PDF documents.

## Features

- **Document-grounded answers:** Uses information retrieved from the provided municipal documents.
- **TF-IDF retrieval:** Finds relevant passages using text similarity.
- **AI-powered responses:** Uses Google's Gemini API to generate clear answers based on retrieved evidence.
- **Source citations:** Displays source document names and PDF page numbers.
- **Clickable PDF references:** Allows users to open source documents directly from the chat.
- **Suggested questions:** Provides ready-to-use prompts for common municipal queries.
- **Markdown formatting:** Displays answers with readable headings, bullet points, and numbered lists.
- **Insufficient-evidence handling:** Indicates when the provided documents do not contain enough information to answer a question.
- **Responsive interface:** Provides a user-friendly experience on desktop and mobile screens.

## Technology Stack

- **Backend:** Python, Flask
- **AI model:** Google Gemini API
- **Information retrieval:** scikit-learn, TF-IDF, cosine similarity
- **PDF processing:** pypdf
- **Frontend:** HTML, CSS, JavaScript
- **Answer formatting:** Marked and DOMPurify

## Project Structure

```text
municipal_knowledge_assistant/
├── app.py
├── agent.py
├── retriever.py
├── document_loader.py
├── data/
│   ├── 01_Cedarhaven_Service_Request_Management.pdf
│   ├── 02_Cedarhaven_Bylaw_Enforcement.pdf
│   └── 03_Cedarhaven_Permits_and_Licensing.pdf
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chat.js
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

Before running the application, ensure you have:

- Python 3.10 or a compatible version supported by your dependencies.
- A Google Gemini API key.
- The required Python packages listed in `requirements.txt`.
- The provided Cedarhaven PDF documents.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd municipal_knowledge_assistant
```

Replace `YOUR_REPOSITORY_URL` with your actual GitHub repository URL.

If you have already downloaded the project, open the project folder in VS Code and skip this step.

### 2. Create a Virtual Environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure the required environment variables.

Example:

```env
GEMINI_API_KEY=your_actual_api_key
GEMINI_MODEL=gemini-2.5-flash
MUNICIPAL_PDF_DIR=data
RETRIEVAL_TOP_K=10
RETRIEVAL_MIN_SCORE=0.055
```

Replace `your_actual_api_key` with your own Gemini API key.

**Important:** Never commit your actual `.env` file or API key to GitHub. If the application does not automatically load `.env` variables, configure environment-variable loading or set them in your terminal.

### 5. Verify the PDF Documents

Ensure that the required PDF files are present in the `data/` directory. The application needs these documents to retrieve information and generate source-grounded answers.

### 6. Run the Application

```bash
python app.py
```

Open the local URL printed in the terminal. It is commonly:

```text
http://127.0.0.1:5000
```

## How It Works

The application follows a retrieval-augmented question-answering workflow:

1. **Document ingestion:** The PDF loader extracts text from the municipal documents and splits it into smaller chunks while preserving PDF page numbers.
2. **Text vectorization:** TF-IDF converts the document chunks and user questions into numerical representations.
3. **Similarity search:** Cosine similarity ranks the document passages according to their relevance to the user's question.
4. **Evidence selection:** Relevant passages are selected for the answer-generation process.
5. **Answer generation:** The Gemini API generates a response using the retrieved evidence and instructions to avoid unsupported claims.
6. **Source references:** The application returns source document names and PDF page numbers so users can verify the information.
7. **Frontend presentation:** The interface displays the answer, formatted text, suggested questions, and clickable PDF references.

## Example Questions

Users can ask questions such as:

- What services and responsibilities does the Cedarhaven municipality provide to residents?
- How can a resident submit a municipal service request?
- How can a resident report a property-related bylaw violation?
- What can a bylaw enforcement officer do when investigating a suspected property standards violation?
- What happens if a property owner ignores a compliance notice?
- What permits and licences are covered in the provided municipal documents?

## Testing and Evaluation

Use the following checklist to evaluate the application:

- Verify that municipal service questions return relevant information.
- Verify that service-request questions retrieve the appropriate document passages.
- Test the bylaw reporting workflow.
- Test questions about bylaw investigations and compliance notices.
- Ask questions about information that is absent from the supplied documents.
- Confirm that the application does not invent unsupported contact details, deadlines, or penalties.
- Verify that source references display the correct PDF filenames and page numbers.
- Open clickable source references and confirm that the PDFs load correctly.
- Confirm that headings, bold text, numbered steps, and bullet points render properly.
- Test the interface on desktop and mobile-sized screens.

## Limitations

- Answers are limited by the information available in the supplied documents.
- TF-IDF retrieval primarily relies on lexical similarity and may miss relevant passages that use different wording.
- AI-generated responses may contain inaccuracies and should be verified against the cited source documents.
- The application does not provide real-time municipal case status or replace official municipal guidance.
- PDF source links depend on the documents being available in the configured directory.

## Future Improvements

Potential enhancements include:

- Semantic search using embedding-based retrieval.
- Automated evaluation of retrieval quality and citation accuracy.
- Persistent user feedback and usage analytics.
- Support for additional municipal documents.
- Improved document update and indexing workflows.
- Automated tests for common questions and insufficient-evidence scenarios.

## Security and Configuration

- Store API keys in environment variables.
- Keep `.env` out of version control.
- Do not expose secret credentials in source code, logs, or screenshots.
- Validate and sanitize user-facing rendered HTML.
- Ensure document routes serve only the intended PDF directory.

## License

Add the license required by your assignment or repository before distributing the project.