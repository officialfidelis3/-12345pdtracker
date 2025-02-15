import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import urllib.parse
from database import Database
from analytics import calculate_kpis, create_pareto_chart, create_downtime_trend, create_equipment_pareto, create_issue_type_pareto
from maintenance_predictor import calculate_equipment_metrics, get_maintenance_recommendations
from utils import (
    calculate_duration, get_shift_options, get_line_options,
    get_equipment_options, get_issue_type_options, format_downtime_summary
)
import time

# Initialize database
db = Database()

# Page configuration
st.set_page_config(
    page_title="Production Line Downtime Reporting",
    page_icon="🏭",
    layout="wide"
)

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>Production Line Downtime Reporting</h1>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Data Entry", "View Records", "Analytics", "Shift Summary"])

with tab1:
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)

    # Form inputs
    with st.form("downtime_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            date = st.date_input("Date", datetime.now())
            shift = st.selectbox("Shift", get_shift_options())
            line = st.selectbox("Production Line", get_line_options())

        with col2:
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            equipment = st.selectbox("Equipment", get_equipment_options())
            if equipment == "Other":
                equipment = st.text_input("Specify Equipment")

        with col3:
            issue_type = st.selectbox("Issue Type", get_issue_type_options())
            if issue_type == "Other":
                issue_type = st.text_input("Specify Issue Type")
            responsible_person = st.text_input("Responsible Person")

        issue_description = st.text_area("Issue Description")
        action_taken = st.text_area("Action Taken")
        remarks = st.text_area("Remarks")

        submit_button = st.form_submit_button("Submit")

        if submit_button:
            duration = calculate_duration(
                start_time.strftime("%H:%M"),
                end_time.strftime("%H:%M")
            )

            data = {
                'date': date.strftime("%Y-%m-%d"),
                'shift': shift,
                'line': line,
                'start_time': start_time.strftime("%H:%M"),
                'end_time': end_time.strftime("%H:%M"),
                'duration': duration,
                'equipment': equipment,
                'issue_type': issue_type,
                'issue_description': issue_description,
                'action_taken': action_taken,
                'responsible_person': responsible_person,
                'remarks': remarks
            }

            db.insert_record(data)
            st.success("Record added successfully!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    # View and manage records
    columns, records = db.get_all_records()
    if records:
        # Create DataFrame
        df = pd.DataFrame(records, columns=columns)

        # Search functionality
        search_term = st.text_input("🔍 Search records")
        if search_term:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df = df[mask]

        # Display records
        st.dataframe(df.style.set_properties(**{'text-align': 'left'}), height=400)

        # Delete records section
        st.subheader("Delete Records")
        st.warning("⚠️ Warning: Deletion cannot be undone!")

        # Simple dropdown for record selection
        record_to_delete = st.selectbox(
            "Select a record to delete:",
            options=df['id'].tolist(),
            format_func=lambda x: f"Record #{x} - {df[df['id'] == x]['date'].iloc[0]} - {df[df['id'] == x]['equipment'].iloc[0]}"
        )

        # Delete button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Delete Record", type="primary"):
                if record_to_delete:
                    try:
                        db.delete_record(record_to_delete)
                        st.success(f"Record #{record_to_delete} deleted successfully!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting record: {str(e)}")
                else:
                    st.warning("Please select a record to delete")

        # Export section
        st.subheader("Export Data")
        if st.button("📊 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"downtime_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No records found in the database")

with tab3:
    # Analytics dashboard
    columns, records = db.get_all_records()
    if records:
        # Calculate KPIs
        kpis = calculate_kpis(records)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Downtime (min)", kpis['total_downtime'])
        with col2:
            st.metric("Average Downtime (min)", kpis['avg_downtime'])
        with col3:
            st.metric("Number of Incidents", kpis['num_incidents'])

        # Equipment Pareto Chart
        st.subheader("Equipment Analysis")
        equipment_stats = db.get_equipment_stats()
        equipment_pareto = create_equipment_pareto(equipment_stats)
        if equipment_pareto:
            st.plotly_chart(equipment_pareto, use_container_width=True)

        # Issue Type Pareto Chart
        st.subheader("Downtime Causes Analysis")
        issue_type_stats = db.get_issue_type_stats()
        issue_type_pareto = create_issue_type_pareto(issue_type_stats)
        if issue_type_pareto:
            st.plotly_chart(issue_type_pareto, use_container_width=True)

        # Preventive Maintenance Analysis
        st.subheader("Preventive Maintenance Predictions")

        # Equipment Metrics
        metrics_df = calculate_equipment_metrics(records)
        if not metrics_df.empty:
            st.write("Equipment Performance Metrics:")
            # Format dates for display
            metrics_df['next_predicted_failure'] = pd.to_datetime(metrics_df['next_predicted_failure']).dt.strftime('%Y-%m-%d')
            metrics_df['recommended_maintenance'] = pd.to_datetime(metrics_df['recommended_maintenance']).dt.strftime('%Y-%m-%d')
            st.dataframe(metrics_df)

            # Maintenance Recommendations
            st.subheader("⚠️ Upcoming Maintenance Recommendations")
            recommendations = get_maintenance_recommendations(records)

            if recommendations:
                for rec in recommendations:
                    with st.expander(f"🔧 {rec['equipment']} - Maintenance needed in {rec['days_until_maintenance']} days"):
                        st.write(f"• Mean Time Between Failures: {rec['mtbf_days']:.1f} days")
                        st.write(f"• Current Failure Rate: {rec['failure_rate']} failures/month")
                        st.write(f"• Average Downtime per Incident: {rec['avg_downtime']} minutes")
            else:
                st.info("No immediate maintenance recommendations at this time.")

        # Downtime Trend
        st.subheader("Downtime Trend")
        trend_fig = create_downtime_trend(records)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)

        # Equipment Performance Analysis
        st.subheader("Equipment Performance Analysis")
        equipment_df = pd.DataFrame(equipment_stats, 
                                  columns=['Equipment', 'Frequency', 'Total Duration'])
        st.dataframe(equipment_df)
    else:
        st.info("No data available for analytics")

with tab4:
    st.subheader("Shift Summary and Sharing")

    # Production data input
    with st.form("production_data"):
        col1, col2 = st.columns(2)
        with col1:
            summary_date = st.date_input("Select Date", datetime.now())
            packs_produced = st.number_input("Number of Packs Produced", min_value=0)
        with col2:
            summary_line = st.selectbox("Select Production Line", get_line_options())
            shift_select = st.selectbox("Select Shift", get_shift_options(), key="summary_shift")

        generate_button = st.form_submit_button("Generate Summary")

        if generate_button:
            columns, records = db.get_all_records()
            if records:
                production_data = {
                    'date': summary_date.strftime("%Y-%m-%d"),
                    'line': summary_line,
                    'packs_produced': packs_produced,
                    'shift': shift_select
                }

                # Generate summary
                summary_text = format_downtime_summary(records, production_data)
                st.text_area("Summary", summary_text, height=300)

                # Share buttons
                col1, col2 = st.columns(2)
                with col1:
                    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(summary_text)}"
                    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Share via WhatsApp</button></a>', unsafe_allow_html=True)

                with col2:
                    mailto_url = f"mailto:?subject=Production%20Shift%20Summary&body={urllib.parse.quote(summary_text)}"
                    st.markdown(f'<a href="{mailto_url}"><button style="background-color: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Share via Email</button></a>', unsafe_allow_html=True)
            else:
                st.warning("No records available to generate summary")