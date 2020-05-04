# Email Forwarding Using AWS

## About

The objective is to receive emails and have them forwarded on to another email address.

At a high level, mail is processed using a combination of SES, S3, and Lambda:

1. SES receives an email.
2. SES puts that email in an S3 bucket.
3. Lambda retrieves that email from the S3 bucket.
4. Lambda creates a new email message and attaches the original (received) email to it.
5. Lambda sends the new email out using SES.

## Further information

See [the wiki](https://github.com/mmattioli/aws-email-forwarding/wiki) for further information and documentation.