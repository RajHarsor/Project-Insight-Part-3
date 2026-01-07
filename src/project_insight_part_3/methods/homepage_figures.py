from turtle import title
import plotly.graph_objects as go
import polars as pl
import datetime as dt
import boto3
from nicegui import ui
from typing import Dict, Any
from .env_initialize import read_env_variables

def pie_chart_progress() -> go.Figure:
    """Creates a pie chart showing participant progress.

    Returns:
        go.Figure: A Plotly Figure object representing the pie chart.
    """
    # Initialize AWS session
    env_vars = read_env_variables()
    
    aws_access_key_id = env_vars.get('aws_access_key_id') or env_vars.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = env_vars.get('aws_secret_access_key') or env_vars.get('AWS_SECRET_ACCESS_KEY')
    region_name = env_vars.get('region') or env_vars.get('REGION') or env_vars.get('AWS_DEFAULT_REGION')
    table_name = env_vars.get('insight_p3_table_name')

    if not region_name:
        ui.label('Error: AWS Region not specified in environment variables.').style('color: red; font-weight: bold;')
        return go.Figure()
    
    try:
        Session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

        dynamodb = Session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.scan()
    except Exception as e:
        ui.label(f'AWS Error: {str(e)}').style('color: red; font-weight: bold;')
        return go.Figure()
    
    # Load data into Polars DataFrame + Clean
    data = response['Items']
    df = pl.DataFrame(data)
    df = df.with_columns([
        pl.col('start_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('start_date'),
        pl.col('end_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('end_date')
    ])
    
    # Calculate counts
    not_started_count = df.filter(pl.col('start_date') > dt.date.today()).height
    in_progress_count = df.filter((pl.col('start_date') <= dt.date.today()) & (pl.col('end_date') >= dt.date.today())).height
    completed_count = df.filter(pl.col('end_date') < dt.date.today()).height
    participants_left = 65 - (not_started_count + in_progress_count + completed_count)
    
    # Create pie chart
    labels = ['Pending Start', 'In Progress', 'Completed', 'Participants Left to Recruit']
    values = [not_started_count, in_progress_count, completed_count, participants_left]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(
        title=dict(
            text= 'Recruitment Progress',
            x=0.5,
            xanchor='center',
            yanchor='top',
            y=0.95
        ),
        font_size=10,
        height=400,
        width=350,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.5,           # move legend below chart (adjust as needed)
            x=0.5,
            xanchor='center',
            font=dict(size=10)
    ),
        template='plotly_dark'
    )

    fig.update_layout(margin=dict(t=60, b=80))
    # adjust overall pie size
    fig.update_traces(marker=dict(line=dict(color='#000000', width=1)))
    
    return fig

# Fig 2: Phase breakdown Pie Chart
def phase_breakdown_pie_chart() -> go.Figure:
    """Creates a pie chart showing the breakdown of participants by phase.

    Returns:
        go.Figure: A Plotly Figure object representing the pie chart.
    """
    # Initialize AWS session
    env_vars = read_env_variables()
    
    aws_access_key_id = env_vars.get('aws_access_key_id') or env_vars.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = env_vars.get('aws_secret_access_key') or env_vars.get('AWS_SECRET_ACCESS_KEY')
    region_name = env_vars.get('region') or env_vars.get('REGION') or env_vars.get('AWS_DEFAULT_REGION')
    table_name = env_vars.get('insight_p3_table_name')

    if not region_name:
        ui.label('Error: AWS Region not specified in environment variables.').style('color: red; font-weight: bold;')
        return go.Figure()

    try:
        Session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        dynamodb = Session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.scan()
    except Exception as e:
        ui.label(f'AWS Error: {str(e)}').style('color: red; font-weight: bold;')
        return go.Figure()
    
    data = response['Items']
    df = pl.DataFrame(data)
    df = df.with_columns([
        pl.col('start_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('start_date'),
        pl.col('end_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('end_date')
    ])
    
    current_date = dt.date.today()
    in_progress_participants = df.filter((pl.col('end_date') >= current_date) & (pl.col('start_date') <= current_date))
    
    in_progress_participants = in_progress_participants.with_columns(
        ((current_date - pl.col('start_date') + pl.duration(days=1)) / pl.duration(days=1)).cast(pl.Int64).alias('days_in_study')
    )

    # Calculate study phase based on days_in_study (1-4 days = phase 1, 5-12 days = phase 2, 13-14 days = phase 3)
    in_progress_participants = in_progress_participants.with_columns(
        pl.when(pl.col('days_in_study').is_between(1, 4)).then(pl.lit(1))
          .when(pl.col('days_in_study').is_between(5, 12)).then(pl.lit(2))
          .when(pl.col('days_in_study').is_between(13, 14)).then(pl.lit(3))
          .otherwise(pl.lit(0))
          .cast(pl.Int64)
          .alias('study_phase')
    )
    
    phase_1_count = in_progress_participants.filter(pl.col('study_phase') == 1).height
    phase_2_count = in_progress_participants.filter(pl.col('study_phase') == 2).height
    phase_3_count = in_progress_participants.filter(pl.col('study_phase') == 3).height

    labels_phase = ['Phase 1', 'Phase 2', 'Phase 3']
    values_phase = [phase_1_count, phase_2_count, phase_3_count]
    fig_phase = go.Figure(data=[go.Pie(labels=labels_phase, values=values_phase, hole=.3)])
    fig_phase.update_layout(
                title=dict(
                    text= 'Current Participants by Phase',
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    y=0.95
                ),
                font_size=10,
                height=400,
                width=350,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-0.5,           # move legend below chart (adjust as needed)
                    x=0.5,
                    xanchor='center',
                    font=dict(size=10)
        ),
                margin=dict(t=60, b=80),
                template='plotly_dark'
            )
    fig_phase.update_traces(marker=dict(line=dict(color='#000000', width=1)))
    return fig_phase
    

# Fig 3: Enrollment Progress Over Time
def enrollment_progress_over_time() -> go.Figure:
    """Creates a bar chart showing enrollment progress over time.

    Returns:
        go.Figure: A Plotly Figure object representing the bar chart.
    """
    # Initialize AWS session
    env_vars = read_env_variables()
    
    aws_access_key_id = env_vars.get('aws_access_key_id') or env_vars.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = env_vars.get('aws_secret_access_key') or env_vars.get('AWS_SECRET_ACCESS_KEY')
    region_name = env_vars.get('region') or env_vars.get('REGION') or env_vars.get('AWS_DEFAULT_REGION')
    table_name = env_vars.get('insight_p3_table_name')

    if not region_name:
        ui.label('Error: AWS Region not specified in environment variables.').style('color: red; font-weight: bold;')
        return go.Figure()

    try:
        Session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        dynamodb = Session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.scan()
    except Exception as e:
        ui.label(f'AWS Error: {str(e)}').style('color: red; font-weight: bold;')
        return go.Figure()
    
    data = response['Items']
    df = pl.DataFrame(data)
    df = df.with_columns([
        pl.col('start_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('start_date'),
        pl.col('end_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('end_date')
    ])
    
    # Create a date range from the earliest start date to latest start date
    min_date = df.select(pl.col('start_date').min()).item()
    max_date = dt.date.today()

    # Adjust to start on the Monday of the first week
    # Python's weekday(): Monday is 0
    start_date = min_date - dt.timedelta(days=min_date.weekday())

    # Create eager date range (Series)
    date_range = pl.date_range(start_date, max_date, interval='1w', eager=True).alias('date')

    enrollment_counts = []
    for date in date_range:
        # Filter for start_date within the specific week (date inclusive, next week exclusive)
        count = df.filter(
            (pl.col('start_date') >= date) & 
            (pl.col('start_date') < (date + dt.timedelta(days=7)))
        ).height
        enrollment_counts.append((date, count))

    enrollment_df = pl.DataFrame(enrollment_counts, schema=['date', 'enrollment_count'], orient='row')
    print(enrollment_df)

    # Create bar chart
    fig = go.Figure(data=[go.Bar(x=enrollment_df['date'].to_list(), y=enrollment_df['enrollment_count'].to_list(), marker_color='cyan')])
    fig.update_layout(
        title=dict(
            text= 'Enrollment Progress Over Time',
            x=0.5,
            xanchor='center',
            yanchor='top',
            y=0.95
        ),
        xaxis_title='Date',
        yaxis_title='Number of Enrollments',
        font_size=10,
        height=400,
        width=700,
        template='plotly_dark'
    )
    fig.update_traces(marker=dict(line=dict(color='#000000', width=1)))

    fig.update_xaxes(ticklabelmode = 'period',
                     rangeslider_visible=True,
                     rangeselector=dict(
                         bgcolor='#333333',     # Color of the buttons
                         activecolor='cyan',    # Color of the active button
                         font=dict(color='white'), # certain text colors
                         buttons=list([
                             dict(count=1, label="1m", step="month", stepmode="backward"),
                             dict(count=3, label="3m", step="month", stepmode="backward"),
                             dict(count=1, label="YTD", step="year", stepmode="todate"),
                             dict(count=1, label="1y", step="year", stepmode="backward"),
                         ])
                     )
    )
    return fig