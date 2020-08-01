# CidrProvider

Local dependencies:
1. Python3.7 installed
2. AWS CLI installed: 
   1. Installation guide: [AWS CLI Installation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
3. IAM permissions to access Lambda
   1.  Creating IAM policies AWS: [AWS Policy creation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html)

## Packaging steps:

The CidrProvider Lambda function requires some external dependencies that by default are excluded from the Lambda Python runtime.

In order for this function to work a zip file should be created with all the required dependencies therein.  
When generating this zip file locally good practice would be to install the dependencies within a virtualenv.


## Mac Installation

Create a zip package with all the required libraries within a virtualenv.

```console
user@local:~$ python3.7 -m venv env
user@local:~$ source env/bin/activate
(env):~$ cd env/lib/python3.7/site-packages
(env)env/lib/python3.7/site-packages:~$ pip install crhelper -t .
(env)env/lib/python3.7/site-packages:~$ pip install boto3 -t .
(env)env/lib/python3.7/site-packages:~$ zip $HOME/cidrProvider.zip *
(env):~$ deactivate
```

Once the virtualenv is deactivated the terminal will be returned back to bash or whichever shell is used.  

**Adding the script to the zip package.**

```console
user@local:~$ zip -g cidrProvider.zip cidrProvider.py
```

After the package has been created the next step is to push the zip file up to the Lambda function.  
For this to work you'll need to have awscli installed and the correct IAM permissions in place to upload the package.

```console
user@local:~$ aws lambda update-function-code \ 
>  --function-name <FUNCTION_NAME> \ 
>  --zip-file fileb://<FUNCTION_ZIP> \
>  --profile <AWS_PROFILE>
```

## Lambda Function Install 

To deploy the Lambda function from scratch the following resources are required.

1. DynamoDB table
   1. Region set to "eu-west-1"
   2. Set the table name to: vpccidrtable
   3. Partition Key called "phsical_resource_id"
   4. Read/Write capacity set to 1
2. IAM Role 
   1. Create Role Name: 
   2. AWSLambdaBasicExecutionPolicy
   ```javascript
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            }
        ]
    }
   ```
   1. Custom Policy
   ```javascript
    {
        "Statement": [
            {
                "Action": [
                    "dynamodb:BatchGet*",
                    "dynamodb:DescribeTable",
                    "dynamodb:Get*",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:Delete*",
                    "dynamodb:Update*",
                    "dynamodb:PutItem"
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:<ACCOUNT_NUMBER>:table/<DYNAMODB_TABLE_NAME>",
                "Effect": "Allow"
            }
        ]
    }
   ```
3. From local laptop/desktop upload the previously created zip file
4. Environment variable set
   1. Key: table_name
   2. Value: vpccidrtable
5. Set the Handler to the following: "cidrProvider.lambda_handler"
6. Set runtime to Python 3.7
7. Attach Custom Role to the lambda function

**Note** Before running the next steps please update the ServiceToken with the AWS LAMBDA function ARN.

1. Upload template into Cloudformation
2. Create stack name
3. Update the input parameters
4. Run the stack


