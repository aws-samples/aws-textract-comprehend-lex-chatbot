##########################################################################
# Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
# http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the
# License for the specific language governing permissions and limitations under the License.
##########################################################################
import urllib
import boto3
import os

textract = boto3.client('textract')

sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
sns_role_arn = os.environ["SNS_ROLE_ARN"]


def handler(event, context):
	source_bucket = event['Records'][0]['s3']['bucket']['name']
	object_key = urllib.parse.unquote_plus(
					event['Records'][0]['s3']['object']['key'])

	textract_result = textract.start_document_text_detection(
		DocumentLocation={
			"S3Object": {
				"Bucket": source_bucket,
				"Name": object_key
			}
		},
		NotificationChannel={
			"SNSTopicArn": sns_topic_arn,
			"RoleArn": sns_role_arn
		}
	)
	print(textract_result)
