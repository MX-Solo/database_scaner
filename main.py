from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

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

# Insert data into the table
def insert_data(session):
    import uuid
    try:
        rows = [
            (uuid.uuid4(), "Alice", "alice@example.com", "Hello, this is a safe comment."),
            (uuid.uuid4(), "Bob", "bob@example.com", "This is another safe comment."),
            (uuid.uuid4(), "Charlie", "charlie@example.com", "<script>alert('XSS1');</script>"),
            (uuid.uuid4(), "Diana", "diana@example.com", "<img src='x' onerror='alert(\"XSS2\")'>"),
            (uuid.uuid4(), "Eve", "eve@example.com", "This is yet another safe comment."),
        ]

        for row in rows:
            session.execute(
                "INSERT INTO your_table (id, name, email, comment) VALUES (%s, %s, %s, %s)",
                row
            )
        print("Data inserted into 'your_table'.")
    except Exception as e:
        print(f"Error inserting data: {e}")

# Query and display data in batches of 5 rows
def query_data_in_batches(session, batch_size=2):
    try:
        counter = batch_size
        last_token = None
        while True:
            # If it's the first batch, do not use token, otherwise use token for pagination
            if last_token:
                query = f"SELECT id, name, email, comment FROM your_table WHERE token(id) > token({last_token}) LIMIT {batch_size}"
            else:
                query = f"SELECT id, name, email, comment FROM your_table LIMIT {batch_size}"

            rows = session.execute(query)
            rows_fetched = list(rows)  # Convert rows to a list
            
            if not rows_fetched:
                break  # Exit loop if no rows are fetched
            
            print(f"Batch: {counter}")
            counter += batch_size
            for row in rows_fetched:
                print(f"ID: {row.id}, Name: {row.name}, Email: {row.email}, Comment: {row.comment}")
                last_token = row.id  # Update the last token to continue the next batch
    except Exception as e:
        print(f"Error querying data in batches: {e}")



# Main function to orchestrate tasks
def main():
    host = "127.0.0.1"
    port = 9042
    keyspace = "your_keyspace"

    cluster, session = connect_to_cluster(host, port)
    if not session:
        return

    try:
        set_keyspace(session, keyspace)
        # insert_data(session)
        query_data_in_batches(session)
    finally:
        if cluster:
            cluster.shutdown()
            print("Connection closed.")

if __name__ == "__main__":
    main()
