import boto3
import polars as pl
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