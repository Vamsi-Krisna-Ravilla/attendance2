import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import os

# Configure Streamlit page
st.set_page_config(
    page_title="RVIT Faculty Feedback System",
    page_icon="📚",
    layout="wide"
)

# Initialize session state variables
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# Constants
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
FEEDBACK_FILE = "feedback.xlsx"

# Create feedback file if it doesn't exist
if not os.path.exists(FEEDBACK_FILE):
    initial_df = pd.DataFrame(columns=[
        'Timestamp', 'Month', 'Program', 'Year_Semester', 'Branch', 
        'Section_Type', 'Hall_Ticket', 'Student_Name', 'Gender', 
        'Email', 'Mobile', 'Subject_Ratings', 'Lab_Feedback', 
        'Overall_Rating', 'Suggestions'
    ])
    initial_df.to_excel(FEEDBACK_FILE, index=False)

# Load data configurations
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
          'August', 'September', 'October', 'November', 'December']

ACADEMIC_YEARS = ['2020', '2021', '2022', '2023', '2024']

BRANCHES = {
    'CSE': 'Computer Science and Engineering [CSE]',
    'CSE(AIML)': 'CSE (Artificial Intelligence & Machine Learning)',
    'CSE(DS)': 'Computer Science and Engineering(Data Science)',
    'ECE': 'Electronics and Communication Engineering',
    'EVT': 'Electronics Engineering (VLSI Design & Tech)'
}

YEAR_SEMESTERS = {
    'I-1': 'I Year B.Tech I Semester',
    'I-2': 'I Year B.Tech II Semester',
    'II-1': 'II Year B.Tech I Semester',
    'II-2': 'II Year B.Tech II Semester',
    'III-1': 'III Year B.Tech I Semester',
    'III-2': 'III Year B.Tech II Semester',
    'IV-1': 'IV Year B.Tech I Semester'
}

SECTION_TYPES = {
    'NOT_APPLICABLE': 'Not Applicable (Select, If 1st Year B.Tech)',
    'CRT': 'CRT',
    'NON-CRT': 'NON-CRT'
}

# Function to load feedback data
def load_feedback_data():
    try:
        return pd.read_excel(FEEDBACK_FILE)
    except:
        return pd.DataFrame()

# Admin login function
def admin_login():
    st.sidebar.title("Admin Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Successfully logged in as admin!")
            st.rerun()
        else:
            st.error("Invalid credentials!")

# Admin dashboard function
def show_admin_dashboard():
    st.title("Admin Dashboard - Faculty Feedback Analysis")
    
    # Load data
    df = load_feedback_data()
    
    if df.empty:
        st.warning("No feedback data available yet.")
        return
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Responses", len(df))
    with col2:
        avg_rating = df['Overall_Rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.2f}/5")
    with col3:
        latest_response = df['Timestamp'].max()
        st.metric("Latest Response", latest_response)
    with col4:
        total_branches = df['Branch'].nunique()
        st.metric("Total Branches", total_branches)

    # Filters
    st.sidebar.title("Filters")
    selected_branch = st.sidebar.multiselect("Select Branch", df['Branch'].unique())
    selected_semester = st.sidebar.multiselect("Select Semester", df['Year_Semester'].unique())
    
    # Apply filters
    filtered_df = df.copy()
    if selected_branch:
        filtered_df = filtered_df[filtered_df['Branch'].isin(selected_branch)]
    if selected_semester:
        filtered_df = filtered_df[filtered_df['Year_Semester'].isin(selected_semester)]

    # Visualizations
    st.subheader("Feedback Analysis")
    
    # Branch-wise distribution
    fig1 = px.pie(filtered_df, names='Branch', title='Feedback Distribution by Branch')
    st.plotly_chart(fig1)
    
    # Rating distribution
    fig2 = px.histogram(filtered_df, x='Overall_Rating', 
                       title='Overall Rating Distribution',
                       nbins=5)
    st.plotly_chart(fig2)
    
    # Subject-wise average ratings
    if 'Subject_Ratings' in filtered_df.columns:
        subject_ratings = pd.json_normalize(filtered_df['Subject_Ratings'].apply(eval))
        subject_means = subject_ratings.mean()
        
        fig3 = px.bar(x=subject_means.index, y=subject_means.values,
                     title='Average Subject Ratings',
                     labels={'x': 'Subject', 'y': 'Average Rating'})
        st.plotly_chart(fig3)
    
    # Recent feedback table
    st.subheader("Recent Feedback")
    recent_feedback = filtered_df[['Timestamp', 'Branch', 'Year_Semester', 
                                 'Overall_Rating', 'Suggestions']].tail(10)
    st.dataframe(recent_feedback)
    
    # Download data option
    st.sidebar.download_button(
        label="Download Full Data",
        data=df.to_csv(index=False),
        file_name="feedback_data.csv",
        mime="text/csv"
    )

# Student feedback form function
def show_feedback_form():
    st.title("RVIT - Student Feedback Form")
    st.write("Please provide your valuable feedback")
    
    with st.form("feedback_form"):
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            month = st.selectbox("Select Current Month *", MONTHS)
            branch = st.selectbox("Select Branch/Discipline *", 
                                list(BRANCHES.keys()), 
                                format_func=lambda x: BRANCHES[x])
            year_sem = st.selectbox("Choose your Current/Last Academic Year and Semester *",
                                  list(YEAR_SEMESTERS.keys()),
                                  format_func=lambda x: YEAR_SEMESTERS[x])
        
        with col2:
            section_type = st.selectbox("Section Type *",
                                      list(SECTION_TYPES.keys()),
                                      format_func=lambda x: SECTION_TYPES[x])
            hall_ticket = st.text_input("Student Hall Ticket Number *")
            student_name = st.text_input("Student Name *")
        
        # Personal Information
        col3, col4 = st.columns(2)
        
        with col3:
            gender = st.radio("Gender *", ["Male", "Female"])
            email = st.text_input("Personal Email ID *")
        
        with col4:
            mobile = st.text_input("Student/Parent Mobile Number *")
            overall_rating = st.slider("Rate your overall Academic Experience at RVIT *",
                                     1, 5, 3)
        
        # Subject Ratings
        st.subheader("Subject Feedback")
        subject_ratings = {}
        
        # Example subjects (modify based on your needs)
        subjects = ["Mathematics", "Physics", "Chemistry", "Programming"]
        for subject in subjects:
            rating = st.slider(f"Rate {subject}", 1, 5, 3)
            subject_ratings[subject] = rating
        
        # Lab Feedback
        st.subheader("Lab Feedback")
        lab_feedback = {}
        
        # Example labs (modify based on your needs)
        labs = ["Physics Lab", "Chemistry Lab", "Programming Lab"]
        for lab in labs:
            col5, col6, col7 = st.columns(3)
            with col5:
                explained = st.checkbox(f"Experiments explained ({lab})")
            with col6:
                executed = st.checkbox(f"Experiments executed ({lab})")
            with col7:
                records = st.checkbox(f"Records corrected ({lab})")
            lab_feedback[lab] = {
                "explained": explained,
                "executed": executed,
                "records": records
            }
        
        suggestions = st.text_area("Suggestions/Recommendations")
        
        submit_button = st.form_submit_button("Submit Feedback")
        
        if submit_button:
            # Validate required fields
            if not all([month, branch, year_sem, hall_ticket, student_name, 
                       email, mobile]):
                st.error("Please fill all required fields")
                return
            
            # Create feedback entry
            feedback_entry = {
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Month': month,
                'Program': 'B.Tech',
                'Year_Semester': year_sem,
                'Branch': branch,
                'Section_Type': section_type,
                'Hall_Ticket': hall_ticket,
                'Student_Name': student_name,
                'Gender': gender,
                'Email': email,
                'Mobile': mobile,
                'Subject_Ratings': str(subject_ratings),
                'Lab_Feedback': str(lab_feedback),
                'Overall_Rating': overall_rating,
                'Suggestions': suggestions
            }
            
            # Load existing data and append new entry
            df = load_feedback_data()
            df = pd.concat([df, pd.DataFrame([feedback_entry])], ignore_index=True)
            df.to_excel(FEEDBACK_FILE, index=False)
            
            st.success("Thank you! Your feedback has been submitted successfully.")

# Main app logic
def main():
    # Sidebar
    if not st.session_state.admin_logged_in:
        admin_login()
    else:
        if st.sidebar.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
    
    # Main content
    if st.session_state.admin_logged_in:
        show_admin_dashboard()
    else:
        show_feedback_form()

if __name__ == "__main__":
    main()