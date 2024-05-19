import os
import subprocess
import json
import argparse

def run_script(script_name):
    try:
        subprocess.run(['python', script_name], check=True)
        print(f"Successfully ran {script_name}")
    except subprocess.CalledProcessError:
        print(f"Failed to run {script_name}")

def load_crawler_scripts(config_file):
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return data['crawler_scripts']
    except FileNotFoundError:
        print("Configuration file not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON from the configuration file.")
        return []

def main(config_file):
    crawler_scripts = load_crawler_scripts(config_file)
    if not crawler_scripts:
        print("No crawler scripts to run.")
        return
    
    for crawler_script in crawler_scripts:
        run_script(crawler_script)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run all crawler scripts.')
    parser.add_argument('--config', type=str, default='crawler_config.json', help='Path to the JSON configuration file with crawler scripts.')
    args = parser.parse_args()

    main(args.config)
