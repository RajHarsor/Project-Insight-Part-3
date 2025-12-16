import plotly.graph_objects as go
import polars as pl
import datetime as dt
import boto3
from typing import Dict, Any
from .env_initialize import read_env_variables

def pie_chart_progress() -> go.Figure:
    """Creates a pie chart showing participant progress.

    Returns:
        go.Figure: A Plotly Figure object representing the pie chart.
    """
    # Initialize AWS session
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )

    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])
    response = table.scan()
    
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
    fig.update_layout(title_text='Participant Progress Overview', font_size=10)    
    # Adjust legend size
    fig.update_layout(legend=dict(font=dict(size=8)))
    # adjust overall pie size
    fig.update_traces(marker=dict(line=dict(color='#000000', width=1)))
    
    return fig