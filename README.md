# aws-delete-logstreams
Delete log streams from an AWS account based on age (in days) and name filter.

Usage:
| switch |           | description |
|--------|-----------|-------------|
| -h     | --help    | Show this help message and exit     |
| -p     | --profile | Specifies the AWS profile (from credentials file) to be used. |
| -v     | --verbose | Verbose output. |
| -d     | --delete  | Delete old log streams. |
| -m     | --maxdays | List/Delete log streams older than this number of days. |
| -r     | --region  | Set a region if not already included in profile. |
| -n     | --name    | Include log groups that contain <name>. |
