import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def calculate_kpis(records):
    if not records or len(records) == 0:
        return {
            'total_downtime': 0,
            'avg_downtime': 0,
            'num_incidents': 0
        }

    # Create DataFrame with proper column names from database schema
    columns = ['id', 'date', 'shift', 'line', 'start_time', 'end_time', 
              'duration', 'equipment', 'issue_type', 'issue_description',
              'action_taken', 'responsible_person', 'remarks', 'created_at']
    df = pd.DataFrame(records, columns=columns)

    total_downtime = df['duration'].sum()
    avg_downtime = df['duration'].mean()
    num_incidents = len(df)

    return {
        'total_downtime': total_downtime,
        'avg_downtime': round(avg_downtime, 2),
        'num_incidents': num_incidents
    }

def create_pareto_chart(data, title="Pareto Analysis", x_title="Category"):
    """Generic Pareto chart creation function"""
    if not data or len(data) == 0:
        return None

    df = pd.DataFrame(data, columns=['category', 'frequency', 'total_duration'])
    df = df.sort_values('total_duration', ascending=False)

    # Calculate cumulative percentage
    df['cumulative_percentage'] = df['total_duration'].cumsum() / df['total_duration'].sum() * 100

    fig = go.Figure()

    # Bar chart for duration
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['total_duration'],
        name='Duration'
    ))

    # Line chart for cumulative percentage
    fig.add_trace(go.Scatter(
        x=df['category'],
        y=df['cumulative_percentage'],
        name='Cumulative %',
        yaxis='y2',
        line=dict(color='red', width=2)
    ))

    fig.update_layout(
        title=title,
        yaxis=dict(title='Total Downtime (minutes)'),
        yaxis2=dict(
            title='Cumulative Percentage',
            overlaying='y',
            side='right',
            range=[0, 100],
            tickformat='.0f'
        ),
        showlegend=True,
        height=500,
        barmode='relative'
    )

    return fig

def create_equipment_pareto(equipment_stats):
    """Create Pareto chart for equipment downtime"""
    return create_pareto_chart(
        equipment_stats,
        title="Pareto Analysis of Equipment Downtime",
        x_title="Equipment"
    )

def create_issue_type_pareto(issue_type_stats):
    """Create Pareto chart for downtime causes"""
    return create_pareto_chart(
        issue_type_stats,
        title="Pareto Analysis of Downtime Causes",
        x_title="Issue Type"
    )

def create_downtime_trend(records):
    """Create trend analysis of downtime over time"""
    if not records or len(records) == 0:
        return None

    # Create DataFrame with proper column names
    columns = ['id', 'date', 'shift', 'line', 'start_time', 'end_time', 
              'duration', 'equipment', 'issue_type', 'issue_description',
              'action_taken', 'responsible_person', 'remarks', 'created_at']
    df = pd.DataFrame(records, columns=columns)
    df['date'] = pd.to_datetime(df['date'])
    daily_downtime = df.groupby('date')['duration'].sum().reset_index()

    fig = px.line(
        daily_downtime, 
        x='date', 
        y='duration',
        title='Daily Downtime Trend',
        labels={'duration': 'Total Downtime (minutes)', 'date': 'Date'}
    )

    return fig

def create_shift_analysis(records):
    if not records or len(records) == 0:
        return None

    columns = ['id', 'date', 'shift', 'line', 'start_time', 'end_time', 
              'duration', 'equipment', 'issue_type', 'issue_description',
              'action_taken', 'responsible_person', 'remarks', 'created_at']
    df = pd.DataFrame(records, columns=columns)

    # Aggregate by shift
    shift_analysis = df.groupby('shift').agg({
        'duration': ['sum', 'mean', 'count']
    }).round(2)

    shift_analysis.columns = ['Total Downtime', 'Average Downtime', 'Number of Incidents']
    shift_analysis = shift_analysis.reset_index()

    fig = go.Figure()

    # Add bars for each metric
    fig.add_trace(go.Bar(
        name='Total Downtime',
        x=shift_analysis['shift'],
        y=shift_analysis['Total Downtime'],
        marker_color='lightblue'
    ))

    fig.add_trace(go.Bar(
        name='Average Downtime',
        x=shift_analysis['shift'],
        y=shift_analysis['Average Downtime'],
        marker_color='lightgreen'
    ))

    fig.add_trace(go.Bar(
        name='Number of Incidents',
        x=shift_analysis['shift'],
        y=shift_analysis['Number of Incidents'],
        marker_color='lightpink'
    ))

    fig.update_layout(
        title='Shift-wise Performance Analysis',
        barmode='group',
        height=400,
        showlegend=True
    )

    return fig, shift_analysis