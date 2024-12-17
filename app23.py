import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import numpy as np

# Configure Streamlit page
st.set_page_config(
    page_title="RVIT - Student Feedback Form",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
FEEDBACK_FILE = "feedback.xlsx"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Rating scale with values
RATING_OPTIONS = [
    "Excellent (5)",
    "Very Good (4)", 
    "Good (3)",
    "Fair (2)",
    "Poor (1)"
]

def safe_json_loads(data):
    """Safely load JSON data with error handling"""
    if pd.isna(data):
        return {}
    try:
        if isinstance(data, dict):
            return data
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        try:
            return eval(str(data))
        except:
            return {}

def get_rating_value(rating_text):
    """Get numeric value from rating safely"""
    try:
        return int(rating_text.split('(')[-1].split(')')[0])
    except (IndexError, ValueError):
        return 0

# Extended Academic Structure
ACADEMIC_STRUCTURE = {
    "B.Tech": {
        "CSE": {
            "I Year I Semester": {
                "subjects": {
                    "LAC": "LINEAR ALGEBRA & CALCULUS",
                    "BCME": "BASIC CIVIL & MECHANICAL ENGINEERING",
                    "CHEM": "CHEMISTRY",
                    "CP": "COMPUTER PROGRAMMING",
                    "ENG": "COMMUNICATIVE ENGLISH"
                },
                "labs": {
                    "CP_LAB": "CP Lab",
                    "BCME_LAB": "BCME Lab",
                    "ENG_LAB": "English Lab",
                    "CHEM_LAB": "Chemistry Lab"
                }
            },
            "I Year II Semester": {
                "subjects": {
                    "DEC": "DIFFERENTIAL EQUATIONS & CALCULUS",
                    "BEEE": "BASIC ELECTRICAL & ELECTRONICS",
                    "PHY": "ENGINEERING PHYSICS",
                    "DS": "DATA STRUCTURES",
                    "EG": "ENGINEERING GRAPHICS"
                },
                "labs": {
                    "DS_LAB": "DS Lab",
                    "BEEE_LAB": "BEEE Lab",
                    "EG_LAB": "EG Lab",
                    "PHY_LAB": "Physics Lab"
                }
            },
            "II Year I Semester": {
                "subjects": {
                    "DMS": "DISCRETE MATHEMATICAL STRUCTURES",
                    "DBMS": "DATABASE MANAGEMENT SYSTEMS",
                    "COA": "COMPUTER ORGANIZATION & ARCHITECTURE",
                    "OOP": "OBJECT ORIENTED PROGRAMMING",
                    "OS": "OPERATING SYSTEMS"
                },
                "labs": {
                    "DBMS_LAB": "DBMS Lab",
                    "OOP_LAB": "OOP Lab",
                    "OS_LAB": "OS Lab"
                }
            }
            # Add more semesters as needed
        }
    },
    "Diploma": {
        "Computer Science": {
            "I Year I Semester": {
                "subjects": {
                    "MATH1": "ENGINEERING MATHEMATICS-I",
                    "ENG1": "ENGLISH-I",
                    "CFUND": "COMPUTER FUNDAMENTALS",
                    "DTECH": "DIGITAL TECHNIQUES",
                    "PROG1": "PROGRAMMING IN C"
                },
                "labs": {
                    "COMP_LAB": "Computer Lab",
                    "DIGITAL_LAB": "Digital Lab",
                    "C_LAB": "C Programming Lab"
                }
            }
        }
    }
}

def initialize_feedback_file():
    """Initialize feedback Excel file if it doesn't exist"""
    try:
        if not os.path.exists(FEEDBACK_FILE):
            df = pd.DataFrame(columns=[
                'Timestamp', 'Program', 'Branch', 'Year_Semester', 'Hall_Ticket', 
                'Student_Name', 'Subject_Ratings', 'Lab_Feedback',
                'Overall_Rating', 'Suggestions'
            ])
            df.to_excel(FEEDBACK_FILE, index=False)
            st.success("Feedback file initialized successfully")
    except Exception as e:
        st.error(f"Error initializing feedback file: {str(e)}")

def analyze_feedback_data(df):
    """Analyze feedback data and return metrics with error handling"""
    try:
        if df.empty:
            return None
        
        # Convert string representations to dictionaries
        df['Subject_Ratings'] = df['Subject_Ratings'].apply(safe_json_loads)
        df['Lab_Feedback'] = df['Lab_Feedback'].apply(safe_json_loads)
        
        # Calculate metrics
        total_responses = len(df)
        avg_rating = df['Overall_Rating'].mean()
        recent_responses = len(df[pd.to_datetime(df['Timestamp']) >= (datetime.now() - timedelta(days=7))])
        
        # Subject-wise analysis
        subject_ratings = []
        for _, row in df.iterrows():
            try:
                ratings = row['Subject_Ratings']
                if isinstance(ratings, dict):
                    for subject, rating in ratings.items():
                        subject_ratings.append({
                            'Subject': subject,
                            'Rating': float(rating),
                            'Program': row['Program'],
                            'Branch': row['Branch']
                        })
            except Exception:
                continue
        
        subject_df = pd.DataFrame(subject_ratings)
        subject_avg = subject_df.groupby(['Program', 'Subject'])['Rating'].mean() if not subject_df.empty else pd.Series()
        
        # Program and branch analysis
        program_avg = df.groupby('Program')['Overall_Rating'].mean()
        branch_avg = df.groupby(['Program', 'Branch'])['Overall_Rating'].mean()
        
        return {
            'total_responses': total_responses,
            'avg_rating': avg_rating,
            'recent_responses': recent_responses,
            'subject_avg': subject_avg,
            'program_avg': program_avg,
            'branch_avg': branch_avg
        }
    except Exception as e:
        st.error(f"Error analyzing feedback data: {str(e)}")
        return None

def show_admin_dashboard():
    """Display admin dashboard with error handling"""
    try:
        st.title("Admin Dashboard - Feedback Analysis")
        
        if not os.path.exists(FEEDBACK_FILE):
            st.warning("No feedback data available yet.")
            return
        
        try:
            df = pd.read_excel(FEEDBACK_FILE)
        except Exception as e:
            st.error(f"Error reading feedback file: {e}")
            return
        
        if df.empty:
            st.warning("No feedback submissions yet.")
            return
        
        metrics = analyze_feedback_data(df)
        if metrics is None:
            st.warning("Unable to process feedback metrics.")
            return
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Responses", metrics['total_responses'])
        with col2:
            st.metric("Average Rating", f"{metrics['avg_rating']:.2f}/5")
        with col3:
            st.metric("Recent Responses (7 days)", metrics['recent_responses'])
        with col4:
            st.metric("Total Programs", len(metrics['program_avg']))
        
        # Filters
        st.sidebar.subheader("Filters")
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now())
        )
        selected_programs = st.sidebar.multiselect(
            "Select Programs",
            options=df['Program'].unique()
        )
        selected_branches = st.sidebar.multiselect(
            "Select Branches",
            options=df['Branch'].unique()
        )
        
        # Apply filters
        mask = (pd.to_datetime(df['Timestamp']).dt.date >= date_range[0]) & \
               (pd.to_datetime(df['Timestamp']).dt.date <= date_range[1])
        if selected_programs:
            mask &= df['Program'].isin(selected_programs)
        if selected_branches:
            mask &= df['Branch'].isin(selected_branches)
        
        filtered_df = df[mask]
        
        # Visualizations
        st.subheader("Program and Branch Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_program = px.pie(
                filtered_df,
                names='Program',
                title='Feedback Distribution by Program',
                template="plotly_dark"
            )
            st.plotly_chart(fig_program, use_container_width=True)
        
        with col2:
            fig_branch = px.pie(
                filtered_df,
                names='Branch',
                title='Feedback Distribution by Branch',
                template="plotly_dark"
            )
            st.plotly_chart(fig_branch, use_container_width=True)
        
        # Rating distribution
        fig_rating = px.histogram(
            filtered_df,
            x='Overall_Rating',
            title='Rating Distribution',
            template="plotly_dark",
            nbins=5
        )
        st.plotly_chart(fig_rating, use_container_width=True)
        
        # Recent feedback table
        st.subheader("Recent Feedback")
        recent = filtered_df.sort_values('Timestamp', ascending=False).head(10)
        st.dataframe(
            recent[['Timestamp', 'Program', 'Branch', 'Student_Name', 'Overall_Rating', 'Suggestions']],
            use_container_width=True
        )
        
        # Export functionality
        st.sidebar.subheader("Export Data")
        export_format = st.sidebar.selectbox(
            "Select Format",
            ["CSV", "Excel"]
        )
        
        if st.sidebar.button("Export"):
            try:
                if export_format == "CSV":
                    filtered_df.to_csv("feedback_export.csv", index=False)
                    st.sidebar.success("Data exported to feedback_export.csv")
                else:
                    filtered_df.to_excel("feedback_export.xlsx", index=False)
                    st.sidebar.success("Data exported to feedback_export.xlsx")
            except Exception as e:
                st.sidebar.error(f"Error exporting data: {str(e)}")
    
    except Exception as e:
        st.error(f"Error in admin dashboard: {str(e)}")

def validate_input(hall_ticket, student_name):
    """Validate user input"""
    if not hall_ticket or not student_name:
        return False, "Please fill all required fields"
    if len(hall_ticket) < 5:
        return False, "Hall ticket number is too short"
    if len(student_name) < 2:
        return False, "Student name is too short"
    return True, ""

def show_feedback_form():
    """Display student feedback form with program selection"""
    try:
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h1>RVIT - Student Feedback Form</h1>
                <h2>RV INSTITUTE OF TECHNOLOGY</h2>
                <h3>NAAC 'A' GRADE</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Program Selection
        program = st.radio(
            "Select Program",
            options=list(ACADEMIC_STRUCTURE.keys()),
            horizontal=True
        )
        
        with st.form("feedback_form"):
            # Basic Information
            st.subheader("Basic Information")
            
            col1, col2 = st.columns(2)
            with col1:
                branch = st.selectbox(
                    "Select Branch/Discipline *",
                    options=list(ACADEMIC_STRUCTURE[program].keys())
                )
                year_sem = st.selectbox(
                    "Year and Semester *",
                    options=list(ACADEMIC_STRUCTURE[program][branch].keys())
                )
            
            with col2:
                hall_ticket = st.text_input("Hall Ticket Number *")
                student_name = st.text_input("Student Name *")
            
            # Subject Feedback
            st.subheader("Subject Feedback")
            subject_ratings = {}
            for subject_code, subject_name in ACADEMIC_STRUCTURE[program][branch][year_sem]["subjects"].items():
                rating = st.radio(
                    f"{subject_name} *",
                    options=RATING_OPTIONS,
                    horizontal=True,
                    key=f"subject_{subject_code}"
                )
                subject_ratings[subject_code] = get_rating_value(rating)
            
            # Lab Feedback
            st.subheader("Lab Feedback")
            lab_feedback = {}
            for lab_code, lab_name in ACADEMIC_STRUCTURE[program][branch][year_sem]["labs"].items():
                st.write(f"**{lab_name}**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    explained = st.checkbox(f"Experiments explained ({lab_name})")
                with col2:
                    executed = st.checkbox(f"Experiments executed ({lab_name})")
                with col3:
                    records = st.checkbox(f"Records corrected ({lab_name})")
                
                lab_feedback[lab_code] = {
                    "explained": explained,
                    "executed": executed,
                    "records": records
                }
            
            # Overall Feedback
            st.subheader("Overall Feedback")
            overall_rating = st.radio(
                "Overall Experience Rating *",
                options=RATING_OPTIONS,
                horizontal=True,
                key="overall_rating"
            )
            suggestions = st.text_area("Suggestions/Recommendations")
            
            # Submit Button
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                is_valid, error_message = validate_input(hall_ticket, student_name)
                if not is_valid:
                    st.error(error_message)
                    return
                
                try:
                    feedback_data = {
                        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Program': program,
                        'Branch': branch,
                        'Year_Semester': year_sem,
                        'Hall_Ticket': hall_ticket,
                        'Student_Name': student_name,
                        'Subject_Ratings': json.dumps(subject_ratings),
                        'Lab_Feedback': json.dumps(lab_feedback),
                        'Overall_Rating': get_rating_value(overall_rating),'Suggestions': suggestions
                    }
                    
                    try:
                        if os.path.exists(FEEDBACK_FILE):
                            # Read existing data
                            df = pd.read_excel(FEEDBACK_FILE)
                            
                            # Check for duplicate submissions
                            if not df.empty and len(df[df['Hall_Ticket'] == hall_ticket]) > 0:
                                st.error("You have already submitted feedback. Multiple submissions are not allowed.")
                                return
                        else:
                            # Create new DataFrame if file doesn't exist
                            df = pd.DataFrame()
                        
                        # Add new feedback
                        df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
                        
                        # Save to Excel
                        df.to_excel(FEEDBACK_FILE, index=False)
                        
                        # Show success message
                        st.success("Thank you! Your feedback has been submitted successfully.")
                        st.balloons()
                        
                        # Clear form (by rerunning the app)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error saving feedback: {str(e)}")
                        print(f"Error saving feedback: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error processing feedback: {str(e)}")
                    print(f"Error processing feedback: {str(e)}")
    
    except Exception as e:
        st.error(f"Error displaying feedback form: {str(e)}")
        print(f"Error displaying feedback form: {str(e)}")

def create_backup():
    """Create backup of feedback data"""
    try:
        if os.path.exists(FEEDBACK_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"feedback_backup_{timestamp}.xlsx"
            df = pd.read_excel(FEEDBACK_FILE)
            df.to_excel(backup_file, index=False)
            return True
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False

def main():
    """Main application function"""
    try:
        # Initialize session state
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False
        
        # Initialize feedback file
        initialize_feedback_file()
        
        # Create daily backup
        if 'last_backup' not in st.session_state:
            st.session_state.last_backup = None
        
        # Check if backup is needed (once per day)
        current_date = datetime.now().date()
        if (st.session_state.last_backup is None or 
            st.session_state.last_backup < current_date):
            if create_backup():
                st.session_state.last_backup = current_date
        
        # Admin Login in Sidebar
        with st.sidebar:
            if not st.session_state.admin_logged_in:
                st.title("Admin Login")
                username = st.text_input("Username", key="admin_username")
                password = st.text_input("Password", type="password", key="admin_password")
                
                if st.button("Login"):
                    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials!")
            else:
                if st.button("Logout"):
                    st.session_state.admin_logged_in = False
                    st.rerun()
        
        # Main content based on login state
        if st.session_state.admin_logged_in:
            show_admin_dashboard()
        else:
            show_feedback_form()
    
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        print(f"Application Error: {str(e)}")

if __name__ == "__main__":
    main()