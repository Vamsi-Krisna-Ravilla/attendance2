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
ADMIN_USERNAME = "a"
ADMIN_PASSWORD = "a"

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
    """Initialize feedback Excel file with multiple sheets if it doesn't exist"""
    try:
        if not os.path.exists(FEEDBACK_FILE):
            # Create a new Excel writer object
            with pd.ExcelWriter(FEEDBACK_FILE, engine='openpyxl') as writer:
                # Create feedback sheet
                feedback_df = pd.DataFrame(columns=[
                    'Timestamp', 'Program', 'Branch', 'Year_Semester', 'Hall_Ticket', 
                    'Student_Name', 'Faculty_Name', 'Subject_Ratings', 'Lab_Feedback',
                    'Overall_Rating', 'Suggestions'
                ])
                feedback_df.to_excel(writer, sheet_name='feedback', index=False)
                
                # Create faculty sheet with sample data
                faculty_df = pd.DataFrame({
                    'Faculty_Name': [
                        'Dr.MD SHABANA SULTHANA(CHEC7006)',
                        'P LALITHA SOWJANAYA(CHEC7007)',
                        'Dr. A Raghavendra Rao(CHEC7020)',
                        # Add other faculty names from your list
                    ]
                })
                faculty_df.to_excel(writer, sheet_name='faculty', index=False)
            
            st.success("Feedback file initialized successfully")
    except Exception as e:
        st.error(f"Error initializing feedback file: {str(e)}")

def get_faculty_list():
    """Get list of faculty from the faculty sheet"""
    try:
        if os.path.exists(FEEDBACK_FILE):
            # Read the faculty sheet
            faculty_df = pd.read_excel(FEEDBACK_FILE, sheet_name='faculty')
            return faculty_df['Faculty_Name'].tolist()
        return []
    except Exception as e:
        st.error(f"Error reading faculty list: {str(e)}")
        return []



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

def process_faculty_data(df):
    """Process faculty data from feedback submissions"""
    try:
        faculty_data = []
        for _, row in df.iterrows():
            try:
                faculty_selections = json.loads(row['Faculty_Selections'])
                subject_ratings = json.loads(row['Subject_Ratings'])
                timestamp = pd.to_datetime(row['Timestamp'])
                month_year = timestamp.strftime('%b%Y')
                
                for subject_code, faculty_name in faculty_selections.items():
                    if faculty_name and subject_code in subject_ratings:
                        faculty_data.append({
                            'Faculty_Name': faculty_name,
                            'Subject': subject_code,
                            'Rating': float(subject_ratings[subject_code]),
                            'Month': month_year,
                            'Program': row['Program'],
                            'Branch': row['Branch']
                        })
            except Exception as e:
                continue
        return pd.DataFrame(faculty_data) if faculty_data else pd.DataFrame()
    except Exception as e:
        print(f"Error processing faculty data: {str(e)}")
        return pd.DataFrame()


def show_admin_dashboard():
    """Display admin dashboard with complete data management and analytics capabilities"""
    try:
        # Create side navigation
        navigation = st.sidebar.radio(
            "Navigation",
            ["Data Management", "Faculty Workload", "Reset Credentials"]
        )

        if navigation == "Data Management":
            st.title("Data Management")
            
            # Sub-navigation for data management
            sub_nav = st.radio(
                "Select Option",
                ["Edit Data", "Bulk Upload"]
            )

            if sub_nav == "Edit Data":
                # Sheet selector
                sheet_type = st.selectbox(
                    "Select Sheet",
                    ["Feedback", "Faculty", "Students"]
                )
                
                try:
                    # Load and display data in editable format
                    df = pd.read_excel(FEEDBACK_FILE, sheet_name=sheet_type.lower())
                    
                    # Add search/filter functionality
                    search_term = st.text_input(
                        "Search/Filter Data",
                        key=f"search_{sheet_type}"
                    )
                    if search_term:
                        mask = df.astype(str).apply(
                            lambda x: x.str.contains(search_term, case=False)
                        ).any(axis=1)
                        df = df[mask]
                    
                    # Handle timestamp and configure columns
                    if 'Timestamp' in df.columns:
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    
                    column_config = {
                        "Timestamp": st.column_config.DatetimeColumn(
                            "Timestamp",
                            format="DD/MM/YYYY HH:mm:ss",
                            required=True
                        ),
                        "Subject_Ratings": st.column_config.TextColumn(
                            "Subject_Ratings",
                            width="large"
                        ),
                        "Lab_Feedback": st.column_config.TextColumn(
                            "Lab_Feedback",
                            width="large"
                        )
                    }
                    
                    # Display editable dataframe
                    edited_df = st.data_editor(
                        df,
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"editor_{sheet_type}",
                        column_config=column_config,
                        disabled=["Subject_Ratings", "Lab_Feedback"]
                    )
                    
                    # Save and export options
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button("Save Changes", key=f"save_{sheet_type}"):
                            try:
                                with pd.ExcelWriter(FEEDBACK_FILE, mode='a', if_sheet_exists='replace') as writer:
                                    edited_df.to_excel(writer, sheet_name=sheet_type.lower(), index=False)
                                st.success("Changes saved successfully!")
                            except Exception as e:
                                st.error(f"Error saving changes: {str(e)}")
                    
                    with col2:
                        if st.button("Export Current View", key=f"export_{sheet_type}"):
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                export_file = f"{sheet_type}_export_{timestamp}.xlsx"
                                edited_df.to_excel(export_file, index=False)
                                st.success(f"Data exported to {export_file}")
                            except Exception as e:
                                st.error(f"Error exporting data: {str(e)}")
                
                except Exception as e:
                    st.error(f"Error loading/displaying data: {str(e)}")
            
            elif sub_nav == "Bulk Upload":
                st.subheader("Upload/Download Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Upload Complete Workbook")
                    uploaded_file = st.file_uploader(
                        "Drop Excel file here",
                        type=["xlsx", "xls"]
                    )
                    
                    if uploaded_file:
                        try:
                            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            if os.path.exists(FEEDBACK_FILE):
                                os.rename(FEEDBACK_FILE, backup_name)
                                st.info(f"Backup created: {backup_name}")
                            
                            with open(FEEDBACK_FILE, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            st.success("Workbook uploaded successfully!")
                        except Exception as e:
                            st.error(f"Error uploading file: {str(e)}")
                
                with col2:
                    st.write("Download Options")
                    if os.path.exists(FEEDBACK_FILE):
                        with open(FEEDBACK_FILE, "rb") as f:
                            st.download_button(
                                "Download Complete Workbook",
                                f,
                                file_name="feedback_complete.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

        elif navigation == "Faculty Workload":
            st.title("Faculty Workload Analysis")
            
            if not os.path.exists(FEEDBACK_FILE):
                st.warning("No feedback data available.")
                return
                
            try:
                # Load feedback data
                feedback_df = pd.read_excel(FEEDBACK_FILE, sheet_name='feedback')
                if feedback_df.empty:
                    st.warning("No feedback submissions available.")
                    return
                
                # Convert timestamp column
                feedback_df['Timestamp'] = pd.to_datetime(feedback_df['Timestamp'])
                
                # Add filters in sidebar
                st.sidebar.header("Analysis Filters")
                
                # Date range filter
                st.sidebar.subheader("Date Range")
                start_date = st.sidebar.date_input(
                    "From Date",
                    value=datetime.now() - timedelta(days=30)
                )
                end_date = st.sidebar.date_input(
                    "To Date",
                    value=datetime.now()
                )
                
                # Program filter
                available_programs = feedback_df['Program'].unique()
                selected_programs = st.sidebar.multiselect(
                    "Select Programs",
                    options=available_programs,
                    default=available_programs
                )
                
                # Branch filter based on selected programs
                available_branches = []
                if selected_programs:
                    available_branches = feedback_df[
                        feedback_df['Program'].isin(selected_programs)
                    ]['Branch'].unique()
                
                selected_branches = st.sidebar.multiselect(
                    "Select Branches",
                    options=available_branches
                )
                
                # Apply filters
                mask = (feedback_df['Timestamp'].dt.date >= start_date) & \
                      (feedback_df['Timestamp'].dt.date <= end_date)
                
                if selected_programs:
                    mask &= feedback_df['Program'].isin(selected_programs)
                if selected_branches:
                    mask &= feedback_df['Branch'].isin(selected_branches)
                
                filtered_df = feedback_df[mask]
                
                if filtered_df.empty:
                    st.warning("No data available for selected filters.")
                    return
                
                # Display applied filters
                st.markdown("### Applied Filters")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Date Range:** {start_date} to {end_date}")
                with col2:
                    st.write(f"**Programs:** {', '.join(selected_programs)}")
                with col3:
                    if selected_branches:
                        st.write(f"**Branches:** {', '.join(selected_branches)}")
                    else:
                        st.write("**Branches:** All")
                
                st.markdown("---")
                
                # Process faculty data
                faculty_data = []
                for _, row in filtered_df.iterrows():
                    try:
                        faculty_selections = json.loads(row['Faculty_Selections'])
                        subject_ratings = json.loads(row['Subject_Ratings'])
                        timestamp = pd.to_datetime(row['Timestamp'])
                        month_year = timestamp.strftime('%b%Y')
                        
                        for subject_code, faculty_name in faculty_selections.items():
                            if faculty_name and subject_code in subject_ratings:
                                faculty_data.append({
                                    'Faculty_Name': faculty_name,
                                    'Subject': subject_code,
                                    'Rating': float(subject_ratings[subject_code]),
                                    'Month': month_year,
                                    'Program': row['Program'],
                                    'Branch': row['Branch'],
                                    'Date': timestamp
                                })
                    except Exception:
                        continue
                
                if faculty_data:
                    faculty_df = pd.DataFrame(faculty_data)
                    
                    # Monthly performance analysis
                    faculty_monthly = faculty_df.groupby(['Month', 'Faculty_Name'])['Rating'].mean().reset_index()
                    faculty_pivot = faculty_monthly.pivot(
                        index='Faculty_Name',
                        columns='Month',
                        values='Rating'
                    ).fillna(0)
                    
                    # Sort months chronologically
                    faculty_pivot = faculty_pivot.reindex(sorted(faculty_pivot.columns), axis=1)
                    
                    # Create heatmap
                    st.subheader("Faculty Performance Heatmap")
                    
                    # Convert to numpy array for heatmap
                    data_array = faculty_pivot.to_numpy()
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=data_array,
                        x=faculty_pivot.columns,
                        y=faculty_pivot.index,
                        text=np.round(data_array, 2),
                        texttemplate="%{text}",
                        textfont={"size": 12},
                        colorscale="Blues",
                        showscale=True,
                        hoverongaps=False
                    ))
                    
                    fig.update_layout(
                        title="Monthly Faculty Performance",
                        xaxis_title="Month",
                        yaxis_title="Faculty Name",
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Subject-wise analysis
                    st.subheader("Subject-wise Faculty Performance")
                    subject_stats = faculty_df.groupby(['Faculty_Name', 'Subject', 'Program', 'Branch'])[
                        'Rating'
                    ].agg(['mean', 'count']).round(2).reset_index()
                    
                    st.dataframe(
                        subject_stats,
                        column_config={
                            'mean': st.column_config.NumberColumn('Average Rating', format="%.2f"),
                            'count': st.column_config.NumberColumn('Number of Ratings')
                        },
                        use_container_width=True
                    )
                    
                    # Download options
                    st.subheader("Download Reports")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Download Detailed Report"):
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                report_file = f"faculty_report_{timestamp}.xlsx"
                                
                                with pd.ExcelWriter(report_file) as writer:
                                    # Monthly performance
                                    faculty_monthly.to_excel(
                                        writer, 
                                        sheet_name='Monthly_Performance',
                                        index=False
                                    )
                                    
                                    # Subject-wise analysis
                                    subject_stats.to_excel(
                                        writer,
                                        sheet_name='Subject_Analysis',
                                        index=False
                                    )
                                    
                                    # Performance matrix
                                    faculty_pivot.to_excel(
                                        writer,
                                        sheet_name='Performance_Matrix'
                                    )
                                    
                                    # Filter information
                                    filter_info = pd.DataFrame({
                                        'Filter': ['Date Range', 'Programs', 'Branches'],
                                        'Value': [
                                            f"{start_date} to {end_date}",
                                            ', '.join(selected_programs),
                                            ', '.join(selected_branches) if selected_branches else 'All'
                                        ]
                                    })
                                    filter_info.to_excel(
                                        writer,
                                        sheet_name='Filter_Info',
                                        index=False
                                    )
                                    
                                st.success(f"Report downloaded as {report_file}")
                            except Exception as e:
                                st.error(f"Error generating report: {str(e)}")
                
                else:
                    st.info("No faculty performance data available for selected filters.")
            
            except Exception as e:
                st.error(f"Error in faculty analysis: {str(e)}")

        elif navigation == "Reset Credentials":
            st.title("Reset Admin Credentials")
            
            with st.form("credentials_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Update Credentials"):
                    if not new_username or not new_password:
                        st.error("Please fill all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long!")
                    else:
                        try:
                            global ADMIN_USERNAME, ADMIN_PASSWORD
                            ADMIN_USERNAME = new_username
                            ADMIN_PASSWORD = new_password
                            st.success("Credentials updated successfully!")
                            st.info("Please log out and log in again with new credentials.")
                        except Exception as e:
                            st.error(f"Error updating credentials: {str(e)}")

    except Exception as e:
        st.error(f"Dashboard Error: {str(e)}")
        print(f"Dashboard Error: {str(e)}")

def validate_input(hall_ticket, student_name):
    """Validate user input"""
    if not hall_ticket or not student_name:
        return False, "Please fill all required fields"
    if len(hall_ticket) < 5:
        return False, "Hall ticket number is too short"
    if len(student_name) < 2:
        return False, "Student name is too short"
    return True, ""

def update_faculty_sheet(feedback_data):
    """Update faculty sheet with monthly ratings"""
    try:
        # Read existing faculty data
        faculty_df = pd.read_excel(FEEDBACK_FILE, sheet_name='faculty')
        
        # Get current month-year
        current_date = datetime.now()
        month_year = current_date.strftime("%b%Y")  # e.g., Dec2024
        
        # Add new column for current month if it doesn't exist
        if month_year not in faculty_df.columns:
            faculty_df[month_year] = None
        
        # Process subject ratings and update faculty scores
        subject_ratings = json.loads(feedback_data['Subject_Ratings'])
        faculty_selections = json.loads(feedback_data['Faculty_Selections'])
        
        for subject_code, rating in subject_ratings.items():
            faculty_name = faculty_selections.get(subject_code)
            if faculty_name:
                # Get existing rating for faculty
                mask = faculty_df['Faculty_Name'] == faculty_name
                current_rating = faculty_df.loc[mask, month_year].iloc[0]
                
                if pd.isna(current_rating):
                    # First rating for this month
                    faculty_df.loc[mask, month_year] = rating
                else:
                    # Average with existing rating
                    faculty_df.loc[mask, month_year] = (current_rating + rating) / 2
        
        # Save updated faculty data
        with pd.ExcelWriter(FEEDBACK_FILE, mode='a', if_sheet_exists='overlay') as writer:
            faculty_df.to_excel(writer, sheet_name='faculty', index=False)
            
        return True
    except Exception as e:
        print(f"Error updating faculty sheet: {str(e)}")
        return False

def show_feedback_form():
    """Display student feedback form with improved table layout"""
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
            
            # Load faculty list
            try:
                faculty_df = pd.read_excel(FEEDBACK_FILE, sheet_name='faculty')
                faculty_list = faculty_df['Faculty_Name'].tolist()
            except Exception as e:
                st.error(f"Error loading faculty list: {str(e)}")
                faculty_list = []
            
            # Custom CSS for table layout
            st.markdown("""
                <style>
                .feedback-header {
                    display: flex;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 2px solid #555;
                    margin-bottom: 15px;
                    font-weight: bold;
                    background-color: #1E1E1E;
                }
                .feedback-row {
                    display: flex;
                    align-items: center;
                    padding: 15px 0;
                    border-bottom: 1px solid #333;
                }
                .subject-col {
                    width: 30%;
                    padding: 5px 10px;
                }
                .faculty-col {
                    width: 30%;
                    padding: 5px 10px;
                }
                .rating-col {
                    width: 40%;
                    padding: 5px 10px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Subject Feedback
            st.subheader("Subject Feedback")
            
            # Table Headers
            st.markdown("""
                <div class="feedback-header">
                    <div class="subject-col">Subject</div>
                    <div class="faculty-col">Faculty</div>
                    <div class="rating-col">Rating</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Initialize feedback storage
            subject_ratings = {}
            faculty_selections = {}
            
            # Subject Feedback Rows
            for subject_code, subject_name in ACADEMIC_STRUCTURE[program][branch][year_sem]["subjects"].items():
                st.markdown(f'<div class="feedback-row">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 3, 4])
                
                with col1:
                    st.markdown(f"**{subject_name}**")
                
                with col2:
                    selected_faculty = st.selectbox(
                        "Select Faculty",
                        options=[""] + faculty_list,  # Add empty option as default
                        key=f"faculty_{subject_code}",
                        label_visibility="collapsed"
                    )
                    faculty_selections[subject_code] = selected_faculty
                
                with col3:
                    rating = st.radio(
                        "Rating",
                        options=RATING_OPTIONS,
                        key=f"rating_{subject_code}",
                        label_visibility="collapsed",
                        horizontal=True,
                        index=None
                    )
                    subject_ratings[subject_code] = get_rating_value(rating) if rating else 0
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Lab Feedback
            st.subheader("Lab Feedback")
            
            # Lab Table Headers
            st.markdown("""
                <div class="feedback-header">
                    <div style="width: 40%; padding: 5px 10px;">Lab</div>
                    <div style="width: 20%; padding: 5px 10px;">Explained</div>
                    <div style="width: 20%; padding: 5px 10px;">Executed</div>
                    <div style="width: 20%; padding: 5px 10px;">Records</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Lab Feedback Rows
            lab_feedback = {}
            for lab_code, lab_name in ACADEMIC_STRUCTURE[program][branch][year_sem]["labs"].items():
                st.markdown(f'<div class="feedback-row">', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
                
                with col1:
                    st.markdown(f"**{lab_name}**")
                
                with col2:
                    explained = st.checkbox(
                        "Explained",
                        key=f"exp_{lab_code}",
                        label_visibility="collapsed",
                        value=False
                    )
                
                with col3:
                    executed = st.checkbox(
                        "Executed",
                        key=f"exe_{lab_code}",
                        label_visibility="collapsed",
                        value=False
                    )
                
                with col4:
                    records = st.checkbox(
                        "Records",
                        key=f"rec_{lab_code}",
                        label_visibility="collapsed",
                        value=False
                    )
                
                lab_feedback[lab_code] = {
                    "explained": explained,
                    "executed": executed,
                    "records": records
                }
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Overall Feedback
            st.subheader("Overall Feedback")
            
            overall_rating = st.radio(
                "Overall Experience Rating *",
                options=RATING_OPTIONS,
                horizontal=True,
                key="overall_rating",
                index=None
            )
            
            suggestions = st.text_area("Suggestions/Recommendations")
            
            # Submit Button
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                # Validate required fields
                is_valid, error_message = validate_input(hall_ticket, student_name)
                if not is_valid:
                    st.error(error_message)
                    return
                
                # Validate ratings
                if not all(rating > 0 for rating in subject_ratings.values()):
                    st.error("Please provide ratings for all subjects")
                    return
                
                if not overall_rating:
                    st.error("Please provide an overall rating")
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
                        'Faculty_Selections': json.dumps(faculty_selections),
                        'Lab_Feedback': json.dumps(lab_feedback),
                        'Overall_Rating': get_rating_value(overall_rating),
                        'Suggestions': suggestions
                    }
                    
                    try:
                        if os.path.exists(FEEDBACK_FILE):
                            # Check for duplicate submissions
                            df = pd.read_excel(FEEDBACK_FILE, sheet_name='feedback')
                            if not df.empty and len(df[df['Hall_Ticket'] == hall_ticket]) > 0:
                                st.error("You have already submitted feedback. Multiple submissions are not allowed.")
                                return
                            
                            # Save feedback data
                            with pd.ExcelWriter(FEEDBACK_FILE, mode='a', if_sheet_exists='overlay') as writer:
                                df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
                                df.to_excel(writer, sheet_name='feedback', index=False)
                            
                            # Update faculty ratings
                            if update_faculty_sheet(feedback_data):
                                st.success("Thank you! Your feedback has been submitted successfully.")
                                st.balloons()
                                st.rerun()
                            else:
                                st.warning("Feedback saved but faculty ratings update failed. Please contact administrator.")
                        else:
                            st.error("Feedback file not found. Please contact administrator.")
                            
                    except Exception as e:
                        st.error(f"Error saving feedback: {str(e)}")
                        print(f"Error saving feedback: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error processing feedback: {str(e)}")
                    print(f"Error processing feedback: {str(e)}")
    
    except Exception as e:
        st.error(f"Error displaying feedback form: {str(e)}")
        print(f"Error displaying feedback form: {str(e)}")    


        

def main():
    """Main application function"""
    try:
        # Initialize session state
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False
        
        # Initialize feedback file
        initialize_feedback_file()
        
        
        
        
        
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