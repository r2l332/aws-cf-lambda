# CIDR Provider Lambda Function

In order to provision CIDR blocks for VPC's a Lambda CIDR calculator has been created. 
The calculator takes some input parameters such as; *Environment, Connection, Region, Network and Sizing* and with this information 
generates a VPC CIDR Block along with subnets.

The following Python library is used and needs to be manually zipped up alongside the code and uploaded to the Lambda function: crhelper
More information on the library can be found here:
[Git crhelper repo](https://github.com/aws-cloudformation/custom-resource-helper)

A guide on how to do this can be found here: 
[AWS Lambda Additional Dependencies](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html#python-package-dependencies)

The function can be broken down into *3 main steps*:

## Step 1

Access DynamoDB table and return all items stored within the *cidr_block* column. Append all returned items from previous call into an empty list.  


## Step 2

Iterate through the notation_map using the *Sizing* input variable to allocate the CIDR notation, assign the result to *notation_size* variable.
Concatanate the following input values  Environment, Network and Region to form something similar to the following *<ENV>-<NETWORK>-<REGION>* and assign to the *env_id* variable. 
Then use the *env_id* variable to lookup the Cidr block within the *region_check* map.
Then setting the variable current to that of the located value within the *region_check* map replacing the CIDR notation with that of the one previously generated called *notation_size*.
The next few steps allow us to verify from our previous list whether or not we can use an address based on: 
1. Whether it is already allocated or 
2. If it fits within the avalaible range.

Once we have our result it is returned to the next step.

## Step 3

The final function is to use the CIDR block returned by the previous function and to divide it into the correct subnet blocks.
To calculate the correct subnets two lookup maps are called, the first map is called region_width which allocates the number of Availaibility Zone's to the correct region, for example *"us-east-1": "four_az"*. Once we have allocated the value we can use it within the *cidr_map* to find the correct number of AZ's and subnets along with associated cidr notations.

The subnets are then returned in the Cloudformation ouputs to be later used in the vending process.

## Additional notes

### Stack Delete
If at any point the VPC that was previously vended is no longer required the Cloudformation stack can be deleted which will remove the row previously added from the DynamoDB table.
To make this process easier we create a column in DynamoDB called *physical_resource_id*, the value of which is created using the string *vpc_vended_* and appending an epoch timestamp to it. This unique ID is searchable using the *PhysicalResourceId* key.

Once the we locate the *PhysicalResourceId* it is then possible to remove the previously created row in the DynamoDB table and as a result freeing up that CIDR block.

Please note that due to the DynamoDB eventual consistency model, there may be a short delay in the row being completely removed from AWS's backend, this means that if the CidrProvider function is called again in short succession it is possible that the previously removed CIDR block may not be immediately re-used.  

### Stack Update
Should for any reason the vended VPC require modification, the CidrProvider Lambda function, using the *crhelper* library can handle changes and update DynamoDB with the adjusted values. 
