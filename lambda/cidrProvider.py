import boto3
import ipaddress
import os
import random
import time
import math
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from crhelper import CfnResource

# Set empty list
used = []

# Set DynamoDB object
table_name = os.environ['table_name']
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
table = dynamodb.Table(table_name)

# Initialise Debug Option
debug = 0

# Set helper object for crhelper
helper = CfnResource()

# The dictionary below describes the subnets and sizes that we need to create based on the size of the VPC, and whether or not we have internet-facing applications.
cidr_map = {
    "four_az": {
        "/26": { "internet": { "public": None, "private": [ "/28", "/28", "/28", "/28" ], "data": None },
                 "non-internet": { "public": None, "private": [ "/28", "/28", "/28", "/28" ], "data": None }, },
        "/24": { "internet": { "public": [ "/28", "/28", "/28", "/28" ], "private": [ "/27", "/27", "/27", "/27" ], "data": [ "/28", "/28", "/28", "/28" ] },
                 "non-internet": { "public": None, "private": [ "/27", "/27", "/27", "/27" ], "data": [ "/27", "/27", "/27", "/27" ] }, },
        "/22": { "internet": { "public": [ "/26", "/26", "/26", "/26" ], "private": [ "/25", "/25", "/25", "/25" ], "data": [ "/26", "/26", "/26", "/26" ] },
                 "non-internet": { "public": None, "private": [ "/25", "/25", "/25", "/25" ], "data": [ "/25", "/25", "/25", "/25" ] }, },
        "/20": { "internet": { "public": [ "/24", "/24", "/24", "/24" ], "private": [ "/23", "/23", "/23", "/23" ], "data": [ "/24", "/24", "/24", "/24" ] },
                 "non-internet": { "public": None, "private": [ "/23", "/23", "/23", "/23" ], "data": [ "/23", "/23", "/23", "/23" ] }, },
        "/18": { "internet": { "public": [ "/22", "/22", "/22", "/22" ], "private": [ "/21", "/21", "/21", "/21" ], "data": [ "/22", "/22", "/22", "/22" ] },
               "non-internet": { "public": None, "private": [ "/21", "/21", "/21", "/21" ], "data": [ "/21", "/21", "/21", "/21" ] }, },
        },
    "three_az": {
        "/26": { "internet": { "public": None, "private": [ "/28", "/28", "/28" ], "data": None },
                 "non-internet": { "public": None, "private": [ "/28", "/28", "/28" ], "data": None }, },
        "/24": { "internet": { "public": [ "/28", "/28", "/28" ], "private": [ "/27", "/27", "/27" ], "data": [ "/28", "/28", "/28" ] },
                 "non-internet": { "public": None, "private": [ "/27", "/27", "/27" ], "data": [ "/27", "/27", "/27" ] }, },
        "/22": { "internet": { "public": [ "/26", "/26", "/26" ], "private": [ "/25", "/25", "/25" ], "data": [ "/26", "/26", "/26" ] },
                 "non-internet": { "public": None, "private": [ "/25", "/25", "/25" ], "data": [ "/25", "/25", "/25" ] }, },
        "/20": { "internet": { "public": [ "/24", "/24", "/24" ], "private": [ "/23", "/23", "/23" ], "data": [ "/24", "/24", "/24" ] },
                 "non-internet": { "public": None, "private": [ "/23", "/23", "/23" ], "data": [ "/23", "/23", "/23" ] }, },
        "/18": { "internet": { "public": [ "/22", "/22", "/22" ], "private": [ "/21", "/21", "/21" ], "data": [ "/22", "/22", "/22" ] },
                 "non-internet": { "public": None, "private": [ "/21", "/21", "/21" ], "data": [ "/21", "/21", "/21" ] }, },
        },
    "two_az": {
            "/26": { "internet": { "public": None, "private": [ "/27", "/27" ], "data": None },
                     "non-internet": { "public": None, "private": [ "/27", "/27" ], "data": None }, },
            "/24": { "internet": { "public": [ "/27", "/27" ], "private": [ "/26", "/26" ], "data": [ "/27", "/27" ] },
                     "non-internet": { "public": None, "private": [ "/26", "/26" ], "data": [ "/26", "/26" ] }, },
            "/22": { "internet": { "public": [ "/25", "/25" ], "private": [ "/24", "/24" ], "data": [ "/25", "/25" ] },
                     "non-internet": { "public": None, "private": [ "/24", "/24" ], "data": [ "/24", "/24" ] }, },
            "/20": { "internet": { "public": [ "/23", "/23" ], "private": [ "/22", "/22" ], "data": [ "/23", "/23" ] },
                     "non-internet": { "public": None, "private": [ "/22", "/22" ], "data": [ "/22", "/22" ] }, },
            "/18": { "internet": { "public": [ "/21", "/21" ], "private": [ "/20", "/20" ], "data": [ "/21", "/21" ] },
                     "non-internet": { "public": None, "private": [ "/20", "/20" ], "data": [ "/20", "/20" ] }, },
        },
}

# Different regions have different numbers of availability zones and consequently we have maps for different widths of VPC.
region_width = { "us-east-1": "four_az", "us-east-2": "three_az", "us-west-2": "four_az" }

# Timestamp generation.
now = datetime.now()
timestamp = datetime.utcnow().replace(microsecond=0)

# Mapping of Cidr Notations
notation_map = {
    'XS': "/26", 
    'S' : "/24",
    'M' : '/22',
    'L' : '/20',
    "XL": '/18'
}

# Verifies region and environment against IP CIDR
region_check = { "prod-corp-us-east-1": ipaddress.ip_network('10.128.0.0/16'),
                 "prod-corp-us-east-2": ipaddress.ip_network('10.132.0.0/16'),
                 "prod-corp-us-west-2": ipaddress.ip_network('10.136.0.0/16'),
                 "qa-corp-us-east-1": ipaddress.ip_network('10.176.0.0/16'),
                 "qa-corp-us-east-2": ipaddress.ip_network('10.180.0.0/16'),
                 "dev-corp-us-east-1": ipaddress.ip_network('10.184.0.0/16'),
                 "lab-corp-us-east-1": ipaddress.ip_network('10.188.0.0/17'),
                 "lab-corp-us-east-2": ipaddress.ip_network('10.190.0.0/17'),
                 "prod-cgs-us-east-1": ipaddress.ip_network('10.129.0.0/16'),
                 "prod-cgs-us-east-1": ipaddress.ip_network('10.133.0.0/16'),
                 "prod-cgs-us-east-1": ipaddress.ip_network('10.137.0.0/16'),
                 "qa-cgs-us-east-1": ipaddress.ip_network('10.177.0.0/16'), 
                 "qa-cgs-us-east-2": ipaddress.ip_network('10.181.0.0/16'),  
                 "dev-cgs-us-east-1": ipaddress.ip_network('10.185.0.0/16'), 
                 "lab-cgs-us-east-1": ipaddress.ip_network('10.188.128.0/17'), 
                 "lab-cgs-us-east-2": ipaddress.ip_network('10.190.128.0/17'), 
                 "prod-fms-us-east-1": ipaddress.ip_network('10.130.0.0/16'),
                 "prod-fms-us-east-2": ipaddress.ip_network('10.134.0.0/16'),
                 "prod-fms-us-west-1": ipaddress.ip_network('10.138.0.0/16'),
                 "qa-fms-us-east-1": ipaddress.ip_network('10.178.0.0/16'), 
                 "qa-fms-us-east-2": ipaddress.ip_network('10.182.0.0/16'),  
                 "dev-fms-us-east-1": ipaddress.ip_network('10.186.0.0/16'), 
                 "lab-fms-us-east-1": ipaddress.ip_network('10.189.0.0/17'), 
                 "lab-fms-us-east-2": ipaddress.ip_network('10.191.0.0/17') 
                 }

subnetKeys = ["SubnetPrivate1","SubnetPrivate2","SubnetPrivate3","SubnetPrivate4",
              "SubnetPublic1","SubnetPublic2","SubnetPublic3","SubnetPublic4",
              "SubnetData1","SubnetData2","SubnetData3","SubnetData4"]

# Function to populate the empty used list by querying the DynamoDB table
def populate_list():
  # Empty list to be populated from DynamoDB
  tableparams = { 'ProjectionExpression':"cidr_block" }
  # Scan DynamoDB for allocated address
  ip_allocated = table.scan(**tableparams)
  # Loop thorugh results and append returned values to list
  for i in ip_allocated['Items']:
    for key, value in i.items():
      used.append(ipaddress.ip_network(value))
  return used

def get_next(size_Id, env_id, used):
  # ranges       - Array of available IP address ranges from which we can pick our (hopefully much smaller) address range
  # used         - Array of ranges currently in use that impact the available address space and cannot be interfered with
  # request_size - CIDR size (e.g. "/24")

  for key, value in notation_map.items():
    if key == size_Id:
      notation_size = value
  # Lookup region sepcified inside the region_lookup dictionary and assign the correct IP value.
  range = region_check[env_id]
  # From the current range, take the base address, and replace the CIDR suffix with our requested CIDR suffix.
  # This is the range we will return if available, and we will use this as an iterator to step forward in chunks of our CIDR range
  current = ipaddress.ip_network(str(range.network_address) + notation_size)
  # If this current range is contained within the main range
  while(range.overlaps(current)):
    if(debug):
      #print("Current Range: " + str(current))
      current_used = str(current)

    # Busy flag used to indicate that this block is partially or completely in use and is therefore unavailable to us.
    busy = 0

    # Here we only consider this range if the current range fits within the available space
    if(current.num_addresses <= range.num_addresses):
      # Now we walk through all unavailable ranges to see if any overlap with our current attempt
      for unavailable in used:
        if(unavailable.overlaps(current) or current.overlaps(unavailable)):
          busy = 1
          if(debug):
            #print("Unavailable range at: " + str(current))
            unavailable_range = str(current)
          break
      # If we get to this point then the no unavailable ranges overlap so we have found our candidate and can return it
      if(not busy):
        if(debug):
          print("Found a range at: " + str(current))
          #cidr_return = s(current)
        return current
    current = ipaddress.ip_network(str(current.broadcast_address + 1) + notation_size)
  
def get_subnets(region, internet_facing, my_range):
  # vpc_range = get_next(my_range)
  # region    - The region that the VPC will reside in (e.g. us-east-1, or us-west-2)
  # vpc_range - The VPC network address range as an "ipaddress" object (e.g. 10.188.0.0/24)
  # internet_facing - "internet" for internet facing VPCs and "non-internet" for non-internet-facing VPCs (usually resulting in no "public" layer)
  # First we create the CIDR width suffix for the VPC
  cidr    = "/" + str(my_range.prefixlen)

  # Now we collect the number of AZs for this region
  width   = region_width[region]

  # Space to return the resultant dictionary of information
  results = {}

  # Starting address
  next = my_range.network_address

  # We process the Private range first as that is likely to be the largest subnets.
  # For efficient use of space, it is best to allocate from the largest to the smallest subnets in that sequence.
  # Private layers tend to be larger as they are usually where most of the workload lives (in a good design, at least).
  if(debug):
    print("About to start a private range with: " + str(next))
  # Only generate results if this layer requires subnets
  if(cidr_map[width][cidr][internet_facing]["private"] is not None):
    # Temporary storage for the subnets for this layer
    subnets = []
    # We loop through each of the CIDR values for this layer
    for subnet in cidr_map[width][cidr][internet_facing]["private"]:
      # Now we create a network subnet based on the next available base address with a capacity as defined in the cidr_map lookup (from the loop)
      subnet_range = ipaddress.ip_network(str(next) + subnet)
      # And we can now append that to the temporary storage
      subnets.append(str(subnet_range))
      # And move the next available address on by the size of this subnet (find the end, add one)
      next = subnet_range.broadcast_address + 1
    # Here we have a complete set of subnet ranges for this layer so we create the appropriate entry in the results dictionary
    results["private"] = subnets

  # The public layer is likely to have either the same size, or larger, subnets than the Data layer so we process that next
  if(debug):
    print("About to start a public range with: " + str(next))
  # Only generate results if this layer requires subnets
  if(cidr_map[width][cidr][internet_facing]["public"] is not None):
    # Temporary storage for the subnets for this layer
    subnets = []
    # We loop through each of the CIDR values for this layer
    for subnet in cidr_map[width][cidr][internet_facing]["public"]:
      # Now we create a network subnet based on the next available base address with a capacity as defined in the cidr_map lookup (from the loop)
      subnet_range = ipaddress.ip_network(str(next) + subnet)
      # And we can now append that to the temporary storage
      subnets.append(str(subnet_range))
      # And move the next available address on by the size of this subnet (find the end, add one)
      next = subnet_range.broadcast_address + 1
    # Here we have a complete set of subnet ranges for this layer so we create the appropriate entry in the results dictionary
    results["public"] = subnets

  # And here we process the Data layer
  if(debug):
    print("About to start a data range with: " + str(next))
  # Only generate results if this layer requires subnets
  if(cidr_map[width][cidr][internet_facing]["data"] is not None):
    # Temporary storage for the subnets for this layer
    subnets = []
    # We loop through each of the CIDR values for this layer
    for subnet in cidr_map[width][cidr][internet_facing]["data"]:
      # Now we create a network subnet based on the next available base address with a capacity as defined in the cidr_map lookup (from the loop)
      subnet_range = ipaddress.ip_network(str(next) + subnet)
      # And we can now append that to the temporary storage
      subnets.append(str(subnet_range))
      # And move the next available address on by the size of this subnet (find the end, add one)
      next = subnet_range.broadcast_address + 1
    # Here we have a complete set of subnet ranges for this layer so we create the appropriate entry in the results dictionary
    results["data"] = subnets

  # We now have a complete set of subnet ranges in our resuts dictionary so we return it to the caller
  return results

def formatOutput(vpc_cidr, subnets):

  output = {}
  output['VPCCidr'] = vpc_cidr
  
  # check if the Private layer exists 
  if 'private' in subnets:
    for i in range(len(subnets["private"])):
     output["SubnetPrivate%s"%(i+1)] = subnets["private"][i]
  # check if the Data layer exists 
  if 'data' in subnets:
    for i in range(len(subnets["data"])):
     output["SubnetData%s"%(i+1)] = subnets["data"][i]
  # check if the Public layer exists 
  if 'public' in subnets:
    for i in range(len(subnets["public"])):
      output["SubnetPublic%s"%(i+1)] = subnets["public"][i]
  
  # setting all empty values to empty string
  for key in subnetKeys:
    if not key in output:
      output[key] = ""
  
  return output

@helper.create
def cidr_create(event, _):
  # Assigning environment variables from input parameter headers.
  environment     = event['ResourceProperties']['Environment']
  network         = event['ResourceProperties']['Network']
  internet_facing = event['ResourceProperties']['Internet']
  region          = event['ResourceProperties']['Region']
  size_Id         = event['ResourceProperties']['Sizing']
  # Concat variables 
  env_id          = environment + '-' + network + '-' +  region  
  my_list = populate_list()
  my_range = get_next(size_Id, env_id, my_list)

  # Putting data into the DynamoDB table
  vpc_vended_id = "vpc_vended_%s"%(math.ceil(time.time()))
  table.put_item(
    Item={
      'cidr_block': str(my_range),
      'geoenv_id': env_id,
      'account_id': 'null',
      'vpc_id': 'null',
      'email_id': 'null',
      'size_id': size_Id,
      'time_allocated': str(timestamp),
      'physical_resource_id': vpc_vended_id,
    }
  )
      
  subnets = get_subnets(region, internet_facing, my_range)
  subnets['vpc_cidr'] = str(my_range)
  # add the formated result to the Data key
  helper.Data = formatOutput(str(my_range), subnets)
  return vpc_vended_id

@helper.update
def cidr_update(event, __):
  # Assigning environment variables from input parameter headers.
  environment     = event['ResourceProperties']['Environment']
  network         = event['ResourceProperties']['Network']
  internet_facing = event['ResourceProperties']['Internet']
  region          = event['ResourceProperties']['Region']
  size_Id         = event['ResourceProperties']['Sizing']
  # Concat variables 
  env_id          = environment + '-' + network + '-' +  region  
  vpc_vended_id = event['PhysicalResourceId']
  my_list = populate_list()
  my_range = get_next(size_Id, env_id, my_list)
  table.update_item(
    Key={
      'physical_resource_id':vpc_vended_id,
      },
      UpdateExpression="set size_id=:s, geoenv_id=:g, cidr_block=:c, account_id=:a, email_id=:e, vpc_id=:v, time_upated=:t",
      ExpressionAttributeValues={
        ":s": size_Id,
        ":g": env_id,
        ":c": str(my_range),
        ":a": "null",
        ":e": "null",
        ":v": "null",
        ":t": str(timestamp),
      }
    )

  subnets = get_subnets(region, internet_facing, my_range)
  # add the formated result to the Data key
  helper.Data = formatOutput(str(my_range), subnets)


# CIDR block deletion function
@helper.delete
def cidr_deletion(event, __):
  # Set variable 'vpc_vended_id' to that of the 'PhysicalResourceId' value.
  vpc_vended_id = event['PhysicalResourceId']
  # Delete CIDR row
  table.delete_item(
      Key={
          'physical_resource_id': vpc_vended_id
      }
  )

def lambda_handler(event, context): 
  helper(event, context)
  