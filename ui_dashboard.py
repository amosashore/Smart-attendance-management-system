"""
Enhanced dashboard UI with modern visualizations and analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import json

from database import db
from logger import get_logger, get_recent_logs

logger = get_logger(__name__)


def dashboard():
    """Main dashboard page"""
    st.title("📊 Attendance Dashboard")
    
    # Load data
    df = db.load_attendance_df()
    stats = db.get_statistics()
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Records", stats['total_records'])
    
    with col2:
        st.metric("👥 Unique Employees", stats['unique_employees'])
    
    with col3:
        st.metric("🕒 Late Arrivals", stats['late_arrivals'], 
                 delta=f"{stats['late_percentage']}%", delta_color="inverse")
    
    with col4:
        st.metric("📅 Today", stats['today_attendance'])
    
    if df.empty:
        st.info("No attendance records yet. Start by registering faces and marking attendance.")
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Analytics", "📋 Records", "📊 Reports", "⚙️ Management", "📝 Logs"
    ])
    
    with tab1:
        _show_analytics(df, stats)
    
    with tab2:
        _show_records(df)
    
    with tab3:
        _show_reports(df)
    
    with tab4:
        _show_management(df)
    
    with tab5:
        _show_logs()


def _show_analytics(df: pd.DataFrame, stats: dict):
    """Analytics tab"""
    st.header("Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Attendance by date
        st.subheader("📅 Daily Attendance Trend")
        daily_counts = df.groupby('date').size().reset_index(name='count')
        fig = px.line(daily_counts, x='date', y='count', 
                     title='Daily Attendance Count',
                     labels={'date': 'Date', 'count': 'Number of Attendees'})
        fig.update_traces(line_color='#FF4B4B')
        st.plotly_chart(fig, use_container_width=True)
        
        # Late vs On-time
        st.subheader("⏰ Punctuality Status")
        late_counts = df['late'].value_counts()
        fig = px.pie(values=late_counts.values, names=late_counts.index,
                    title='Late vs On-Time Arrivals',
                    color_discrete_sequence=['#00CC96', '#FF4B4B'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top attendees
        st.subheader("🏆 Most Active Employees")
        name_counts = df['name'].value_counts().head(10)
        fig = px.bar(x=name_counts.values, y=name_counts.index, 
                    orientation='h',
                    labels={'x': 'Days Present', 'y': 'Employee'},
                    title='Top 10 Attendees')
        fig.update_traces(marker_color='#636EFA')
        st.plotly_chart(fig, use_container_width=True)
        
        # Attendance by hour
        st.subheader("🕐 Check-in Time Distribution")
        if 'time' in df.columns and len(df) > 0:
            df_copy = df.copy()
            df_copy['hour'] = pd.to_datetime(df_copy['time'], format='%H:%M:%S').dt.hour
            hour_counts = df_copy['hour'].value_counts().sort_index()
            fig = px.bar(x=hour_counts.index, y=hour_counts.values,
                        labels={'x': 'Hour of Day', 'y': 'Check-ins'},
                        title='Check-in Time Distribution')
            fig.update_traces(marker_color='#AB63FA')
            st.plotly_chart(fig, use_container_width=True)
    
    # Confidence metrics
    if 'confidence' in df.columns and df['confidence'].sum() > 0:
        st.subheader("🎯 Recognition Confidence")
        avg_conf = df[df['confidence'] > 0]['confidence'].mean()
        st.metric("Average Confidence", f"{avg_conf:.1%}")
        
        fig = px.histogram(df[df['confidence'] > 0], x='confidence', 
                          nbins=20, title='Confidence Distribution',
                          labels={'confidence': 'Recognition Confidence'})
        st.plotly_chart(fig, use_container_width=True)


def _show_records(df: pd.DataFrame):
    """Records tab"""
    st.header("Attendance Records")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name_filter = st.selectbox("Filter by Name", 
                                   ["All"] + sorted(df['name'].unique().tolist()))
    
    with col2:
        date_from = st.date_input("From Date", 
                                  value=datetime.now() - timedelta(days=30))
    
    with col3:
        date_to = st.date_input("To Date", value=datetime.now())
    
    # Apply filters
    filtered_df = df.copy()
    
    if name_filter != "All":
        filtered_df = filtered_df[filtered_df['name'] == name_filter]
    
    if date_from and date_to:
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['date']) >= pd.to_datetime(date_from)) &
            (pd.to_datetime(filtered_df['date']) <= pd.to_datetime(date_to))
        ]
    
    st.dataframe(
        filtered_df.style.applymap(
            lambda x: 'background-color: #ffcccc' if x == 'Late' else '',
            subset=['late']
        ),
        use_container_width=True,
        height=400
    )
    
    st.caption(f"Showing {len(filtered_df)} of {len(df)} records")


def _show_reports(df: pd.DataFrame):
    """Reports tab"""
    st.header("Export Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Monthly Report")
        if 'date' in df.columns and len(df) > 0:
            available_months = sorted(df['date'].str[:7].unique(), reverse=True)
            month = st.selectbox("Select Month", available_months)
            
            filtered = df[df['date'].str.startswith(month)]
            
            st.write(f"**Records for {month}:** {len(filtered)}")
            
            # Export format
            export_format = st.selectbox("Export Format", ["Excel", "CSV", "JSON"])
            
            if st.button("Generate Report"):
                if export_format == "Excel":
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        filtered.to_excel(writer, index=False, sheet_name='Attendance')
                    buffer.seek(0)
                    st.download_button(
                        "📥 Download Excel Report",
                        buffer,
                        file_name=f"attendance_{month}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                elif export_format == "CSV":
                    csv = filtered.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV Report",
                        csv,
                        file_name=f"attendance_{month}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    json_str = filtered.to_json(orient='records', indent=2)
                    st.download_button(
                        "📥 Download JSON Report",
                        json_str,
                        file_name=f"attendance_{month}.json",
                        mime="application/json"
                    )
    
    with col2:
        st.subheader("📊 Summary Report")
        
        report_type = st.selectbox("Report Type", 
                                  ["Employee Summary", "Late Arrivals", "Daily Summary"])
        
        if report_type == "Employee Summary":
            summary = df.groupby('name').agg({
                'date': 'count',
                'late': lambda x: (x == 'Late').sum(),
                'confidence': 'mean'
            }).rename(columns={
                'date': 'Total Days',
                'late': 'Late Count',
                'confidence': 'Avg Confidence'
            })
            summary['Avg Confidence'] = summary['Avg Confidence'].apply(lambda x: f"{x:.1%}")
            st.dataframe(summary, use_container_width=True)
        
        elif report_type == "Late Arrivals":
            late_df = df[df['late'] == 'Late']
            st.dataframe(late_df, use_container_width=True)
        
        elif report_type == "Daily Summary":
            daily = df.groupby('date').agg({
                'name': 'count',
                'late': lambda x: (x == 'Late').sum()
            }).rename(columns={
                'name': 'Total Attendance',
                'late': 'Late Arrivals'
            })
            st.dataframe(daily, use_container_width=True)


def _show_management(df: pd.DataFrame):
    """Management tab"""
    st.header("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💾 Backup Database")
        if st.button("Create Backup"):
            try:
                backup_path = db.backup_database()
                st.success(f"✅ Backup created: {backup_path.name}")
            except Exception as e:
                st.error(f"❌ Backup failed: {e}")
    
    with col2:
        st.subheader("🔄 Restore Database")
        st.info("Upload a backup file to restore the database")
        uploaded_file = st.file_uploader("Choose backup file", type=['db'])
        if uploaded_file and st.button("Restore"):
            st.warning("This feature requires file system access")
    
    st.divider()
    
    # Danger zone
    st.subheader("⚠️ Danger Zone")
    with st.expander("Clear All Records", expanded=False):
        st.error("**WARNING**: This action cannot be undone!")
        
        confirm_text = st.text_input("Type 'DELETE ALL' to confirm")
        
        if confirm_text == "DELETE ALL":
            if st.button("🗑️ Clear All Records", type="primary"):
                count = db.clear_all_attendance()
                st.success(f"Cleared {count} records")
                st.rerun()
        else:
            st.button("🗑️ Clear All Records", disabled=True)


def _show_logs():
    """Logs tab"""
    st.header("System Logs")
    
    logs = get_recent_logs(100)
    
    if not logs:
        st.info("No logs available")
        return
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.selectbox("Log Level", ["ALL", "ERROR", "WARNING", "INFO", "DEBUG"])
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=False)
    
    # Filter logs
    if log_level != "ALL":
        logs = [log for log in logs if log['level'] == log_level]
    
    # Display logs
    for log in reversed(logs[-50:]):  # Show last 50
        level_color = {
            'ERROR': '🔴',
            'WARNING': '🟡',
            'INFO': '🔵',
            'DEBUG': '⚪'
        }.get(log['level'], '⚪')
        
        with st.expander(f"{level_color} [{log['level']}] {log['message'][:100]}...", expanded=False):
            st.code(log['message'], language='text')
            st.caption(f"Time: {datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if auto_refresh:
        st.rerun()
