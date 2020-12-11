#!/usr/bin/env python

"""This is just an example of how one might export data from the NCPI fhir 
server using the bulk export and the ncpi-fhir-utility. 

Please note that I'm using my fhir_host library to manage cookies/authentication
details, but that's fairly trivial and can easily be ignored for users who 
need to use different authentication mechanisms or prefer to manage those
details differently. 

This script doesn't actually do anything with the data it pulls down aside from 
printing a single example from each of the profiles pulled along with counts. It 
is just here as a crude example.
"""

from collections import defaultdict
from argparse import ArgumentParser, FileType
from urllib.parse import urlparse
from ncpi_fhir_utility.client import FhirApiClient
from time import sleep
from pprint import pformat
import json
from base64 import b64decode

from fhir_walk.config import DataConfig 
from fhir_walk.fhir_host import FhirHost

config = DataConfig.config()
env_options = config.list_environments()
parser = ArgumentParser()

parser.add_argument("resources", 
		nargs='+', 
		help='One or more resource types to be downloaded (all if none are provided)')
parser.add_argument("-e", 
            "--env", 
            choices=env_options, 
            default='dev', 
            help=f"Remote configuration to be used")
args = parser.parse_args()

fhir_host = config.set_host(args.env)
fhir_server = FhirHost.host()


"""
# This is just an FhirApiClient object and could have been created using 
# the standard constructor. I'm using the fhir_walk library so that it can
# incorporate the cookie used by the public server 

client = FhirApiClient(
		base_url=args.host, 
		auth=(args.username, args.password)
)"""
client = fhir_host.client()

failures = {}
resources = args.resources

# Request our data to be fhir+json separated by new lines
prefix = f"{fhir_host.target_service_url}/$export?_outputFormat=application%2Ffhir%2Bndjson"

# We need to specify our types as comma separated list
if len(resources) > 0:
	endpoint = f"{prefix}&_type={','.join(args.resources)}"

# bulk export currently requires that we get an asynchronous response
cheaders = client._fhir_version_headers()
cheaders['prefer'] = "respond-async"

# for the ncpi controlled server, access is restricted by a cookie
if fhir_server.cookie:
    cheaders['cookie'] = fhir_server.cookie

# This is the intial GET. The response will contain the URL where the download 
# links will be found once the job has completed
success,result = client.send_request("GET", endpoint, headers=cheaders)
if success:
	# The payload is embedded inside the header. The response from this will include
	# the final data or a recommended wait time
	content_location = result['response_headers']['Content-Location']
	retry_after = 120

	# For each profile requested, there will be one or more links containing the 
	# actual data. 
	data_sources = defaultdict(list)

	while retry_after > 0:
		success,result = client.send_request("GET", content_location, headers=cheaders)
		if 'Retry-After' in result['response_headers']:
			retry_after = int(result['response_headers']['Retry-After'])
			print(f"Sleeping as requested: {retry_after}")
			sleep(retry_after)
		else:
			for chunk in result['response']['output']:
				data_sources[chunk['type']].append(chunk['url'])
			retry_after = 0

	print(f"{len(data_sources)} were found")

	total_rows_seen = 0
	for source_type  in data_sources.keys():
		print(f"{source_type} : {len(data_sources[source_type])} urls found")

		# For now, we'll just keep them until we've collected all and 
		# report on how many we found
		data = []
		for url in data_sources[source_type]:
			success, result = client.send_request("GET", url, headers=cheaders)
			# The data comes as a byte string of base 64 encoded JSon objects, each
			# separated by a new line.
			payload = b64decode(result['response']['data']).decode("utf-8").split("\n")
			data += payload
		total_rows_seen += len(data)
		print(f"Total of {len(data)} rows")

		# Give the user a taste of what is about to be deleted!
		print(data[0])

	print(f"Total records encountered: {total_rows_seen}")
else:
	print("There was a problem with the request. Response can be seen below.")
	print(result['response'])