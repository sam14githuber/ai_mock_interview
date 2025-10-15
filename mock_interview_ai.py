import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx

# ===============================
# CONFIGURATION
# ===============================
st.set_page_config(page_title="AI Mock Interview", page_icon="🧠", layout="centered")

# Gemini API Key Setup
GEMINI_API_KEY = "AIzaSyDcJXTc_FM2sNqfWrvCrYYsAPKssCPl1AQ"  # Replace with your API key
genai.configure(api_key=GEMINI_API_KEY)


# ===============================
# HELPER FUNCTIONS
# ===============================
def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file."""
    text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        text += page.extract_text()
    return text


def extract_text_from_docx(uploaded_file):
    """Extract text from a DOCX file."""
    doc = docx.Document(uploaded_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def extract_resume_text(uploaded_file):
    """Determine file type and extract text accordingly."""
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        st.error("Please upload a PDF or DOCX resume.")
        return ""


def generate_questions(resume_text, interview_type):
    """Generate 5 interview questions using Gemini."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
    You are a professional mock interviewer.
    Based on the following resume and interview type, generate 5 high-quality interview questions.

    Resume:
    {resume_text}

    Interview Type: {interview_type}

    Format strictly as:
    1. Question 1
    2. Question 2
    ...
    """
    response = model.generate_content(prompt)
    # Return a clean list of questions
    return [q.strip() for q in response.text.split("\n") if q.strip() and q[0].isdigit()]


def generate_feedback(question, answer):
    """Generate feedback for a specific answer."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
    You are an expert interviewer.
    Evaluate the following answer for the question below.

    Question: {question}
    Answer: {answer}

    Provide feedback in this format:
    - Score: x/10
    - Strengths:
    - Weaknesses:
    - Suggestions:
    """
    response = model.generate_content(prompt)
    return response.text


# ===============================
# STREAMLIT APP
# ===============================
st.title("🧩 AI Mock Interview Agent")
st.write("Upload your resume, select an interview type, and answer each question below to get instant feedback!")

uploaded_file = st.file_uploader("📄 Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

if uploaded_file:
    resume_text = extract_resume_text(uploaded_file)

    interview_type = st.selectbox(
        "🎯 Select Interview Type",
        ["Select...", "HR", "Managerial", "General", "Technical"]
    )

    if interview_type != "Select...":
        # Initialize session state
        if "questions" not in st.session_state:
            st.session_state.questions = []
        if "feedbacks" not in st.session_state:
            st.session_state.feedbacks = {}

        # Generate all questions
        if st.button("🚀 Generate Questions"):
            with st.spinner("Generating interview questions..."):
                st.session_state.questions = generate_questions(resume_text, interview_type)
                st.session_state.feedbacks = {}
            st.success("✅ Questions generated successfully!")

        # Display questions one by one with answer and feedback sections
        if st.session_state.questions:
            st.subheader("🧠 Your Mock Interview Questions")

            for i, question in enumerate(st.session_state.questions):
                st.markdown(f"**{question}**")

                # Unique key for each question
                answer_key = f"answer_{i}"
                feedback_key = f"feedback_{i}"

                # Text area for answer
                answer = st.text_area(f"✍️ Your Answer for Question {i+1}", key=answer_key)

                # Feedback button
                if st.button(f"🧩 Get Feedback for Question {i+1}"):
                    if not answer.strip():
                        st.warning("⚠️ Please write your answer before requesting feedback.")
                    else:
                        with st.spinner("Analyzing your answer..."):
                            feedback = generate_feedback(question, answer)
                        st.session_state.feedbacks[feedback_key] = feedback
                        st.success("✅ Feedback Generated!")

                # Show feedback if available
                if feedback_key in st.session_state.feedbacks:
                    st.markdown("**📋 Feedback:**")
                    st.write(st.session_state.feedbacks[feedback_key])

                st.markdown("---")

        # Show overall performance summary if all feedbacks are done
        if st.session_state.feedbacks and len(st.session_state.feedbacks) == len(st.session_state.questions):
            if st.button("📊 Show Overall Performance"):
                all_feedbacks = "\n\n".join(st.session_state.feedbacks.values())
                summary_prompt = f"""
                You are a professional interview evaluator.
                Based on the following feedbacks, summarize the candidate's overall performance.

                Feedbacks:
                {all_feedbacks}

                Format:
                - Average Score:
                - Common Strengths:
                - Common Weaknesses:
                - Final Advice:
                """
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(summary_prompt)
                st.subheader("🏁 Overall Performance Summary")
                st.write(response.text)
