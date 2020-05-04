#
# Written by Michael Mattioli
#

import os
import boto3
import email
import re
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def get_message_from_s3(message_id):

    incoming_email_bucket = os.environ["MailS3Bucket"]
    incoming_email_prefix = os.environ["MailS3Prefix"]

    if incoming_email_prefix:
        object_path = f"{incoming_email_prefix}/{message_id}"
    else:
        object_path = message_id

    # Create a new S3 client.
    client_s3 = boto3.client("s3")

    # Get the email object from the S3 bucket.
    object_s3 = client_s3.get_object(Bucket = incoming_email_bucket, Key = object_path)

    # Read the content of the message.
    file = object_s3["Body"].read()

    return file

def create_message(file):

    sender = os.environ["MailSender"]
    recipient = os.environ["MailRecipient"]

    # Parse the email body.
    mailobject = email.message_from_string(file.decode("utf-8"))

    # Create a new subject line.
    subject_original = mailobject["Subject"]
    subject = f"FW: {subject_original}"

    # Get all "From" fields.
    separator = ";"
    from_addresses = separator.join(mailobject.get_all("From"))

    # The body text of the email.
    body_text = f"The attached message was received from {from_addresses}"

    # The file name to use for the attached message. Uses regex to remove all
    # non-alphanumeric characters, and appends a file extension.
    filename = f"{re.sub('[^0-9a-zA-Z]+', '_', subject_original)}.eml"

    # Create a MIME container.
    msg = MIMEMultipart()

    # Create a MIME text part.
    text_part = MIMEText(body_text, _subtype = "html")

    # Attach the text part to the MIME message.
    msg.attach(text_part)

    # Add subject, from, and to lines.
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Create a new MIME object.
    att = MIMEApplication(file, filename)
    att.add_header("Content-Disposition", "attachment", filename = filename)

    # Attach the file object to the message.
    msg.attach(att)

    message = {
        "Source": sender,
        "Destinations": recipient,
        "Data": msg.as_string()
    }

    return message

def send_email(message):

    # Create a new SES client.
    client_ses = boto3.client("ses", os.environ["Region"])

    # Send the email.
    try:
        # Provide the contents of the email.
        response = client_ses.send_raw_email(
            Source = message["Source"],
            Destinations = [
                message["Destinations"]
            ],
            RawMessage = {
                "Data": message["Data"]
            }
        )

    # Display an error if something goes wrong.
    except ClientError as e:
        output = e.response["Error"]["Message"]
    else:
        output = f"Email sent! Message ID: {response['MessageId']}"

    return output

def lambda_handler(event, context):

    # Get the unique ID of the message. This corresponds to the name of the file in S3.
    message_id = event["Records"][0]["ses"]["mail"]["messageId"]
    print (f"Received message ID {message_id}")

    # Retrieve the file from the S3 bucket.
    file = get_message_from_s3(message_id)

    # Create the message.
    message = create_message(file)

    # Send the email and print the result.
    result = send_email(message)
    print (result)