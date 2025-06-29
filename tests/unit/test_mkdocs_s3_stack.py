import aws_cdk as core
import aws_cdk.assertions as assertions

from mkdocs_s3.mkdocs_s3_stack import MkdocsS3Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in mkdocs_s3/mkdocs_s3_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MkdocsS3Stack(app, "mkdocs-s3")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
