import os
from dotenv import load_dotenv, find_dotenv, dotenv_values


def check_env_file_exists() -> bool:
    """Check if the .env file exists and load environment variables if it does.

    Returns:
        bool: True if the .env file exists, False otherwise.
    """
    load_dotenv() 
    return os.path.exists('.env')  # Check if .env file exists in the current directory

def check_env_variables() -> tuple[bool, str]:
    """
    Check if the required environment variables are set in the .env file only.
    Returns (success: bool, message: str) tuple.
    """
    current_dir = os.getcwd()
    env_path = os.path.join(current_dir, '.env')

    # Check if .env file exists first
    if not os.path.exists(env_path):
        return False, f"No .env file found via find_dotenv (looking in {os.getcwd()} and parents)"

    # Read the .env file directly to check only those variables
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        return False, f"Error reading .env file: {e}"

    required_vars = ['aws_access_key_id', 'aws_secret_access_key', 'region', 'insight_p3_table_name']
    missing_vars = []

    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing_vars.append(var)

    if missing_vars:
        return False, f"Missing environment variables: {', '.join(missing_vars)}"
    else:
        return True, f"All required environment variables found: {', '.join(required_vars)}"

def create_env_file(aws_access_key_id: str,
    aws_secret_access_key: str,
    p3_table_name: str,
    qualtrics_survey_p3_1a_path: str = None,
    qualtrics_survey_p3_1b_path: str = None,
    qualtrics_survey_p3_2a_path: str = None,
    qualtrics_survey_p3_2b_path: str = None,
    qualtrics_survey_p3_3_path: str = None,
    qualtrics_survey_p3_4_path: str = None,
    participant_db: str = None):
    """Create a .env file with the provided environment variables.
    Args:
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        table_name (str): DynamoDB Table Name.
        qualtrics_survey_p3_1a_path (str, optional): Path for Qualtrics Survey 1A. Defaults to None.
        qualtrics_survey_p3_1b_path (str, optional): Path for Qualtrics Survey 1B. Defaults to None.
        qualtrics_survey_p3_2a_path (str, optional): Path for Qualtrics Survey 2A. Defaults to None.
        qualtrics_survey_p3_2b_path (str, optional): Path for Qualtrics Survey 2B. Defaults to None.
        qualtrics_survey_p3_3_path (str, optional): Path for Qualtrics Survey 3. Defaults to None.
        qualtrics_survey_p3_4_path (str, optional): Path for Qualtrics Survey 4. Defaults to None.
        participant_db (str, optional): Path for Participant Database. Defaults to None.
    """
    
    with open('.env', 'w') as f:
        f.write(f"aws_access_key_id={aws_access_key_id}\n")
        f.write(f"aws_secret_access_key={aws_secret_access_key}\n")
        f.write(f"region=us-east-1\n")
        f.write(f"insight_p3_table_name={p3_table_name}\n")

        # Optional Qualtrics survey paths
        if qualtrics_survey_p3_1a_path is not None:
            f.write(f"qualtrics_survey_p3_1a_path={qualtrics_survey_p3_1a_path}\n")
        if qualtrics_survey_p3_1b_path is not None:
            f.write(f"qualtrics_survey_p3_1b_path={qualtrics_survey_p3_1b_path}\n")
        if qualtrics_survey_p3_2a_path is not None:
            f.write(f"qualtrics_survey_p3_2a_path={qualtrics_survey_p3_2a_path}\n")
        if qualtrics_survey_p3_2b_path is not None:
            f.write(f"qualtrics_survey_p3_2b_path={qualtrics_survey_p3_2b_path}\n")
        if qualtrics_survey_p3_3_path is not None:
            f.write(f"qualtrics_survey_p3_3_path={qualtrics_survey_p3_3_path}\n")
        if qualtrics_survey_p3_4_path is not None:
            f.write(f"qualtrics_survey_p3_4_path={qualtrics_survey_p3_4_path}\n")
        if participant_db is not None:
            f.write(f"participant_db={participant_db}\n")
    
def update_env_variable(variable: str, value: str):
    """Update a specific environment variable in the .env file.
    Args:
        variable (str): The name of the environment variable to update.
        value (str): The new value for the environment variable.
    """
    # Read existing variables from .env file
    path = find_dotenv()
    if not path:
        path = '.env'
        
    env_vars = dotenv_values(path)
    # Convert to mutable dict if not already (dotenv_values returns dict)
    env_vars = dict(env_vars)
    
    # Update the specified variable
    env_vars[variable] = value

    # Write updated variables back to .env file
    with open(path, 'w') as f:
        for key, val in env_vars.items():
             if val is None: val = ""
             f.write(f"{key}={val}\n")

def read_env_variables() -> dict:
    """Read all environment variables from the .env file.
    Returns:
        dict: A dictionary of environment variables and their values.
    """
    path = os.path.join(os.getcwd(), '.env')
    if not os.path.exists(path):
        return {}
    env_vars = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        return {}
    return env_vars