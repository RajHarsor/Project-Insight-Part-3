import boto3
import os
from dotenv import load_dotenv
from ..methods.env_initialize import read_env_variables

def add_user_to_database(participant_id,
                         start_date,
                         end_date, 
                         phone_number, 
                         lb_link, 
                         schedule, 
                         message_randomizer):
    """Add a new user to the AWS DynamoDB table.
    
    Args:
        participant_id (int): The participant ID.
        start_date (str): The start date for the participant.
        end_date (str): The end date for the participant.
        phone_number (str): The participant's phone number.
        lb_link (str): The leaderboard link for the participant.
        schedule (str): The schedule type for the participant.
        message_randomizer (list): A list indicating when to send messages.
    
    Returns:
        bool: True if the user was added successfully, False otherwise.
        message (str): Success or error message.
    """
    
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])
    
    try:
        table.put_item(
            Item={
                'participant_id': int(participant_id),
                'start_date': start_date,
                'end_date': end_date,
                'phone_number': phone_number,
                'leaderboard_link': lb_link,
                'schedule_type': schedule,
                'message_randomizer': message_randomizer
            }
        )
        return True, "User added successfully."
    except Exception as e:
        print(f"Error adding user to database: {e}")
        return False, f"Error adding user to database: {e}"

def get_user_info(participant_id):
    """
    Retrieve user information from the AWS DynamoDB table.
    
    Args:
        participant_id (int): The participant ID.
    
    Returns:
        dict: User information if found, None otherwise.
    """
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])
    
    try:
        response = table.get_item(
            Key={
                'participant_id': int(participant_id)
            }
        )
        return response.get('Item', None), 'Error: User not found.'
    except Exception as e:
        print(f"Error retrieving user from database: {e}")
        return None, f"Error retrieving user from database: {e}"

def update_user_info(participant_id, attribute_name, new_value):
    """
    Update user information in the AWS DynamoDB table.
    
    Args:
        participant_id (int): The participant ID.
        attribute_name (str): The attribute name to update.
        new_value: The new value for the attribute.
    
    Returns:
        bool: True if the update was successful, False otherwise.
        message (str): Success or error message.
    """
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])
    
    try: 
        table.update_item(
            Key={
                'participant_id': int(participant_id)
            },
            UpdateExpression=f'SET {attribute_name} = :val',
            ExpressionAttributeValues={
                ':val': new_value
            }
        )
        return True, "User information updated successfully."
    except Exception as e:
        print(f"Error updating user in database: {e}")
        return False, f"Error updating user in database: {e}"

def delete_user_from_database(participant_id):
    """
    Delete a user from the AWS DynamoDB table.
    
    Args:
        participant_id (int): The participant ID.
    Returns:
        bool: True if the deletion was successful, False otherwise.
        message (str): Success or error message.
    """
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    dynamodb = Session.resource('dynamodb')
    table = dynamodb.Table(env_vars['insight_p3_table_name'])
    
    try:
        table.delete_item(
            Key={
                'participant_id': int(participant_id)
            }
        )
        return True, "User deleted successfully."
    except Exception as e:
        print(f"Error deleting user from database: {e}")
        return False, f"Error deleting user from database: {e}"

def send_test_sms(participant_phone_number, message):
    """
    Send a test SMS to the specified phone number using AWS SNS.
    
    Args:
        participant_phone_number (str): The participant's phone number in E.164 format.
        message (str): The message to send.
    
    Returns:
        bool: True if the SMS was sent successfully, False otherwise.
        message (str): Success or error message.
    """
    env_vars = read_env_variables()
    
    Session = boto3.Session(
        aws_access_key_id=env_vars['aws_access_key_id'],
        aws_secret_access_key=env_vars['aws_secret_access_key'],
        region_name=env_vars['region']
    )
    
    sns = Session.client('sns')
    
    try:
        sns.publish(
            PhoneNumber=participant_phone_number,
            Message=message
        )
        return True, "SMS sent successfully."
    except Exception as e:
        print(f"Error sending test SMS: {e}")
        return False, f"Error sending test SMS: {e}"