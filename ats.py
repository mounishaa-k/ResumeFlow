import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure the Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to interact with Gemini API
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    try:
        return response.text
    except AttributeError:
        st.error("Error processing the response from the model. Please try again.")
        return None

# Function to extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        text += str(reader.pages[page].extract_text())
    return text

# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analysis,
and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide
best assistance for improving the resumes. Assign the percentage Matching based
on JD and the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response in one single string having the structure:
{{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
"""

# Initialize session state for job descriptions and results
if 'jd_history' not in st.session_state:
    st.session_state.jd_history = []  # Stores list of JDs
if 'results_history' not in st.session_state:
    st.session_state.results_history = []  # Stores corresponding results for each JD
if 'selected_result' not in st.session_state:
    st.session_state.selected_result = None  # Stores the selected result for display
if 'selected_jd' not in st.session_state:
    st.session_state.selected_jd = None  # Stores the selected JD for display

# Set wide page layout for better alignment
st.set_page_config(layout="wide")

# Sidebar: Job Description History
with st.sidebar:
    st.header("Job Description History")
    if st.session_state.jd_history:
        # Display clickable history items
        for i, jd_text in enumerate(st.session_state.jd_history[::-1], 1):
            snippet = jd_text[:50] + '...'  # Display the first 50 characters
            if st.button(snippet, key=f"jd_button_{i}"):  # Unique key for each button
                # Ensure valid index for jd_history and results_history
                if len(st.session_state.jd_history) >= i and len(st.session_state.results_history) >= i:
                    result_index = len(st.session_state.jd_history) - i
                    st.session_state.selected_result = st.session_state.results_history[result_index]
                    st.session_state.selected_jd = st.session_state.jd_history[result_index]
                else:
                    st.error("Invalid selection, please try again.")
    else:
        st.write("No job descriptions submitted yet.")

# Main content section
st.title("ResumeFlow 📝")
st.text("Connecting great Resumes with great Jobs")

st.subheader("Analyze Your Resume")

# Show the selected job description in the input area, if available
if st.session_state.selected_jd:
    jd = st.text_area("Paste the Job Description", st.session_state.selected_jd)
else:
    jd = st.text_area("Paste the Job Description", "")

# File uploader for the resume
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload the pdf")

# Button to trigger the matching process
submit = st.button("Check➤")

# Process the job description and resume
if submit:
    if uploaded_file and jd:
        # Append new JD to history if not already in it
        if jd not in st.session_state.jd_history:
            st.session_state.jd_history.append(jd)

        # Extract text from the uploaded resume
        resume_text = input_pdf_text(uploaded_file)

        # Generate response using Gemini API
        response = get_gemini_response(input_prompt.format(text=resume_text, jd=jd))

        if response:
            try:
                # Parse the response JSON
                parsed_response = json.loads(response)

                # Store the parsed result in results history
                st.session_state.results_history.append(parsed_response)

                # Display the result immediately
                st.subheader(f"JD Match: {parsed_response['JD Match']}")
                st.write(f"Missing Keywords: {parsed_response['MissingKeywords']}")
                st.write(f"Profile Summary: {parsed_response['Profile Summary']}")
            except json.JSONDecodeError:
                st.error("There was an error parsing the model's response. Please try again.")
    else:
        st.warning("Please provide both a job description and a resume.")

# Display the selected result and job description from the history, if available
if st.session_state.selected_result:
    st.subheader(f"JD Match: {st.session_state.selected_result['JD Match']}")
    st.write(f"Missing Keywords: {st.session_state.selected_result['MissingKeywords']}")
    st.write(f"Profile Summary: {st.session_state.selected_result['Profile Summary']}")
