import boto3
import polars as pl
from datetime import datetime, timedelta
from project_insight_part_3.methods.env_initialize import read_env_variables

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