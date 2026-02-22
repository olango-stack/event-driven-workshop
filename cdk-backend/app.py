#!/usr/bin/env python3
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.
"""
CDK Application entry point for CNS203 E-Commerce Backend.

This script creates and configures the CDK application with proper
tagging and resource management policies.
"""
from aws_cdk import App, Tags

from cdk_backend.cdk_backend_stack import CdkBackendStack


app = App()

# Create the stack with CNS203 prefix
stack = CdkBackendStack(app, "CNS203CdkBackendStack")

# Add project tagging to all resources in the stack
Tags.of(stack).add("project", "CNS203")
Tags.of(stack).add("auto-delete", "false")
Tags.of(stack).add("auto-stop", "false")

app.synth()
