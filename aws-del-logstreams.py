from operator import truediv
from pprint import pprint
from datetime import datetime
import account
import argparse
import dotenv

# Setup command-line arguments


def setup_cli_args():
    parser = argparse.ArgumentParser(
        description='Lists, and optionally deletes old log streams.')

    parser.add_argument(
        "-p", "--profile", dest="profile", help="Specifies the AWS profile (from credentials file) to be used.")

    parser.add_argument(
        "-v", "--verbose", help="Verbose output.", action="store_true", dest="verbose", default=False)

    parser.add_argument(
        "-d", "--delete", help="Delete old log streams.", action="store_true", dest="delete")

    parser.add_argument(
        "-m", "--maxdays", help="List/Delete log streams older than this number of days.", dest="maxdays", default=548)

    parser.add_argument(
        "-r", "--region", help="Set a region if not already included in profile.", dest="region")

    parser.add_argument(
        "-n", "--name", help="Include log groups that contain <name>.", dest="name", default="")

    return parser.parse_args()


# Display the AWS Account ID for reference
def display_startup_parameters(args, account):
    print("*******************************************")
    print(" Account ID: {0}".format(account.account_id))
    print(" Region:     {0}".format(account.session.region_name))

    if (account.profile_name is None):
        print(" Profile:    Using env configuration")
    else:
        print(" Profile:    {0}".format(account.profile_name))

    print(" Date:       {0}".format(datetime.now().strftime("%c")))
    print(" Max Days:   {0}".format(args.maxdays))
    print(" Name:       {0}".format(args.name))
    print(" Delete:     {0}".format(args.delete))
    print(" Verbose:    {0}".format(args.verbose))
    print("*******************************************")


# load the environment variables
dotenv.load_dotenv()

# Get command-line arguments
args = setup_cli_args()

# Create AWS Account object using the profile name specified
aws_account = account.Account(args.profile, args.region)

display_startup_parameters(args, aws_account)

client = aws_account.session.client('logs')

# Get the initial list of log groups (only the first n groups are returned)
log_groups = client.describe_log_groups()
total_log_groups_count = 0
total_log_stream_count = 0
total_log_streams_flagged = 0

if (args.verbose):
    print("===== BEGIN CSV FORMAT =====")

for log_group in log_groups['logGroups']:
    log_group_name = log_group['logGroupName']

    # If the log group doesn't have any stored data, no point continuing with this group
    if(log_group['storedBytes'] > 0):
        if (args.name.lower() in log_group_name.lower()):
            total_log_groups_count += 1
            next_token = None

            while True:
                if next_token:
                    # Making subsequent calls to the same log group
                    log_streams = client.describe_log_streams(
                        logGroupName=log_group_name, nextToken=next_token)
                else:
                    # First time around for this log group
                    log_streams = client.describe_log_streams(
                        logGroupName=log_group_name)

                # Get the next log streams token
                next_token = log_streams.get('nextToken', None)

                for stream in log_streams['logStreams']:
                    total_log_stream_count += 1
                    log_stream_name = stream['logStreamName']

                    # Apparently some log streams don't have last ingestion times
                    if ('lastIngestionTime' in stream):
                        last_ingestion_timestamp = stream['lastIngestionTime']

                        # Convert to a date/time for comparison
                        last_ingestion_time = datetime.fromtimestamp(
                            stream['lastIngestionTime']/1000)
                    else:
                        last_ingestion_time = None

                    stored_bytes = stream['storedBytes']

                    if (last_ingestion_time):
                        age_in_days = (datetime.today() -
                                       last_ingestion_time).days
                    else:
                        # We've ran into an edge case where there is no ingestion date
                        # present, so we skip these to be safe
                        age_in_days = -1

                    # Check to see if the log stream is older than the specified number of days
                    if (age_in_days > int(args.maxdays)):
                        total_log_streams_flagged += 1

                        # Display in CSV format if verbose is on
                        if (args.verbose):
                            print("\"{0}\",\"{1}\",\"{2}\",{3}".format(
                                log_group_name, log_stream_name, last_ingestion_time, age_in_days))

                        # If the delete switch was specified in the arguments, delete the log stream
                        if (args.delete):
                            client.delete_log_stream(
                                logGroupName=log_group_name, logStreamName=log_stream_name)

                # Have we reached the last log stream?
                if (not next_token or len(log_streams['logStreams']) == 0):
                    break

if (args.verbose):
    print("===== END CSV FORMAT =====")

print("\r\n  {: 6d} log groups searched".format(total_log_groups_count))
print("  {0: 6d} log streams searched".format(total_log_stream_count))

if (args.delete):
    print("  {0: 6d} log streams deleted".format(total_log_streams_flagged))
else:
    print("  {0: 6d} log streams flagged".format(total_log_streams_flagged))
