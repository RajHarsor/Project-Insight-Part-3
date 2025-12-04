import os
from dotenv import load_dotenv


def check_env_file_exists() -> bool:
    """Check if the .env file exists and load environment variables if it does.

    Returns:
        bool: True if the .env file exists, False otherwise.
    """
    load_dotenv() 
    return os.path.exists('.env')  

def check_env_variables() -> tuple[bool, str]:
    """
    Check if the required environment variables are set in the .env file only.
    Returns (success: bool, message: str) tuple.
    """
    current_dir = os.getcwd()
    env_path = os.path.join(current_dir, '.env')

    # Check if .env file exists first
    if not os.path.exists('.env'):
        return False, f"No .env file found in current directory: {current_dir}"

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