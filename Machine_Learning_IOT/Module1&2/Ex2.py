
#Import the libraries

import psutil
import redis
import time
import uuid
from datetime import datetime
import argparse

# Establish connection to the Redis server
def establish_redis_connection(server_host, server_port, account_user, account_password):
    redis_server = redis.Redis(
        host=server_host,
        port=server_port,
        username=account_user,
        password=account_password
    )
    return redis_server

# Setting up the argument parser for command line inputs
argument_parser = argparse.ArgumentParser(description='Manage Redis Connection Parameters')
argument_parser.add_argument('--host', type=str, default='redis-18934.c293.eu-central-1-1.ec2.cloud.redislabs.com')
argument_parser.add_argument('--port', type=int, default=18934)
argument_parser.add_argument('--user', type=str, default='default')
argument_parser.add_argument('--password', type=str, default='IvXQkMs50KIlQzp5ZSFmV2fX6hF1DFiK')
arguments = argument_parser.parse_args()

# Creating and verifying the Redis connection
redis_connection = establish_redis_connection(arguments.host, arguments.port, arguments.user, arguments.password)
if redis_connection.ping():
    print('Connection established with Redis server')

# Getting the hardware address
hardware_address = hex(uuid.getnode())

# Time retention configurations
one_day_seconds = 86400 * 1000  # in milliseconds
thirty_days_seconds = 2592000 * 1000  # in milliseconds

# Initialize or update the time series in Redis for battery and power status
for metric in ['battery', 'power']:
    series_name = f'{hardware_address}:{metric}'
    try:
        redis_connection.ts().create(series_name, retention_msecs=one_day_seconds)
        print(f'Time series for {metric} created with one-day retention.')
    except redis.ResponseError:
        redis_connection.ts().alter(series_name, retention_msecs=one_day_seconds)
        print(f'Time series for {metric} already exists, retention updated.')

# Initialize or update the time series for plugged in duration
plugged_series_name = f'{hardware_address}:plugged_seconds'
try:
    redis_connection.ts().create(plugged_series_name, retention_msecs=thirty_days_seconds)
    print(f'Time series for plugged seconds created with thirty-days retention.')
except redis.ResponseError:
    redis_connection.ts().alter(plugged_series_name, retention_msecs=thirty_days_seconds)
    print(f'Time series for plugged seconds already exists, retention updated.')

# Monitor and store power status at regular intervals
accumulated_plugged_seconds = 0
while True:
    current_time = time.time()
    current_time_ms = int(current_time * 1000)  # Redis requires milliseconds

    # Retrieve battery status
    battery_stats = psutil.sensors_battery()
    battery_percentage = battery_stats.percent
    is_plugged = int(battery_stats.power_plugged)

    # Store battery and power status to Redis time series
    redis_connection.ts().add(f'{hardware_address}:battery', current_time_ms, battery_percentage)
    redis_connection.ts().add(f'{hardware_address}:power', current_time_ms, is_plugged)

    # Display the current status
    formatted_time = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f'{formatted_time} - {hardware_address}:power = {is_plugged}')

    # Track plugged in duration
    if is_plugged:
        accumulated_plugged_seconds += 1
        redis_connection.ts().add(f'{hardware_address}:plugged_seconds', current_time_ms, accumulated_plugged_seconds)

    # Wait for 1 second before the next read
    time.sleep(1)
