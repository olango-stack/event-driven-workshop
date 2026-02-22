import aws_cdk as core
from aws_cdk import assertions

from cdk_backend.cdk_backend_stack import CdkBackendStack


def test_stack_resources_created():
    """Test that the CDK stack creates the expected AWS resources."""
    app = core.App()
    stack = CdkBackendStack(app, "cdk-backend")
    template = assertions.Template.from_stack(stack)

    # Verify DynamoDB tables are created
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST"
    })

    # Verify Lambda functions are created
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.13"
    })

    # Verify API Gateway is created
    template.has_resource_properties("AWS::ApiGateway::RestApi", {
        "Name": "CNS203 E-Commerce API"
    })
