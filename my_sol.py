import csv
from datetime import datetime

def read_zones_file(zones_file_path):
    """
    Read the CSV file that maps each station to its pricing zone and
    translate this into a dictionary.
    """

    # Create an empty dictionary to store the mapping of stations to zones
    zone_map = {}

    # Open the zones file for reading
    with open(zones_file_path, "r") as file:
        # Create a CSV reader object to read the file
        reader = csv.DictReader(file)

        # Iterate over each row in the CSV file
        for row in reader:
            # Extract the station and zone information from the current row
            station = row["station"]
            zone = int(row["zone"])

            # Map the station to its corresponding zone in the zone_map dictionary
            zone_map[station] = zone

    # Return the populated zone_map dictionary
    return zone_map

def read_journey_data(journey_data_path):
    """
    Read the CSV file containing the journey data and translate this into a
    dictionary mapping each user to a list of their journeys.
    """

    # Create an empty list to store the journey data
    journey_data = []

    # Open the journey data file for reading
    with open(journey_data_path, "r") as file:
        # Create a CSV reader object to read the file
        reader = csv.DictReader(file)

        # Create a dictionary to store journeys for each user
        journeys = {}

        # Iterate over each row in the CSV file
        for row in reader:
            # Extract the user ID, station, direction, and time information from the current row
            user_id = row["user_id"]
            station = row["station"]
            direction = row["direction"]
            time = datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%S")

            # Check if the user ID already exists in the journeys dictionary
            if user_id not in journeys:
                # If not, create an empty list to store journeys for that user
                journeys[user_id] = []

            if direction == "IN":
                # Create a new journey dictionary for an "IN" event
                journey = {
                    "user_id": user_id,
                    "station_in": station,
                    "direction_in": direction,
                    "time_in": time,
                    "direction_out": None,
                    "time_out": None,
                    "station_out": None
                }
                # Append the journey to the list of journeys for the user
                journeys[user_id].append(journey)
            else:
                # For an "OUT" event, update the last journey in the list for the user
                last_journey = journeys[user_id][-1]
                last_journey["direction_out"] = direction
                last_journey["time_out"] = time
                last_journey["station_out"] = station

    # Extend the journey_data list with the journeys from all users
    for user_journeys in journeys.values():
        journey_data.extend(user_journeys)
    
    # Return the populated journey_data list
    return journey_data


def calculate_billing_amount(zone_map, journey_data):
    """
    Calculate the total amount each user owes by aggregating the cost of their journeys.
    """

    billing_data = {}
    daily_spending = {}
    monthly_spending = {}
    daily_cap = 15
    monthly_cap = 100

    for journey in journey_data:
        user_id = journey["user_id"]
        station_in = journey["station_in"]
        station_out = journey["station_out"]
        time_in = journey["time_in"]
        time_out = journey["time_out"]


        if user_id not in billing_data:
            billing_data[user_id] = 0

        # Get the zones for the stations
        if station_in in zone_map and station_out in zone_map:
                zone_in = zone_map[station_in]
                zone_out = zone_map[station_out]
        else:
                # Handle missing zone information
                billing_data[user_id] += 5
                continue

        # Calculate cost based on the zones
        base_cost = 2.0  # Base fee

        if zone_in == 1:
               billing_data[user_id] += 0.8
        elif zone_in in [2, 3]:
                billing_data[user_id] += 0.5
        elif zone_in in [4, 5]:
                billing_data[user_id] += 0.3
        else:
                billing_data[user_id] += 0.1
             
        if zone_out == 1:
            billing_data[user_id] += 0.8
        elif zone_out in [2, 3]:
            billing_data[user_id] += 0.5
        elif zone_out in [4, 5]:
            billing_data[user_id] += 0.3
        else:
            billing_data[user_id] += 0.1

        billing_data[user_id] += base_cost

       # Update daily spending

        # Get the date from the time_in
        date = time_in.date()

        # Check if user is not present in daily spending
        if user_id not in daily_spending:
            # Create entry for user with current date and zero amount
            daily_spending[user_id] = {"dates": [date], "amount": 0}
        else:
            # Append current date to the list of dates for the user
            daily_spending[user_id]["dates"].append(date)
            # Find the latest date for the user
            latest_date = max(daily_spending[user_id]["dates"])

            # Check if the current date is greater than the latest date
            if date > latest_date:
                # Set the amount for the current date to the billing data
                daily_spending[user_id]["amount"] = billing_data[user_id]
            else:
                # Add the billing data to the existing amount for the current date
                daily_spending[user_id]["amount"] += billing_data[user_id]

        # Find the latest date for the user
        latest_date = max(daily_spending[user_id]["dates"]) if user_id in daily_spending else None

        # Apply the daily cap to the billing data if it exceeds the cap
        if user_id in daily_spending and latest_date == date and daily_spending[user_id]["amount"] > daily_cap:
            billing_data[user_id] = min(billing_data[user_id], daily_cap)

       # Update monthly spending

        # Check if user is not present in monthly spending
        if user_id not in monthly_spending: 
            # Create entry for user with current month and zero amount
            monthly_spending[user_id] = {"months": [date.month], "amount": 0}  
        else:
            # Append current month to the list of months for the user
            monthly_spending[user_id]["months"].append(date.month)  
            # Find the latest month for the user
            latest_month = max(monthly_spending[user_id]["months"])  
            # Check if the current month is greater than the latest month
            if date.month > latest_month:  
                # Set the amount for the current month to the billing data
                monthly_spending[user_id]["amount"] = billing_data[user_id]  
            else:
                 # Add the billing data to the existing amount for the current month
                monthly_spending[user_id]["amount"] += billing_data[user_id] 

        # Apply monthly cap

        # Find the latest month for the user
        latest_month = max(monthly_spending[user_id]["months"]) if user_id in monthly_spending else None  
        if user_id in monthly_spending and latest_month == date.month and monthly_spending[user_id]["amount"] > monthly_cap:
            # Apply the monthly cap to the billing data if it exceeds the cap
            billing_data[user_id] = min(billing_data[user_id], monthly_cap) 

    return billing_data

   
def write_results(output_file_path, billing_data):
    """
    Write the billing output to a CSV file, with each line containing the
    user ID and their billing amount (£).
    """
    # Open the output file for writing
    with open(output_file_path, "w", newline="") as file:
        # Create a CSV writer object to write data to the file
        writer = csv.writer(file)

        # Write the header row containing column names
        writer.writerow(["user_id", "billing_amount"])

        # Iterate over each user ID in sorted order
        for user_id in sorted(billing_data):
            # Retrieve the billing amount for the current user and format it to 2 decimal places
            billing_amount = "{:.2f}".format(billing_data[user_id])

            # Write a row with the user ID and billing amount
            writer.writerow([user_id, billing_amount])
    
    print(
            f"Successfully wrote billing output to {output_file_path} at "
            f"{datetime.now()}"
        )


def process_data(zones_file_path, journey_data_path, output_file_path):
    zone_map = read_zones_file(zones_file_path)
    journey_data = read_journey_data(journey_data_path)
    billing_data = calculate_billing_amount(zone_map, journey_data)
    write_results(output_file_path, billing_data)

# Entry point
if __name__ == "__main__":
    zones_file_path = "zone_map.csv"
    journey_data_path = "journey_data.csv"
    output_file_path = "output.csv"
    process_data(zones_file_path, journey_data_path, output_file_path) 