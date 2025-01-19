import re
import os

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


host = "127.0.0.1"
port = 9042
keyspace = "your_keyspace"
regex_file = "allrole.txt"
columns_to_check = ['comment', 'email']
base_path = "owasp_crs/rules"
files_to_process = [
    "REQUEST-941-APPLICATION-ATTACK-XSS.conf"
]


def extract_rx_patterns():
    # Regex pattern to find SecRule with @rx
    pattern = r'^SecRule.*?"(@rx.*?)(?<!\\)"\s\\$'

    # List to store results
    results = []

    # Process each file
    for file_name in files_to_process:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    match = re.search(pattern, line)
                    if match:
                        results.append(f"{file_name},{match.group(1)}")

    # Write results to the output file
    with open(regex_file, "w", encoding="utf-8") as output:
        output.write("\n".join(results))

    print(f"Extracted data has been saved in {regex_file}.")

# Configuration for database connection
def connect_to_cluster(host="127.0.0.1", port=9042):
    try:
        cluster = Cluster([host], port=port)
        session = cluster.connect()
        print("Successfully connected to ScyllaDB!")
        return cluster, session
    except Exception as e:
        print(f"Error connecting to ScyllaDB: {e}")
        return None, None
    
# Set the keyspace
def set_keyspace(session, keyspace):
    try:
        session.set_keyspace(keyspace)
        print(f"Keyspace set to '{keyspace}'!")
    except Exception as e:
        print(f"Error setting keyspace: {e}")


    
# Read and compile regex patterns from the file
def load_regex_patterns(file_path):
    try:
        with open(file_path, 'r') as file:
            patterns = []
            for line in file:
                # Split by comma to extract category and regex pattern
                parts = line.strip().split(",", 1)
                if len(parts) == 2:
                    category = parts[0]
                    regex_pattern = parts[1].strip().split(" ", 1)[1]
                    compiled_pattern = re.compile(regex_pattern)
                    patterns.append((category, compiled_pattern))
        return patterns
    except Exception as e:
        print(f"Error reading regex patterns: {e}")
        return []


# Check comments against regex patterns
def check_comments_against_patterns(session, patterns):
    try:
        query = "SELECT id, name, email, comment FROM your_table"
        rows = session.execute(query)

        for row in rows:
            matched = False  # Flag to stop further checks if a match is found
            for column_name in columns_to_check:  # Add the columns to check
                if matched:
                    break  # Stop checking further columns if a match is already found
                column_value = getattr(row, column_name, "")
                for category, compiled_pattern in patterns:  # Iterate over patterns with their categories
                    match = compiled_pattern.search(column_value)
                    if match:
                        print(f"ID: {row.id}, Category: {category}, Matched Text in Column {column_name}: {match.group(0)}")
                        matched = True  # Mark as matched to stop further checks
                        break  # Stop checking further patterns for this column
    except Exception as e:
        print(f"Error checking comments against patterns: {e}")



# Main function to orchestrate tasks
def main():

    #update role file : allrole.txt
    extract_rx_patterns()

    cluster, session = connect_to_cluster(host, port)
    if not session:
        return

    try:
        set_keyspace(session, keyspace)

        # Load regex patterns
        patterns = load_regex_patterns(regex_file)
        if not patterns:
            print("No valid regex patterns loaded.")
            return

        # Check comments against patterns
        check_comments_against_patterns(session, patterns)
    finally:
        if cluster:
            cluster.shutdown()
            print("Connection closed.")

if __name__ == "__main__":
    main()
