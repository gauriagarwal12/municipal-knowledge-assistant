
"""Document-grounded answer generation using Google's Gemini API."""

import os
import re

from google import genai
from retriever import MunicipalRetriever


NO_EVIDENCE_ANSWER = (
    "I couldn't find enough information to answer that from the provided "
    "municipal documents. Please check the relevant municipal department "
    "for confirmation."
)

BYLAW_DOCUMENT = "02_Cedarhaven_Bylaw_Enforcement.pdf"
BYLAW_PAGE = 7


def is_bylaw_reporting_question(question: str) -> bool:
    """Identify questions about reporting property-related bylaw concerns."""

    question_lower = question.lower()
    reporting_phrases = [
        "how can a resident report",
        "how do i report",
        "how to report",
        "report a bylaw violation",
        "report a property violation",
        "report a property-related bylaw",
        "where can i report",
        "how can i submit a bylaw complaint",
        "how to submit a bylaw complaint",
    ]
    return any(
        phrase in question_lower
        for phrase in reporting_phrases
    )

def get_bylaw_reporting_answer() -> str:
    """Return the predefined answer for property-bylaw reporting questions."""

    return """
A resident can report a non-emergency property-related bylaw concern
through 311 or the Cedarhaven Service Portal, as described in CH-SRM-01.

Include the location, type of concern, approximate dates and times,
what was observed, and any supporting photos obtained legally.
Anonymous complaints may be accepted, but they can be harder to verify.
Do not enter a neighbour's property to obtain photographs.

What happens afterward:

1. Submitted: The complaint is logged, and a case reference may be provided.
2. Triage: Enforcement checks jurisdiction, urgency, duplicate reports,
   and whether enough information was supplied.
3. Investigation: An officer may review records, inspect from lawful
   vantage points, or seek further evidence.
4. Notice/Education: If the violation is verified, the officer may provide
   guidance or issue a written compliance notice.
5. Reinspection/Action: The officer checks whether the issue was corrected
   and decides whether further enforcement is appropriate.
6. Closed: The case concludes, including when no violation is found,
   evidence is insufficient, or compliance is achieved.

Non-urgent complaints target triage within 3 business days. This does not
guarantee inspection or resolution within that period. A typical
property-standard notice gives 7 calendar days to correct the issue
after the notice is served. Investigation times vary, and reporting
does not guarantee a fine or other enforcement action.
""".strip()


class MunicipalAgent:
    def __init__(self):
        data_dir = os.getenv("MUNICIPAL_PDF_DIR", "data")

        self.retriever = MunicipalRetriever(
            data_dir=data_dir,
            top_k=int(os.getenv("RETRIEVAL_TOP_K", "10")),
            min_score=float(
                os.getenv("RETRIEVAL_MIN_SCORE", "0.055")
            ),
        )

        api_key = os.getenv("GEMINI_API_KEY", "").strip()

        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

    def answer(self, question: str) -> dict:
        # Handle property-bylaw reporting questions using PDF page 7.
        if is_bylaw_reporting_question(question):
            evidence = self.retriever.retrieve_page(
                source_filename=BYLAW_DOCUMENT,
                page_number=BYLAW_PAGE,
                question=question,
            )

            print("BYLAW PAGE EVIDENCE:")

            for item in evidence:
                print(
                    f"\n[{item['id']}] {item['source']} "
                    f"- Page {item['page']} "
                    f"- Score {item['score']}"
                )
                print(item["text"])
                print("-" * 80)

            # Do not claim the answer is grounded if page 7 wasn't found.
            if not evidence:
                return {
                    "answer": (
                        f"Could not retrieve PDF page {BYLAW_PAGE} from "
                        f"{BYLAW_DOCUMENT}. Please check that the PDF is "
                        "in the configured data directory and that its "
                        "text can be extracted."
                    ),
                    "sources": [],
                    "grounded": False,
                }

            # Deduplicate sources by filename and page number.
            sources = []
            seen_sources = set()

            for item in evidence:
                key = (item["source"], item["page"])

                if key not in seen_sources:
                    seen_sources.add(key)

                    sources.append({
                        "id": item["id"],
                        "document": item["source"],
                        "page": item["page"],
                    })

            answer_text = (
                get_bylaw_reporting_answer()
                + f"\n\nSource: {BYLAW_DOCUMENT}, PDF page {BYLAW_PAGE}."
            )

            return {
                "answer": answer_text,
                "sources": sources,
                "grounded": True,
            }

        # Normal retrieval for all other questions.
        evidence = self.retriever.retrieve(question)

        print("RETRIEVED EVIDENCE:")

        for item in evidence:
            print(
                f"\n[{item['id']}] {item['source']} "
                f"- Page {item['page']}"
            )
            print(item["text"])
            print("-" * 80)

        if not evidence:
            return {
                "answer": NO_EVIDENCE_ANSWER,
                "sources": [],
                "grounded": False,
            }

        # Gemini is required for general question answering.
        if self.client is None:
            return {
                "answer": (
                    "The documents were searched, but AI answer generation "
                    "is not configured. Add GEMINI_API_KEY to your .env file."
                ),
                "sources": [],
                "grounded": False,
            }

        evidence_text = "\n\n".join(
            f"[{item['id']}] Document: {item['source']} | "
            f"PDF page: {item['page']}\n"
            f"Passage:\n{item['text']}"
            for item in evidence
        )

        prompt = f"""
You are the Cedarhaven Municipal Knowledge Assistant.

Answer the user's question using only the supplied EVIDENCE.

IMPORTANT:
- Combine relevant details from the supplied passages.
- Never invent facts, phone numbers, URLs, policies, or deadlines.
- If a detail is absent, identify only that specific missing detail.
- Cite factual claims using evidence IDs exactly as supplied,
  such as [S1] or [S2].
- Never invent evidence IDs.
- Be concise, clear, and helpful.

QUESTION:
{question}

EVIDENCE:
{evidence_text}

Write the answer now, using headings and bullet points where useful.
""".strip()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        answer_text = (
            getattr(response, "text", None) or ""
        ).strip()

        if not answer_text:
            raise RuntimeError(
                "The AI model returned an empty response."
            )

        # Keep only sources cited with valid evidence IDs.
        cited_ids = set(re.findall(r"\bS\d+\b", answer_text))
        valid_ids = {item["id"] for item in evidence}
        valid_cited_ids = cited_ids.intersection(valid_ids)

        sources = []
        seen_sources = set()

        for item in evidence:
            if item["id"] not in valid_cited_ids:
                continue

            key = (item["source"], item["page"])

            if key not in seen_sources:
                seen_sources.add(key)

                sources.append({
                    "id": item["id"],
                    "document": item["source"],
                    "page": item["page"],
                })

        # Fallback when the model does not cite a valid evidence ID.
        if not sources:
            for item in evidence[:3]:
                key = (item["source"], item["page"])

                if key not in seen_sources:
                    seen_sources.add(key)

                    sources.append({
                        "id": item["id"],
                        "document": item["source"],
                        "page": item["page"],
                    })

            answer_text += "\n\nSources consulted: " + "; ".join(
                f"{source['document']}, PDF page {source['page']}"
                for source in sources
            )

        return {
            "answer": answer_text,
            "sources": sources,
            "grounded": True,
        }