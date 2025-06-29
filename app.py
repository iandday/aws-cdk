#!/usr/bin/env python3
import os

import aws_cdk as cdk

from mkdocs_s3_cloudfront.mkdocs_s3_stack import MkdocsS3CloudfrontStack


app = cdk.App()
MkdocsS3CloudfrontStack(app, "MkdocsS3CloudfrontStack"    )

app.synth()
