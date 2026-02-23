import boto3
import polars as pl
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go
from project_insight_part_3.methods.env_initialize import read_env_variables
from project_insight_part_3.methods.aws_functions import get_user_info
from collections import defaultdict

import pytz

def get_participant_initials():
    env_vars = read_env_variables()

    # get initials and participant db
    participant_db_path = env_vars['participant_db']
    participant_db_df = pl.read_csv(participant_db_path)
    participant_db_df = participant_db_df.select([
        'Participant ID #',
        'Initials'
    ])
    participant_db_df = participant_db_df.filter(pl.col('Participant ID #').is_not_null())
    
    # Capitalize initials and remove spaces from initials
    participant_db_df = participant_db_df.with_columns(
        pl.col('Initials').str.to_uppercase().str.replace_all(" ", "")
    )

    # Combine Participant ID # and Initials into a new column
    participant_db_df = participant_db_df.with_columns(
        (pl.col('Participant ID #').cast(pl.Utf8) + ' (' + pl.col('Initials') + ')').alias('Participant_Initials')
    )

    return participant_db_df

def get_participant_dynamo_db(participant_id: str):
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    
    # Get the needed variables
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])

    response = table.get_item(Key={"participant_id": participant_id})
    
    study_start_date = response['Item']['start_date']
    study_end_date = response['Item']['end_date']
    schedule_type = response['Item']['schedule_type']

    
    return study_start_date, study_end_date, schedule_type

def merge_survey_data():
    env_vars = read_env_variables()

    # Load Files
    try:
        survey_1a_df = pl.read_csv(env_vars['qualtrics_survey_p3_1a_path'], schema_overrides={"Date/Time": str})
        survey_1b_df = pl.read_csv(env_vars['qualtrics_survey_p3_1b_path'], schema_overrides={"Date/Time": str})
        survey_2a_df = pl.read_csv(env_vars['qualtrics_survey_p3_2a_path'], schema_overrides={"Date/Time": str})
        survey_2b_df = pl.read_csv(env_vars['qualtrics_survey_p3_2b_path'], schema_overrides={"Date/Time": str})
        survey_3_df = pl.read_csv(env_vars['qualtrics_survey_p3_3_path'], schema_overrides={"Date/Time": str})
        survey_4_df = pl.read_csv(env_vars['qualtrics_survey_p3_4_path'], schema_overrides={"Date/Time": str})

        print("Survey files loaded successfully.")
    except Exception as e:
        print(f"Error loading survey files: {e}")
        return None

    # Add column to identify survey source
    survey_1a_df = survey_1a_df.with_columns(pl.lit("Survey 1A").alias("Survey_Source"))
    survey_1b_df = survey_1b_df.with_columns(pl.lit("Survey 1B").alias("Survey_Source"))
    survey_2a_df = survey_2a_df.with_columns(pl.lit("Survey 2A").alias("Survey_Source"))
    survey_2b_df = survey_2b_df.with_columns(pl.lit("Survey 2B").alias("Survey_Source"))
    survey_3_df = survey_3_df.with_columns(pl.lit("Survey 3").alias("Survey_Source"))
    survey_4_df = survey_4_df.with_columns(pl.lit("Survey 4").alias("Survey_Source"))

    # Merge Files
    merged_df = pl.concat([survey_1a_df, survey_1b_df, survey_2a_df, survey_2b_df, survey_3_df, survey_4_df], how="vertical")
    print("Survey files merged successfully.")

    merged_df = merged_df.with_columns(pl.col("Date/Time").str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M:%S", strict=False))

    merged_df = merged_df.with_columns(pl.col("Date/Time").dt.replace_time_zone("America/Denver").dt.convert_time_zone("America/New_York"))

    merged_df = merged_df.sort("Date/Time", descending=True)

    merged_df = merged_df.with_columns(
        pl.col("Name").str.to_uppercase().str.replace_all(" ", "")
    )

    merged_df = merged_df.filter(pl.col("Date/Time").is_not_null())

    return merged_df

def match_initials_table(merged_df, participant_db_df):
    merged_df = merged_df.join(
        participant_db_df.select(['Initials', 'Participant ID #']),
        left_on='Name',
        right_on='Initials',
        how='left'
    )

    merged_df = merged_df.with_columns(
        pl.col('Participant ID #').fill_null('N/A')
    )
    
    merged_df = merged_df.rename({'Name': 'Initials', 'Survey_Source': 'Survey Source'})

    return merged_df

def generate_compliance_table_individual(participant_id: str):
    study_start_date, study_end_date, schedule_type = get_participant_dynamo_db(participant_id)
    

def get_survey_send_times_all(input_date: str):
    # Convert input_date to datetime object
    input_date_dt = datetime.strptime(input_date, "%Y-%m-%d")
    yesterday_dt = input_date_dt - timedelta(days=1)
    
    # Create timezone-aware datetime objects
    est = pytz.timezone('America/New_York')
    input_date_aware = est.localize(input_date_dt)
    yesterday_aware = est.localize(yesterday_dt)
    
    schedule_types = ["Early Bird Schedule", "Standard Schedule", "Night Owl Schedule"]
    
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    
    cloudwatch_logs = Session.client('logs')
    
    early_bird_data = defaultdict(lambda: {"Survey 1": None, "Survey 2": None, "Survey 3": None, "Survey 4": None})
    standard_data = defaultdict(lambda: {"Survey 1": None, "Survey 2": None, "Survey 3": None, "Survey 4": None})
    night_owl_data = defaultdict(lambda: {"Survey 1": None, "Survey 2": None, "Survey 3": None, "Survey 4": None})
    
    
    for schedules in schedule_types:
        
        if schedules == "Early Bird Schedule":
            log_group_name_list = ['/aws/lambda/INSIGHT_Part3_earlybird_message1', 
                                '/aws/lambda/INSIGHT_Part3_earlybird_message2',
                                '/aws/lambda/INSIGHT_Part3_earlybird_message3',
                                '/aws/lambda/INSIGHT_Part3_earlybird_message4']
            
            # Should generate one row for the input date and another with the previous dates send times
            for log_group_name in log_group_name_list:
                response = cloudwatch_logs.describe_log_streams(
                    logGroupName=log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=50
                )
                log_stream_df = pl.DataFrame(response['logStreams'])
                
                log_stream_df = log_stream_df.with_columns(
                    pl.from_epoch(pl.col('firstEventTimestamp'), time_unit="ms").alias('firstEventTimestamp'),
                    pl.from_epoch(pl.col('lastEventTimestamp'), time_unit="ms").alias('lastEventTimestamp'),
                    pl.from_epoch(pl.col('creationTime'), time_unit="ms").alias('creationTime')
                )
                
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('firstEventTimestamp'),
                    pl.col('lastEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('lastEventTimestamp'),
                    pl.col('creationTime').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('creationTime')
                )
                
                # Filter BEFORE converting to string - look for both yesterday and today
                log_stream_df = log_stream_df.filter(
                    (pl.col('firstEventTimestamp') >= yesterday_aware) &
                    (pl.col('firstEventTimestamp') < input_date_aware + timedelta(days=1))
                )
                
                # NOW convert to string after filtering
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.strftime("%Y-%m-%dT%H:%M:%S").alias('firstEventTimestamp')
                )
                
                # Put values in early_bird_dict
                for row in log_stream_df.iter_rows(named=True):
                    date_str = row['firstEventTimestamp'][:10]  # Extract "YYYY-MM-DD"
                    time_str = row['firstEventTimestamp'][11:19]  # Extract "HH:MM:SS"
                    
                    if "message1" in log_group_name:
                        early_bird_data[date_str]["Survey 1"] = time_str
                    elif "message2" in log_group_name:
                        early_bird_data[date_str]["Survey 2"] = time_str
                    elif "message3" in log_group_name:
                        early_bird_data[date_str]["Survey 3"] = time_str
                    elif "message4" in log_group_name:
                        early_bird_data[date_str]["Survey 4"] = time_str
                        
                
        elif schedules == "Standard Schedule":
            log_group_name_list = ['/aws/lambda/INSIGHT_Part3_standard_message1', 
                                '/aws/lambda/INSIGHT_Part3_standard_message2',
                                '/aws/lambda/INSIGHT_Part3_standard_message3',
                                '/aws/lambda/INSIGHT_Part3_standard_message4']
            
            for log_group_name in log_group_name_list:
                response = cloudwatch_logs.describe_log_streams(
                    logGroupName=log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=50
                )
                log_stream_df = pl.DataFrame(response['logStreams'])
                
                log_stream_df = log_stream_df.with_columns(
                    pl.from_epoch(pl.col('firstEventTimestamp'), time_unit="ms").alias('firstEventTimestamp'),
                    pl.from_epoch(pl.col('lastEventTimestamp'), time_unit="ms").alias('lastEventTimestamp'),
                    pl.from_epoch(pl.col('creationTime'), time_unit="ms").alias('creationTime')
                )
                
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('firstEventTimestamp'),
                    pl.col('lastEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('lastEventTimestamp'),
                    pl.col('creationTime').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('creationTime')
                )
                
                log_stream_df = log_stream_df.filter(
                    (pl.col('firstEventTimestamp') >= yesterday_aware) &
                    (pl.col('firstEventTimestamp') < input_date_aware + timedelta(days=1))
                )
                
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.strftime("%Y-%m-%dT%H:%M:%S").alias('firstEventTimestamp')
                )

                for row in log_stream_df.iter_rows(named=True):
                    date_str = row['firstEventTimestamp'][:10]  # Extract "YYYY-MM-DD"
                    time_str = row['firstEventTimestamp'][11:19]  # Extract "HH:MM:SS"
                    
                    if "message1" in log_group_name:
                        standard_data[date_str]["Survey 1"] = time_str
                    elif "message2" in log_group_name:
                        standard_data[date_str]["Survey 2"] = time_str
                    elif "message3" in log_group_name:
                        standard_data[date_str]["Survey 3"] = time_str
                    elif "message4" in log_group_name:
                        standard_data[date_str]["Survey 4"] = time_str
                        
        elif schedules == "Night Owl Schedule":
            log_group_name_list = ['/aws/lambda/INSIGHT_Part3_nightowl_message1',
                                '/aws/lambda/INSIGHT_Part3_nightowl_message2',
                                '/aws/lambda/INSIGHT_Part3_nightowl_message3',
                                '/aws/lambda/INSIGHT_Part3_nightowl_message4']
            
            for log_group_name in log_group_name_list:
                response = cloudwatch_logs.describe_log_streams(
                    logGroupName=log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=50
                )
                log_stream_df = pl.DataFrame(response['logStreams'])
                
                log_stream_df = log_stream_df.with_columns(
                    pl.from_epoch(pl.col('firstEventTimestamp'), time_unit="ms").alias('firstEventTimestamp'),
                    pl.from_epoch(pl.col('lastEventTimestamp'), time_unit="ms").alias('lastEventTimestamp'),
                    pl.from_epoch(pl.col('creationTime'), time_unit="ms").alias('creationTime')
                )
                
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('firstEventTimestamp'),
                    pl.col('lastEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('lastEventTimestamp'),
                    pl.col('creationTime').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('creationTime')
                )
                
                log_stream_df = log_stream_df.filter(
                    (pl.col('firstEventTimestamp') >= yesterday_aware) &
                    (pl.col('firstEventTimestamp') < input_date_aware + timedelta(days=1))
                )
                
                log_stream_df = log_stream_df.with_columns(
                    pl.col('firstEventTimestamp').dt.strftime("%Y-%m-%dT%H:%M:%S").alias('firstEventTimestamp')
                )

                for row in log_stream_df.iter_rows(named=True):
                    date_str = row['firstEventTimestamp'][:10]  # Extract "YYYY-MM-DD"
                    time_str = row['firstEventTimestamp'][11:19]  # Extract "HH:MM:SS"
                    
                    if "message1" in log_group_name:
                        night_owl_data[date_str]["Survey 1"] = time_str
                    elif "message2" in log_group_name:
                        night_owl_data[date_str]["Survey 2"] = time_str
                    elif "message3" in log_group_name:
                        night_owl_data[date_str]["Survey 3"] = time_str
                    elif "message4" in log_group_name:
                        night_owl_data[date_str]["Survey 4"] = time_str
    
    # Convert dicts to dataframes with proper structure
    early_bird_rows = []
    for date, surveys in sorted(early_bird_data.items()):
        early_bird_rows.append({
            "Date": date,
            "Survey 1": surveys["Survey 1"],
            "Survey 2": surveys["Survey 2"],
            "Survey 3": surveys["Survey 3"],
            "Survey 4": surveys["Survey 4"]
        })
    early_bird_df = pl.DataFrame(early_bird_rows)
    
    standard_rows = []
    for date, surveys in sorted(standard_data.items()):
        standard_rows.append({
            "Date": date,
            "Survey 1": surveys["Survey 1"],
            "Survey 2": surveys["Survey 2"],
            "Survey 3": surveys["Survey 3"],
            "Survey 4": surveys["Survey 4"]
        })
    standard_schedule_df = pl.DataFrame(standard_rows)
    
    night_owl_rows = []
    for date, surveys in sorted(night_owl_data.items()):
        night_owl_rows.append({
            "Date": date,
            "Survey 1": surveys["Survey 1"],
            "Survey 2": surveys["Survey 2"],
            "Survey 3": surveys["Survey 3"],
            "Survey 4": surveys["Survey 4"]
        })
    night_owl_df = pl.DataFrame(night_owl_rows)
    
    return early_bird_df, standard_schedule_df, night_owl_df


def get_survey_send_times(participant_id: str):
    study_start_date, study_end_date, schedule_type = get_participant_dynamo_db(participant_id)

    study_start_date = datetime.strptime(study_start_date, "%Y-%m-%d")
    study_end_date = datetime.strptime(study_end_date, "%Y-%m-%d")
    
    date_range = pl.date_range(
        start=study_start_date,
        end=study_end_date,
        interval="1d",
        eager=True
    )
    
    if schedule_type == "Early Bird Schedule":
        log_group_name_list = ['/aws/lambda/INSIGHT_Part3_earlybird_message1', 
                            '/aws/lambda/INSIGHT_Part3_earlybird_message2',
                            '/aws/lambda/INSIGHT_Part3_earlybird_message3',
                            '/aws/lambda/INSIGHT_Part3_earlybird_message4']
    elif schedule_type == "Standard Schedule":
        log_group_name_list = ['/aws/lambda/INSIGHT_Part3_standard_message1', 
                                '/aws/lambda/INSIGHT_Part3_standard_message2',
                                '/aws/lambda/INSIGHT_Part3_standard_message3',
                                '/aws/lambda/INSIGHT_Part3_standard_message4']
    elif schedule_type == "Night Owl Schedule":
        log_group_name_list = ['/aws/lambda/INSIGHT_Part3_nightowl_message1', 
                                '/aws/lambda/INSIGHT_Part3_nightowl_message2',
                                '/aws/lambda/INSIGHT_Part3_nightowl_message3',
                                '/aws/lambda/INSIGHT_Part3_nightowl_message4']
    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")
    
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    
    cloudwatch_logs = Session.client('logs')
    
    send_time_dict = {str(date): [] for date in date_range}
    for log_group_name in log_group_name_list:
        response = cloudwatch_logs.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=50
        )
        log_stream_df = pl.DataFrame(response['logStreams'])
        
        log_stream_df = log_stream_df.with_columns(
            pl.from_epoch(pl.col('firstEventTimestamp'), time_unit="ms").alias('firstEventTimestamp'),
            pl.from_epoch(pl.col('lastEventTimestamp'), time_unit="ms").alias('lastEventTimestamp'),
            pl.from_epoch(pl.col('creationTime'), time_unit="ms").alias('creationTime')
        )
        
        log_stream_df = log_stream_df.with_columns(
            pl.col('firstEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('firstEventTimestamp'),
            pl.col('lastEventTimestamp').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('lastEventTimestamp'),
            pl.col('creationTime').dt.replace_time_zone("UTC").dt.convert_time_zone("America/New_York").alias('creationTime')
        )
        
        study_start_dt = pl.lit(study_start_date).dt.replace_time_zone("America/New_York").dt.cast_time_unit("ms")
        study_end_dt = pl.lit(study_end_date + timedelta(days=1)).dt.replace_time_zone("America/New_York").dt.cast_time_unit("ms")
        log_stream_df = log_stream_df.filter(
            (pl.col('firstEventTimestamp') >= study_start_dt) &
            (pl.col('firstEventTimestamp') < study_end_dt)
        )
        log_stream_df = log_stream_df.with_columns(
            pl.col('firstEventTimestamp').dt.strftime("%Y-%m-%dT%H:%M:%S").alias('firstEventTimestamp')
        )
        
        # with pl.Config(tbl_rows=-1, tbl_cols=-1):
        #      display(log_stream_df)
        
        for date in date_range:
            match = None
            date_str = str(date)
            for row in log_stream_df.iter_rows(named=True):
                # Check if the timestamp string starts with the date (e.g., '2025-08-12')
                if date_str in row['firstEventTimestamp']:
                    match = row
                    break
            if match and match['firstEventTimestamp'] is not None:
                # firstEventTimestamp is already a string in "%Y-%m-%dT%H:%M:%S" format
                time_str = match['firstEventTimestamp'][11:19]  # Extract "HH:MM:SS"
                send_time_dict[date_str].append(time_str)
            else:
                send_time_dict[date_str].append(None)
                
        # Convert send_time_dict to dataframe
        send_time_df = pl.DataFrame({
            "Date": list(send_time_dict.keys()),
            "Survey 1": [times[0] if len(times) > 0 else None for times in send_time_dict.values()],
            "Survey 2": [times[1] if len(times) > 1 else None for times in send_time_dict.values()],
            "Survey 3": [times[2] if len(times) > 2 else None for times in send_time_dict.values()],
            "Survey 4": [times[3] if len(times) > 3 else None for times in send_time_dict.values()]
        })
    
    #print(send_time_df)
    
    return send_time_df

def get_dynamo_table():
    env_vars = read_env_variables()
    #print(env_vars)

    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )

    # Get the needed variables
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])

    response = table.scan()

    data = response['Items']
    df = pl.DataFrame(data)
    return env_vars, df

"""Individual Participant Compliance Check Page Methods"""

def generate_compliance_table_individual(participant_id: str):
    study_start_date, study_end_date, schedule_type = get_participant_dynamo_db(participant_id)
    
    study_start_date = datetime.strptime(study_start_date, "%Y-%m-%d")
    study_end_date = datetime.strptime(study_end_date, "%Y-%m-%d")
    
    # Make df from study start and end date in the first column, the other columns names are "Survey 1", "Survey 2", "Survey 3", and "Survey 4." Keep those empty
    date_range = pl.date_range(
        start=study_start_date,
        end=study_end_date,
        interval="1d",
        eager=True
    )
    compliance_df = pl.DataFrame({
        "Date": date_range,
        "Survey 1": [None] * len(date_range),
        "Survey 2": [None] * len(date_range),
        "Survey 3": [None] * len(date_range),
        "Survey 4": [None] * len(date_range)
    })
    #display(compliance_df)
    
    participant_db = get_participant_initials()
    participant_row = participant_db.filter(pl.col('Participant ID #') == participant_id)
    initials = participant_row.select('Initials').to_series()[0]
    
    # Check if the initials are the same as anyone elses in participant db
    same_initials_df = participant_db.filter(pl.col('Initials') == initials).filter(pl.col('Participant ID #') != participant_id)
    if same_initials_df.height > 0:
        print(f"Warning: The initials {initials} are shared by multiple participants: {same_initials_df.select('Participant ID #').to_series().to_list()}")
        use_age = True
        print(f"Use_age: {use_age}")
        age = participant_row.select('Age').to_series()[0]
    else:
        use_age = False
        age = None
        print(f"Use_age: {use_age}")
    
    # Survey send time data
    survey_send_time_df = get_survey_send_times(participant_id)
    
    merged_df = merge_survey_data()
    
    # Split the date/time column into separate date and time columns
    merged_df = merged_df.with_columns(
        pl.col("Date/Time").dt.date().alias("Date"),
        pl.col("Date/Time").dt.time().alias("Time")
    )
    
    # Checking Survey 1
    compliance_df = check_survey_1(participant_id, initials, study_start_date, study_end_date, merged_df, survey_send_time_df, compliance_df, use_age, age)
    #display(compliance_df)
    compliance_df = check_survey_2(participant_id, initials, study_start_date, study_end_date, merged_df, survey_send_time_df, compliance_df, use_age, age)
    #display(compliance_df)
    compliance_df = check_survey_3(participant_id, initials, study_start_date, study_end_date, merged_df, survey_send_time_df, compliance_df, use_age, age)
    #display(compliance_df)
    compliance_df = check_survey_4(participant_id, initials, study_start_date, study_end_date, merged_df, survey_send_time_df, compliance_df, use_age, age)
    #display(compliance_df)
    
    return compliance_df

def check_survey_1(participant_id: str, initials: str, start_date: datetime, end_date: datetime, merged_df: pl.DataFrame, send_time_df: pl.DataFrame, compliance_df: pl.DataFrame, use_age: bool = False, age: int = None):
    current_day = datetime.now().date()
    #display(compliance_df)
    
    survey_1_dict = {
        "Date": [],
        "Time": [],
        "Code": []
    }
    for row in compliance_df.iter_rows(named=True):
        survey_date = row['Date']
        if survey_date <= current_day:
            print(f"--- Checking Survey 1 for date: {survey_date} ---")

            day_in_study = (survey_date - start_date.date()).days + 1
            print(f"Day in study: {day_in_study}")

            if (day_in_study >= 1 and day_in_study <= 4) or (day_in_study == 13 or day_in_study == 14):
                if use_age is True:
                    survey_1b_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 1B') &
                        (pl.col('Age') == age)
                    )
                else:
                    survey_1b_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 1B')
                    )
                    
                if not survey_1b_row.is_empty():
                    print(f"Survey 1B completed on {survey_date}")
                    if len(survey_1b_row) == 1:
                        print(f"Found one entry for Survey 1B on {survey_date}.")
                        date = survey_1b_row["Date"][0]
                        time = survey_1b_row["Time"][0]
                        name = survey_1b_row["Name"][0]
                        
                        code = compare_times(survey_1b_row, send_time_df, 1)
                        
                        # put values in survey_1_dict
                        survey_1_dict["Date"].append(date)
                        survey_1_dict["Time"].append(time)
                        survey_1_dict["Code"].append(code)
                    elif len(survey_1b_row) > 1:
                        print(f"Multiple entries found for Survey 1B on {survey_date} for participant {initials}. Taking the first entry.")
                        date = survey_1b_row["Date"][0]
                        name = survey_1b_row["Name"][0]
                        
                        code = compare_times(survey_1b_row, send_time_df, 1)
                        # put values in survey_1_dict
                        survey_1_dict["Date"].append(date)
                        survey_1_dict["Time"].append(None)
                        survey_1_dict["Code"].append(code)
                else:
                    print(f"No entry found for Survey 1B on {survey_date} for participant {initials}.")
                    # Add this block - append None values when no entry found
                    survey_1_dict["Date"].append(survey_date)
                    survey_1_dict["Time"].append(None)
                    survey_1_dict["Code"].append("✗ NR")
                    
            elif day_in_study >= 5 and day_in_study <= 12:
                if use_age is True:
                    survey_1a_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 1A') &
                        (pl.col('Age') == age)
                    )
                else:
                    survey_1a_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 1A')
                    )
                    
                if not survey_1a_row.is_empty():
                    print(f"Survey 1A completed on {survey_date}")
                    if len(survey_1a_row) == 1:
                        print(f"Found one entry for Survey 1A on {survey_date}.")
                        date = survey_1a_row["Date"][0]
                        time = survey_1a_row["Time"][0]
                        name = survey_1a_row["Name"][0]
                        
                        code = compare_times(survey_1a_row, send_time_df, 1)
                        # Add this - append to dict for single entry
                        survey_1_dict["Date"].append(date)
                        survey_1_dict["Time"].append(time)
                        survey_1_dict["Code"].append(code)
                    elif len(survey_1a_row) > 1:
                        print(f"Multiple entries found for Survey 1A on {survey_date} for participant {initials}. Taking the first entry.")
                        date = survey_1a_row["Date"][0]
                        name = survey_1a_row["Name"][0]
                        
                        code = compare_times(survey_1a_row, send_time_df, 1)
                        # put values in survey_1_dict
                        survey_1_dict["Date"].append(date)
                        survey_1_dict["Time"].append(None)
                        survey_1_dict["Code"].append(code)
                else:
                    print(f"No entry found for Survey 1A on {survey_date} for participant {initials}.")
                    code = "✗ NR" # No Response
                    # put values in survey_1_dict
                    survey_1_dict["Date"].append(survey_date)
                    survey_1_dict["Time"].append(None)
                    survey_1_dict["Code"].append(code)
        else:
            # Add this block - for dates in the future, still append to maintain length
            survey_1_dict["Date"].append(survey_date)
            survey_1_dict["Time"].append(None)
            survey_1_dict["Code"].append(None)
    
    # Put values in compliance_df (already has "Date" column and "Survey 1" columns). Match the date values to ensure correct placement. For the "Survey 1" column put f"{code} {time}"
    ## Join compliance_df with survey_1_dict on Date
    survey_1_df = pl.DataFrame(survey_1_dict)
    compliance_df = compliance_df.join(
        survey_1_df,
        on="Date",
        how="left",
        suffix="_survey1"
    ).with_columns(
        pl.when(pl.col("Code").is_not_null())
          .then(pl.col("Code"))
          .otherwise(None)
          .alias("Survey 1")
    ).drop(["Time", "Code"])
    
    

    #display(compliance_df)
    return compliance_df

def check_survey_2(participant_id: str, initials: str, start_date: datetime, end_date: datetime, merged_df: pl.DataFrame, send_time_df: pl.DataFrame, compliance_df: pl.DataFrame, use_age: bool = False, age: int = None):
    current_day = datetime.now().date()
    survey_2_dict = {
        "Date": [],
        "Time": [],
        "Code": []
    }
    
    # Get the participant's details from dynamo table
    user_info = get_user_info(participant_id)
    user_info = user_info[0]
    message_randomizer = user_info['message_randomizer']
    
    # Convert all values in message randomizer to ints
    message_randomizer = [int(x) for x in message_randomizer]
    print(message_randomizer)
    day_list = list(range(5,13,1))
    zip_day_message = dict(zip(day_list, message_randomizer))
    print(zip_day_message)
    
    for row in compliance_df.iter_rows(named=True):
        survey_date = row['Date']
        if survey_date <= current_day:
            print(f"--- Checking Survey 2 for date: {survey_date} ---")

            day_in_study = (survey_date - start_date.date()).days + 1
            print(f"Day in study: {day_in_study}")

            if (day_in_study >= 1 and day_in_study <= 4) or (day_in_study == 13 or day_in_study == 14):
                if use_age is True:
                    survey_2b_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 2B') &
                        (pl.col('Age') == age)
                    )
                else:
                    survey_2b_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 2B')
                    )
                    
                if not survey_2b_row.is_empty():
                    print(f"Survey 2B completed on {survey_date}")
                    if len(survey_2b_row) == 1:
                        print(f"Found one entry for Survey 2B on {survey_date}.")
                        date = survey_2b_row["Date"][0]
                        time = survey_2b_row["Time"][0]
                        name = survey_2b_row["Name"][0]
                        
                        code = compare_times(survey_2b_row, send_time_df, 2)
                        
                        # put values in survey_2_dict
                        survey_2_dict["Date"].append(date)
                        survey_2_dict["Time"].append(time)
                        survey_2_dict["Code"].append(code)
                    elif len(survey_2b_row) > 1:
                        print(f"Multiple entries found for Survey 2B on {survey_date} for participant {initials}. Taking the first entry.")
                        date = survey_2b_row["Date"][0]
                        name = survey_2b_row["Name"][0]
                        
                        code = compare_times(survey_2b_row, send_time_df, 2)
                        # put values in survey_2_dict
                        survey_2_dict["Date"].append(date)
                        survey_2_dict["Time"].append(None)
                        survey_2_dict["Code"].append(code)
                else:
                    print(f"No entry found for Survey 2B on {survey_date} for participant {initials}.")
                    # Add this block - append None values when no entry found
                    survey_2_dict["Date"].append(survey_date)
                    survey_2_dict["Time"].append(None)
                    survey_2_dict["Code"].append("✗ NR")
            elif (day_in_study >= 5 and day_in_study <= 12):
                message_number = int(zip_day_message[day_in_study])
                print(f"[Survey 2] day_in_study={day_in_study} message_number={message_number} type={type(message_number)} zip_day_message={zip_day_message}")
                print(zip_day_message)
                
                if message_number == 1:
                    survey_2a_source = f"Survey 2A"
                    
                    if use_age is True:
                        survey_2a_row = merged_df.filter(
                            (pl.col('Date') == survey_date) &
                            (pl.col('Name') == initials) &
                            (pl.col('Survey_Source') == survey_2a_source) &
                            (pl.col('Age') == age)
                        )
                    else:
                        survey_2a_row = merged_df.filter(
                            (pl.col('Date') == survey_date) &
                            (pl.col('Name') == initials) &
                            (pl.col('Survey_Source') == survey_2a_source)
                        )
                        
                    if not survey_2a_row.is_empty():
                        print(f"Survey 2A completed on {survey_date}")
                        if len(survey_2a_row) == 1:
                            print(f"Found one entry for Survey 2A on {survey_date}.")
                            date = survey_2a_row["Date"][0]
                            time = survey_2a_row["Time"][0]
                            name = survey_2a_row["Name"][0]
                            
                            code = compare_times(survey_2a_row, send_time_df, 2)
                            # Add this - append to dict for single entry
                            survey_2_dict["Date"].append(date)
                            survey_2_dict["Time"].append(time)
                            survey_2_dict["Code"].append(code)
                        elif len(survey_2a_row) > 1:
                            print(f"Multiple entries found for Survey 2A on {survey_date} for participant {initials}. Taking the first entry.")
                            date = survey_2a_row["Date"][0]
                            name = survey_2a_row["Name"][0]
                            
                            code = compare_times(survey_2a_row, send_time_df, 2)
                            # put values in survey_2_dict
                            survey_2_dict["Date"].append(date)
                            survey_2_dict["Time"].append(None)
                            survey_2_dict["Code"].append(code)
                elif message_number == 0:
                    survey_2b_source = f"Survey 2B"
                    
                    if use_age is True:
                        survey_2b_row = merged_df.filter(
                            (pl.col('Date') == survey_date) &
                            (pl.col('Name') == initials) &
                            (pl.col('Survey_Source') == survey_2b_source) &
                            (pl.col('Age') == age)
                        )
                    else:
                        survey_2b_row = merged_df.filter(
                            (pl.col('Date') == survey_date) &
                            (pl.col('Name') == initials) &
                            (pl.col('Survey_Source') == survey_2b_source)
                        )
                        
                    if not survey_2b_row.is_empty():
                        print(f"Survey 2B completed on {survey_date}")
                        if len(survey_2b_row) == 1:
                            print(f"Found one entry for Survey 2B on {survey_date}.")
                            date = survey_2b_row["Date"][0]
                            time = survey_2b_row["Time"][0]
                            name = survey_2b_row["Name"][0]
                            
                            code = compare_times(survey_2b_row, send_time_df, 2)
                            # Add this - append to dict for single entry
                            survey_2_dict["Date"].append(date)
                            survey_2_dict["Time"].append(time)
                            survey_2_dict["Code"].append(code)
                        elif len(survey_2b_row) > 1:
                            print(f"Multiple entries found for Survey 2B on {survey_date} for participant {initials}. Taking the first entry.")
                            date = survey_2b_row["Date"][0]
                            name = survey_2b_row["Name"][0]
                            
                            code = compare_times(survey_2b_row, send_time_df, 2)
                            # put values in survey_2_dict
                            survey_2_dict["Date"].append(date)
                            survey_2_dict["Time"].append(None)
                            survey_2_dict["Code"].append(code)
                    
                else:
                    print(f"No entry found for Survey 2 on {survey_date} for participant {initials}.")
                    code = "✗ NR" # No Response
                    # put values in survey_2_dict
                    survey_2_dict["Date"].append(survey_date)
                    survey_2_dict["Time"].append(None)
                    survey_2_dict["Code"].append(code)
        else:
            # Add this block - for dates in the future, still append to maintain length
            survey_2_dict["Date"].append(survey_date)
            survey_2_dict["Time"].append(None)
            survey_2_dict["Code"].append(None)
    
    # Put values in compliance_df (already has "Date" column and "Survey 2" columns). Match the date values to ensure correct placement. For the "Survey 2" column put f"{code} {time}"
    ## Join compliance_df with survey_2_dict on Date
    survey_2_df = pl.DataFrame(survey_2_dict)
    compliance_df = compliance_df.join(
        survey_2_df,
        on="Date",
        how="left",
        suffix="_survey2"
    ).with_columns(
        pl.when(pl.col("Code").is_not_null())
          .then(pl.col("Code"))
          .otherwise(None)
          .alias("Survey 2")
    ).drop(["Time", "Code"])

    return compliance_df

def check_survey_3(participant_id: str, initials: str, start_date: datetime, end_date: datetime, merged_df: pl.DataFrame, send_time_df: pl.DataFrame, compliance_df: pl.DataFrame, use_age: bool = False, age: int = None):
    current_day = datetime.now().date()
    survey_3_dict = {
        "Date": [],
        "Time": [],
        "Code": []
    }
    
    for row in compliance_df.iter_rows(named=True):
        survey_date = row['Date']
        if survey_date <= current_day:
            print(f"--- Checking Survey 3 for date: {survey_date} ---")

            day_in_study = (survey_date - start_date.date()).days + 1
            print(f"Day in study: {day_in_study}")

            if day_in_study > 0 and day_in_study <= 14:
                if use_age is True:
                    survey_3_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 3') &
                        (pl.col('Age') == age)
                    )
                else:
                    survey_3_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 3')
                    )
                    
                if not survey_3_row.is_empty():
                    print(f"Survey 3 completed on {survey_date}")
                    if len(survey_3_row) == 1:
                        print(f"Found one entry for Survey 3 on {survey_date}.")
                        date = survey_3_row["Date"][0]
                        time = survey_3_row["Time"][0]
                        name = survey_3_row["Name"][0]
                        
                        code = compare_times(survey_3_row, send_time_df, 3)
                        
                        # put values in survey_3_dict
                        survey_3_dict["Date"].append(date)
                        survey_3_dict["Time"].append(time)
                        survey_3_dict["Code"].append(code)
                    elif len(survey_3_row) > 1:
                        print(f"Multiple entries found for Survey 3 on {survey_date} for participant {initials}. Taking the first entry.")
                        date = survey_3_row["Date"][0]
                        name = survey_3_row["Name"][0]
                        
                        code = compare_times(survey_3_row, send_time_df, 3)
                        # put values in survey_3_dict
                        survey_3_dict["Date"].append(date)
                        survey_3_dict["Time"].append(None)
                        survey_3_dict["Code"].append(code)
                else:
                    print(f"No entry found for Survey 3 on {survey_date} for participant {initials}.")
                    # Add this block - append None values when no entry found
                    survey_3_dict["Date"].append(survey_date)
                    survey_3_dict["Time"].append(None)
                    survey_3_dict["Code"].append("✗ NR")
        else:
            # Add this block - for dates in the future, still append to maintain length
            survey_3_dict["Date"].append(survey_date)
            survey_3_dict["Time"].append(None)
            survey_3_dict["Code"].append(None)
            
    # Put values in compliance_df (already has "Date" column and "Survey 3" columns). Match the date values to ensure correct placement. For the "Survey 3" column put f"{code} {time}"
    ## Join compliance_df with survey_3_dict on Date
    survey_3_df = pl.DataFrame(survey_3_dict)
    compliance_df = compliance_df.join(
        survey_3_df,
        on="Date",
        how="left",
        suffix="_survey3"
    ).with_columns(
        pl.when(pl.col("Code").is_not_null())
          .then(pl.col("Code"))
          .otherwise(None)
          .alias("Survey 3")
    ).drop(["Time", "Code"])
    
    return compliance_df

def check_survey_4(participant_id: str, initials: str, start_date: datetime, end_date: datetime, merged_df: pl.DataFrame, send_time_df: pl.DataFrame, compliance_df: pl.DataFrame, use_age: bool = False, age: int = None):
    current_day = datetime.now().date()
    survey_4_dict = {
        "Date": [],
        "Time": [],
        "Code": []
    }
    
    for row in compliance_df.iter_rows(named=True):
        survey_date = row['Date']
        if survey_date <= current_day:
            print(f"--- Checking Survey 4 for date: {survey_date} ---")

            day_in_study = (survey_date - start_date.date()).days + 1
            print(f"Day in study: {day_in_study}")

            if day_in_study > 0 and day_in_study <= 14:
                if use_age is True:
                    survey_4_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 4') &
                        (pl.col('Age') == age)
                    )
                else:
                    survey_4_row = merged_df.filter(
                        (pl.col('Date') == survey_date) &
                        (pl.col('Name') == initials) &
                        (pl.col('Survey_Source') == 'Survey 4')
                    )
                    
                if not survey_4_row.is_empty():
                    print(f"Survey 4 completed on {survey_date}")
                    if len(survey_4_row) == 1:
                        print(f"Found one entry for Survey 4 on {survey_date}.")
                        date = survey_4_row["Date"][0]
                        time = survey_4_row["Time"][0]
                        name = survey_4_row["Name"][0]
                        
                        code = compare_times(survey_4_row, send_time_df, 4)
                        
                        # put values in survey_4_dict
                        survey_4_dict["Date"].append(date)
                        survey_4_dict["Time"].append(time)
                        survey_4_dict["Code"].append(code)
                    elif len(survey_4_row) > 1:
                        print(f"Multiple entries found for Survey 4 on {survey_date} for participant {initials}. Taking the first entry.")
                        date = survey_4_row["Date"][0]
                        name = survey_4_row["Name"][0]
                        
                        code = compare_times(survey_4_row, send_time_df, 4)
                        # put values in survey_4_dict
                        survey_4_dict["Date"].append(date)
                        survey_4_dict["Time"].append(None)
                        survey_4_dict["Code"].append(code)
                else:
                    print(f"No entry found for Survey 4 on {survey_date} for participant {initials}.")
                    # Add this block - append None values when no entry found
                    survey_4_dict["Date"].append(survey_date)
                    survey_4_dict["Time"].append(None)
                    survey_4_dict["Code"].append("✗ NR")
        else:
            # Add this block - for dates in the future, still append to maintain length
            survey_4_dict["Date"].append(survey_date)
            survey_4_dict["Time"].append(None)
            survey_4_dict["Code"].append(None)
            
    # Put values in compliance_df (already has "Date" column and "Survey 4" columns). Match the date values to ensure correct placement. For the "Survey 4" column put f"{code} {time}"
    ## Join compliance_df with survey_4_dict on Date
    survey_4_df = pl.DataFrame(survey_4_dict)
    compliance_df = compliance_df.join(
        survey_4_df,
        on="Date",
        how="left",
        suffix="_survey4"
    ).with_columns(
        pl.when(pl.col("Code").is_not_null())
          .then(pl.col("Code"))
          .otherwise(None)
          .alias("Survey 4")
    ).drop(["Time", "Code"])
    
    return compliance_df

def compare_times(filtered_row, send_time_df, survey_number):
    #print("DEBUG: compare_times called")
    #print(f"DEBUG: filtered_row columns: {filtered_row.columns}")
    #print(f"DEBUG: filtered_row shape: {filtered_row.shape}")
    
    # Get the send time column based on survey number from the send_time_df
    survey_col = f"Survey {survey_number}"
    survey_date = str(filtered_row["Date"][0])
    
    #print(f"DEBUG: survey_date = {survey_date}, survey_complete_time = {survey_complete_time}")
    #print(f"DEBUG: send_time_df columns: {send_time_df.columns}")
    #print(f"DEBUG: send_time_df Date column sample: {send_time_df['Date'].head()}")
    
    send_time_row = send_time_df.filter(pl.col("Date") == survey_date)
    
    #print(f"DEBUG: send_time_row length: {len(send_time_row)}")

    if len(filtered_row) == 0:
        print(f"No send time found for {survey_col} on {survey_date}.")
        code = "Issue"
        return code
    elif len(filtered_row) > 1:
        # Iterate through each entry and compare times, if one is within 1 hour, print and stop
        for i in range(len(filtered_row)):
            survey_complete_time = str(filtered_row["Time"][i])
            actual_time = send_time_row[survey_col][0]
            
            
            # Check if send time is within 1 hour of survey completion time
            if actual_time is None:
                print(f"No actual send time recorded for {survey_col} on {survey_date}.")
                code = "Issue"
                continue 
            
            survey_complete_dt = datetime.strptime(f"{survey_date} {survey_complete_time}", "%Y-%m-%d %H:%M:%S")
            actual_send_dt = datetime.strptime(f"{survey_date} {actual_time}", "%Y-%m-%d %H:%M:%S")
            time_diff = (survey_complete_dt - actual_send_dt).total_seconds() / 60  # in minutes
            
            # Convert Survey complete time to America/New_York timezone and a string to be put in the table
            est = pytz.timezone('America/New_York')
            survey_complete_dt = est.localize(survey_complete_dt)
            actual_send_dt = est.localize(actual_send_dt)
            survey_complete_time_str = survey_complete_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            if (time_diff <= 60 and time_diff > 0):
                print(f"{survey_col} on {survey_date}: Survey Complete Time = {survey_complete_time_str}, Actual Send Time = {actual_time}, Time Difference (minutes) = {time_diff}")
                code = f"✓ MR {survey_complete_time_str}" # Multiple Responses, one within range
                return code
            else:
                code = "✗ MR" # Multiple Responses, none within range
    else:
        survey_complete_time = str(filtered_row["Time"][0])
        actual_time = send_time_row[survey_col][0]
        
        # Check if send time is within 1 hour of survey completion time
        if actual_time is None:
            print(f"No actual send time recorded for {survey_col} on {survey_date}.")
            return code
        
        survey_complete_dt = datetime.strptime(f"{survey_date} {survey_complete_time}", "%Y-%m-%d %H:%M:%S")
        actual_send_dt = datetime.strptime(f"{survey_date} {actual_time}", "%Y-%m-%d %H:%M:%S")
        time_diff = (survey_complete_dt - actual_send_dt).total_seconds() / 60  # in minutes
        
        # Convert Survey complete time to America/New_York timezone and a string to be put in the table
        est = pytz.timezone('America/New_York')
        survey_complete_dt = est.localize(survey_complete_dt)
        actual_send_dt = est.localize(actual_send_dt)
        survey_complete_time_str = survey_complete_dt.strftime("%Y-%m-%d %H:%M:%S")

        
        if (time_diff <= 60 and time_diff > -10):
            code = f"✓ SR {survey_complete_time_str}" # Single Response within range
            print(f"{survey_col} on {survey_date}: Survey Complete Time = {survey_complete_time_str}, Actual Send Time = {actual_time}, Time Difference (minutes) = {time_diff}")
        else:
            code = f"✗ SR {survey_complete_time_str}" # Single Response, not within range
    return code

def compliance_over_time_plot(compliance_df_percentage: pl.DataFrame):

    # Get current overall compliance over the days in study

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=compliance_df_percentage["Date"], y=compliance_df_percentage["Compliance Percentage"], mode='lines+markers', name='Compliance Percentage'))
    fig.add_trace(go.Scatter(x=compliance_df_percentage["Date"], y=compliance_df_percentage["14-Day Rolling Average"], mode='lines+markers', name='Rolling Average', opacity=0.5))

    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        title = dict(
            text="Compliance Over Time",
            x=0.5,
            xanchor='center'
        ),
        #title = "Compliance Over Time",
        xaxis_title = "Date",
        yaxis_title = "Compliance Percentage",
        yaxis=dict(range=[0, 100]),
        legend=dict(
            #title = "Legend",
            orientation="h",
            #yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        template="plotly_dark"
    )
    #fig.show()
    return fig

def calculate_compliance_percentage(compliance_df: pl.DataFrame):
    # Count the number of checkmarks in each row (each survey column) and divide by the total number of surveys (4) to get a percentage
    def count_checkmarks(row):
        checkmark_count = 0
        total_surveys = 0
        for survey in ["Survey 1", "Survey 2", "Survey 3", "Survey 4"]:
            if row[survey] is not None:
                total_surveys += 1
                if row[survey].startswith("✓"):
                    checkmark_count += 1
        if total_surveys == 0:
            return None
        return (checkmark_count / total_surveys) * 100
    
    compliance_df = compliance_df.with_columns(
        pl.struct(["Survey 1", "Survey 2", "Survey 3", "Survey 4"]).map_elements(count_checkmarks, return_dtype=pl.Float64).alias("Compliance Percentage")
    )
    
    # Calculate rolling average over the days that have occured (row 1 should have an average of day 1, row 2 should have an average of day 1 and 2, etc.)
    compliance_df = compliance_df.with_columns(
        (pl.col("Compliance Percentage").cum_sum() / 
        pl.int_range(1, pl.len() + 1)).alias("14-Day Rolling Average")
)

    return compliance_df

def get_participant_list(date_input: str):
    # Convert date_input to datetime object
    try:
        date_input_dt = datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return None
    
    env_vars = read_env_variables()
    
    aws_access_key_id = env_vars.get('aws_access_key_id') or env_vars.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = env_vars.get('aws_secret_access_key') or env_vars.get('AWS_SECRET_ACCESS_KEY')
    region_name = env_vars.get('region') or env_vars.get('REGION') or env_vars.get('AWS_DEFAULT_REGION')
    table_name = env_vars.get('insight_p3_table_name')

    try:
        
        Session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        dynamodb = Session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.scan()
        data = response['Items']
        df = pl.DataFrame(data)
        
        df = df.with_columns([
            pl.col('start_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('start_date'),
            pl.col('end_date').str.strptime(pl.Date, format="%Y-%m-%d").alias('end_date')
        ])
        
        # Remove leaderboard_link, phone_number, and message_randomizer columns
        df = df.drop(['leaderboard_link', 'phone_number', 'message_randomizer'])
        
        # Change column order to participant_id, start_date, end_date, schedule_type
        df = df.select(['participant_id', 'start_date', 'end_date', 'schedule_type'])
                
        done_with_study = df.filter(pl.col('end_date') < date_input_dt)
        
        currently_in_study = df.filter(
            (pl.col('start_date') <= date_input_dt) &
            (
                (pl.col('end_date') >= date_input_dt) |
                (pl.col('end_date').is_null())
            )
        )

        not_started = df.filter(pl.col('start_date') > date_input_dt)
        
        # Rename columns to be more user friendly
        done_with_study = done_with_study.rename({
            'participant_id': 'Participant ID',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'schedule_type': 'Schedule Type',
        })
        
        currently_in_study = currently_in_study.rename({
            'participant_id': 'Participant ID',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'schedule_type': 'Schedule Type',
        })
        
        not_started = not_started.rename({
            'participant_id': 'Participant ID',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'schedule_type': 'Schedule Type',
        })
    except Exception as e:
        print(f"Error retrieving participant list: {e}")
        df = None
    
    if df is not None:
        return {
            "done_with_study": done_with_study,
            "currently_in_study": currently_in_study,
            "not_started": not_started
        }
    else:
        return df