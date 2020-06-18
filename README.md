## Deriving conversational insights from invoices with Amazon Textract, Amazon Comprehend, and Amazon Lex  

This sample is based on the blog post (Link to be specified). It shows you how to use AWS AI services to automate text data processing and insight discovery. With AWS AI services such as Amazon Textract, Amazon Comprehend and Amazon Lex, you can set up an automated serverless solution to address this requirement. We will walk you through below steps:
1) Extract text from receipts or invoices in pdf or images with Amazon Textract.
2) Derive insights with  Amazon Comprehend.
3) Interact with these insights in natural language using Amazon Lex.


## Services Used
This solution uses AI services, serverless technologies and managed services to
implement a scalable and cost-effective architecture.
* AWS CodeStar – Sets up the web UI for the chatbot and continuous delivery pipeline. 
* Amazon Cognito – Lets you add user signup, signin, and access control to your web and mobile apps quickly and easily. 
* AWS Lambda – Executes code in response to triggers such as changes in data, shifts in system state, or user actions. Because Amazon S3 can directly trigger a Lambda function, you can build a variety of real-time serverless data-processing systems. 
* Amazon Lex – Provides an interface to create conversational chatbots.
* Amazon Comprehend – NLP service that uses machine learning to find insights and relationships in text.
* Amazon Textract– Uses ML to extract text and data from scanned documents in PDF, JPEG, or PNG formats. 
* Amazon Simple Storage Service (Amazon S3) – Serves as an object store for your documents and allows for central management with fine-tuned access controls.


## This sample includes:

* README.md - this file

* cfntemplate.yml - this file contains the AWS Serverless Application Model (AWS SAM) used
  by AWS CloudFormation to deploy your application.
  
* AWS Lambda functions writted in Python present in src/Lambda folder for implementing calls to Amazon Textract, Amazon       Comprehend and the fulfillment code for Amazon Lex  


## Solution Overview 

The following diagram illustrates the architecture of the solution

![](arch.png)

The architecture contains the following steps:

1.	The backend user or administrator uses the AWS Management Console or AWS Command Line Interface (AWS CLI) to upload the PDF documents or images to an S3 bucket. 
2.	The Amazon S3 upload triggers a AWS Lambda function.
3.	The Lambda function invokes an Amazon Textract StartDocumentTextDetection async API, which sets up an asynchronous job to detect text from the PDF you uploaded.
4.	Amazon Textract notifies Amazon Simple Notification Service (Amazon SNS) when text processing is complete.
5.	A second Lambda function gets the notification from SNS topic when the job is completed  to detect text.
6.	Once the lambda is notified of job completion from Amazon SNS, it calls a  Amazon Textract GetDocumentTextDetection  async API to receive the result from asynchronous operation and loads the results into an S3 bucket.
7.	A Lambda function is used for fulfillment of the Amazon Lex intents. For a more detailed sequence of interactions please refer to the Building your chatbot step in “Deploying the Architecture with Cloudformation” section.
8.	Amazon Comprehend uses ML to find insights and relationships in text. The lambda function uses boto3 APIs that Amazon Comprehend provides for entity and key phrases detection.
  a.	In response to the Bot’s welcome message, the user types “Show me the invoice summary”, this invokes the GetInvoiceSummary Lex intent and the Lambda function uses the Amazon Comprehend DetectEntities API for fulfillment
  b.	When the user types “Get me the invoice details”, this invokes the GetInvoiceDetails intent, Amazon Lex prompts the user to enter Invoice Number, and the Lambda function uses the Amazon Comprehend DetectEntities API to return the Invoice Details message
  c.	When the user types “Can you show me the invoice notes for <invoice number>”, this invokes the GetInvoiceNotes intent, and the Lambda function uses the Amazon Comprehend DetectKeyPhrases API to return comments associated with the invoice

9.	You deploy the Lexbot Web UI in your AWS Cloudformation template by using an existing CloudFormation stack as a nested stack. To download the stack, see Deploy a Web UI for Your Chatbot. This nested stack deploys a Lex Web UI, the webpage is served as a static website from an S3 bucket. The web UI uses Amazon Cognito to generate an access token for authentication and uses AWS CodeStar to set up a delivery pipeline.The end-users interact this chatbot web UI. Please refer to this AWS github repo if you need more details on how to setup a Web UI for your Amazon Lex chatbots - https://github.com/aws-samples/aws-lex-web-ui. 



## Deploy 1 click
[![button](launchstack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?stackName=lexbot&templateURL=https://aws-codestar-us-east-1-820570838999-meaningfulconve-pipe.s3.amazonaws.com/template-export.yml)
## License

This project is licensed under the Apache-2.0 License.

