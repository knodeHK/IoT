'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from datetime import datetime

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import logging
import time
import getopt

# import cassandra driver 
# connecting local cassandra instant
from cassandra.cluster import Cluster
cluster = Cluster(['127.0.0.1'])
session = cluster.connect('iot')

import json
from pandas.io.json import json_normalize

# Custom MQTT message callback
def customCallback(client, userdata, message):
#	print("Received a new message: ")
#	print(message.payload)
	
#	print('Json string')
# 	Testing simply string
#	json_string = '{"first_name": "Guido", "last_name":"Rossum"}'

# 	Put the paylod from the message into json_string for printing and processing

	json_string = message.payload

#	Use json.loads function to parse the string to a parsed string, beware load vs loads, dump vs dumps, for detail reference to API doc.	
	parsed_json = json.loads(json_string)
#	print(parsed_json)

#	Search the object name from the tree of json, beware the first level [0]
#	print(parsed_json[0]['ObjectName'])

#	Normalizing the parsed_json string to pandas data object.
#	result = json_normalize(parsed_json, 'ObjectInfo', ['ObjectName'])
	if message.topic == '5287c1cc-eea2-11e6-bf34-000c29158b55/Data' :
		result = json_normalize(parsed_json, 'ObjectContent', ['ObjectName', 'TimeStamp'])
#		result = json_normalize(parsed_json, 'ObjectDetails', ['ObjectName'])	
		print(result)
#		print(result.dtypes)


		for index, row in result.iterrows():	

#			print(row['ObjectDetails'].type)
#			print(row['FieldName'].type)

			
			list_string = str([str(x) for x in row['ObjectDetails']])
			print(list_string)

#			test_statement = row['ObjectDetails'].astype(str).values
#			test_statement = row['ObjectDetails'] + "')"

			# Need to convert the timestamp format 
#			timestamp_string = "{:%B %d, %Y}".format(row['TimeStamp'])
			timestamp_string = '2017-02-17 11:25:12'
#			print(timestamp_string) 
			timestamp = str(row['TimeStamp'])
			datetime_object = datetime.strptime(timestamp, '%H:%M:%S %d %b %Y')
			print(datetime_object)
#			print(timestamp.dt.strftime('%Y-%m-%d'))

			sql_insert = "INSERT INTO data (registry_no, object_name, field_name, created_date, objectdetails) VALUES (" 
			sql_data = "5287c1cc-eea2-11e6-bf34-000c29158b55" + ", '" + row['ObjectName'] + "', '" + row['FieldName'] + "', '" + str(datetime_object)	+ "', "  + list_string + ")"

			sql_statement = sql_insert + sql_data

			print ("-- sql_statement --") 
			print (sql_statement) 

			session.execute(sql_statement)

	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

# Usage
usageInfo = """Usage:
Use certificate based mutual authentication:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
Use MQTT over WebSocket:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w
Type "python basicPubSub.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-c, --cert
	Certificate file path
-k, --key
	Private key file path
-w, --websocket
	Use MQTT over WebSocket
-h, --help
	Help information
"""

# Read in command-line parameters
useWebsocket = False
host = ""
rootCAPath = ""
certificatePath = ""
privateKeyPath = ""
try:
	opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:", ["help", "endpoint=", "key=","cert=","rootCA=", "websocket"])
	if len(opts) == 0:
		raise getopt.GetoptError("No input parameters!")
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print(helpInfo)
			exit(0)
		if opt in ("-e", "--endpoint"):
			host = arg
		if opt in ("-r", "--rootCA"):
			rootCAPath = arg
		if opt in ("-c", "--cert"):
			certificatePath = arg
		if opt in ("-k", "--key"):
			privateKeyPath = arg
		if opt in ("-w", "--websocket"):
			useWebsocket = True
except getopt.GetoptError:
	print(usageInfo)
	exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
	print("Missing '-e' or '--endpoint'")
	missingConfiguration = True
if not rootCAPath:
	print("Missing '-r' or '--rootCA'")
	missingConfiguration = True
if not useWebsocket:
	if not certificatePath:
		print("Missing '-c' or '--cert'")
		missingConfiguration = True
	if not privateKeyPath:
		print("Missing '-k' or '--key'")
		missingConfiguration = True
if missingConfiguration:
	exit(2)

# Configure logging
logger = None
if sys.version_info[0] == 3:
	logger = logging.getLogger("core")  # Python 3
else:
	logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub", useWebsocket=True)
	myAWSIoTMQTTClient.configureEndpoint(host, 443)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
myAWSIoTMQTTClient.subscribe("SystemRegistry", 1, customCallback)
myAWSIoTMQTTClient.subscribe("5287c1cc-eea2-11e6-bf34-000c29158b55/Data", 1, customCallback)
#time.sleep(2)
time.sleep(200000)

# Publish to the same topic in a loop forever
loopCount = 0
#while True:
#	myAWSIoTMQTTClient.publish("sdk/test/Python", "New Message " + str(loopCount), 1)
#	loopCount += 1
#	time.sleep(1)
