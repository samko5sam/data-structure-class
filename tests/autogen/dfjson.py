import json

# Open the JSON file and load it into a Python dictionary
with open('../../rankings.json', 'r') as file:
    data = json.load(file)

# Accessing data for a specific date and app
date = '2025-03-18'
app = 'wis_tw_ios'

# Access the rank and category for a specific app on a specific date
if date in data and app in data[date]:
    chunks = []
    # Define the chunk size
    chunk_size = 2

    # Convert the data to a list of tuples if it's a dictionary
    items = list(data.items()) if isinstance(data, dict) else data

    # Create chunks of data
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        chunks.append(chunk)

    # For debugging purposes, you can print the chunks
    for index, chunk in enumerate(chunks):
        print(f"Chunk {index + 1}: {chunk}")
    # print(f"Data chunks for {app} on {date}: {chunks}")
else:
    print(f"No data found for {app} on {date}")
