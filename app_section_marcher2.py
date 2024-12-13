import streamlit as st
import pandas as pd
import io
from copy import deepcopy

def get_sheets_with_original_section(excel_file):
    """Return list of sheet names that have 'Original Section' in their third column"""
    xls = pd.ExcelFile(excel_file)
    sheets_with_original_section = []
    
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1)
            if len(df.columns) >= 3 and df.columns[2] == 'Original Section':
                sheets_with_original_section.append(sheet_name)
        except:
            continue
    
    return sheets_with_original_section

def get_o_section_sheets(excel_file):
    """Return list of sheet names starting with '(O)'"""
    xls = pd.ExcelFile(excel_file)
    return [sheet for sheet in xls.sheet_names if sheet.startswith('(O)')]

def update_original_sections(excel_file, source_sheet, target_sheets):
    """
    Check HT Numbers from source sheet against target sheets and update Original Section
    Returns updated DataFrame and results summary
    """
    # Create a copy of the Excel file in memory
    excel_buffer_copy = deepcopy(excel_file)
    
    # Read source sheet and explicitly set Original Section as string type
    source_df = pd.read_excel(excel_buffer_copy, sheet_name=source_sheet)
    source_df['Original Section'] = source_df['Original Section'].astype(str)
    
    # Initialize results list
    results = []
    
    # For each HT Number in source sheet
    for idx, row in source_df.iterrows():
        ht_number = row['HT Number']
        row_result = {
            'HT Number': ht_number,
            'Original Sheet': source_sheet,
            'Previous Section': row['Original Section']
        }
        
        # Check each target sheet
        found_in_sheets = []
        for target_sheet in target_sheets:
            target_df = pd.read_excel(excel_buffer_copy, sheet_name=target_sheet)
            if ht_number in target_df['HT Number'].values:
                found_in_sheets.append(target_sheet)
        
        # Update Original Section if found
        if len(found_in_sheets) == 1:
            # Convert to string type before assignment
            source_df.at[idx, 'Original Section'] = str(found_in_sheets[0])
            row_result['New Section'] = found_in_sheets[0]
            row_result['Status'] = 'Updated'
        elif len(found_in_sheets) > 1:
            row_result['New Section'] = 'Multiple Matches: ' + ', '.join(found_in_sheets)
            row_result['Status'] = 'Multiple Matches Found'
        else:
            row_result['New Section'] = 'Not Found'
            row_result['Status'] = 'No Match Found'
            
        results.append(row_result)
    
    return source_df, pd.DataFrame(results)

def main():
    st.title("Excel Section Matcher and Updater")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Excel Workbook", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Save the uploaded file to a buffer
        excel_buffer = io.BytesIO(uploaded_file.read())
        
        try:
            # Get sheets with 'Original Section'
            source_sheets = get_sheets_with_original_section(excel_buffer)
            
            # Get sheets starting with (O)
            o_section_sheets = get_o_section_sheets(excel_buffer)
            
            # Create two columns for dropdowns
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Select Source Sheet")
                selected_source = st.selectbox(
                    "Sheets with 'Original Section'",
                    options=source_sheets
                )
            
            with col2:
                st.subheader("Select Target Sheets")
                selected_targets = st.multiselect(
                    "Sheets starting with (O)",
                    options=o_section_sheets
                )
            
            # Process button
            if st.button("Process and Update") and selected_source and selected_targets:
                # Reset buffer position
                excel_buffer.seek(0)
                
                # Get updated dataframe and results
                updated_df, results_df = update_original_sections(excel_buffer, selected_source, selected_targets)
                
                # Display results summary
                st.subheader("Processing Results")
                st.dataframe(results_df)
                
                # Create updated Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Copy all sheets from original file
                    excel_buffer.seek(0)
                    original_wb = pd.ExcelFile(excel_buffer)
                    for sheet_name in original_wb.sheet_names:
                        if sheet_name == selected_source:
                            # Write updated sheet
                            updated_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        else:
                            # Copy original sheet
                            df = pd.read_excel(excel_buffer, sheet_name=sheet_name)
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download updated Excel workbook
                    output.seek(0)
                    st.download_button(
                        label="Download Updated Excel Workbook",
                        data=output,
                        file_name="updated_workbook.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col2:
                    # Download results summary
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="Download Results Summary (CSV)",
                        data=csv,
                        file_name="update_results.csv",
                        mime="text/csv"
                    )
                
                # Display preview of updated sheet
                st.subheader(f"Preview of Updated {selected_source} Sheet")
                st.dataframe(updated_df)
        
        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
            st.error("Please make sure the Excel file has the correct format with 'HT Number' and 'Original Section' columns.")

if __name__ == "__main__":
    main()