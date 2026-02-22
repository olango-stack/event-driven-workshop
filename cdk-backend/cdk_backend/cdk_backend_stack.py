# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.
"""
CDK Stack for CNS203 E-Commerce Backend.

This module defines the AWS infrastructure for the serverless e-commerce backend
including Lambda functions, DynamoDB tables, API Gateway, and CloudFront distribution.

The code is commented throughout with TODO for easy searching.
For exmaple: search "TODO: Lab 1.1" to find the relevant sections requiring code modifications
from the corresponding workshop content.
"""

##########################################################################################################################
#
# Python library import section
#
##########################################################################################################################

from constructs import Construct
from cdk_nag import AwsSolutionsChecks, NagSuppressions

from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    RemovalPolicy,
    Tags,
    Aspects,

    ############################################################################
    #
    # TODO: Lab 1.1 - Add EventBridge and SQS imports below this comment block
    #
    ############################################################################


)


##########################################################################################################################
#
# CDK Stack for CNS203 E-Commerce Backend Infrastructure.
#
# Creates all necessary AWS resources including Lambda functions,
# DynamoDB tables, API Gateway, S3 bucket, and CloudFront distribution.
#
##########################################################################################################################

class CdkBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Apply project-wide tags
        Tags.of(self).add("auto-stop", "false")
        Tags.of(self).add("auto-delete", "false")
        Tags.of(self).add("project", "CNS203-ecommerce")

        # Create shared LogGroup for all Lambda functions
        shared_log_group = logs.LogGroup(
            self, "CNS203SharedLogGroup",
            log_group_name="/aws/lambda/CNS203-ecommerce-functions",
            # 8 days is not available, using 7 days (ONE_WEEK)
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create S3 bucket for frontend hosting
        frontend_bucket = s3.Bucket(
            self, "CNS203FrontendBucket",
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
            public_read_access=False,  # Will use OAC instead
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            enforce_ssl=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipartUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(1)
                )
            ],
        )

        # Create Origin Access Control for CloudFront to access S3
        origin_access_control = cloudfront.S3OriginAccessControl(
            self, "CNS203OriginAccessControl",
            description="OAC for CNS203 E-Commerce Frontend",
        )

        # Create API Gateway REST API with CNS203 prefix (moved before CloudFront)
        api = apigateway.RestApi(
            self, "CNS203ECommerceApi",
            rest_api_name="CNS203 E-Commerce Backend API",
            description=("RESTful API for CNS203 e-commerce cart "
                         "and checkout operations"),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date",
                               "Authorization", "X-Api-Key", "x-user-id",
                               "X-User-Id"],  # Added capitalized version
                expose_headers=["Content-Type", "X-Amz-Date", "X-Amz-Request-Id"],
                allow_credentials=False,
                max_age=Duration.seconds(86400)  # 24 hours
            ),
            # Enable X-Ray tracing for API Gateway
            cloud_watch_role=True,
            deploy_options=apigateway.StageOptions(
                tracing_enabled=True,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
        )

        # Create CloudFront distribution with API Gateway integration
        frontend_distribution = cloudfront.Distribution(
            self,
            "CNS203FrontendDistribution",
            comment="CNS203 E-Commerce Frontend Distribution with API Integration",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    frontend_bucket,
                    origin_access_control=origin_access_control,
                ),
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            ),
            additional_behaviors={
                # API Gateway integration under /api path
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        domain_name=f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com",
                        origin_path="/prod",
                        custom_headers={
                            "X-Forwarded-Host": f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com"
                        },
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    function_associations=[
                        cloudfront.FunctionAssociation(
                            function=cloudfront.Function(
                                self,
                                "CNS203ApiPathRewriteFunction",
                                code=cloudfront.FunctionCode.from_inline(
                                    """
function handler(event) {
    var request = event.request;
    // Remove /api prefix from the URI
    request.uri = request.uri.replace(/^\/api/, '');
    // Ensure we have at least a root path
    if (!request.uri || request.uri === '') {
        request.uri = '/';
    }
    return request;
}
                                """
                                ),
                                comment="Rewrite /api/* paths to remove /api prefix for API Gateway",
                            ),
                            event_type=cloudfront.FunctionEventType.VIEWER_REQUEST,
                        )
                    ],
                ),
                "*.html": cloudfront.BehaviorOptions(
                    origin=origins.S3BucketOrigin.with_origin_access_control(
                        frontend_bucket,
                        origin_access_control=origin_access_control,
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "*.js": cloudfront.BehaviorOptions(
                    origin=origins.S3BucketOrigin.with_origin_access_control(
                        frontend_bucket,
                        origin_access_control=origin_access_control,
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "*.css": cloudfront.BehaviorOptions(
                    origin=origins.S3BucketOrigin.with_origin_access_control(
                        frontend_bucket,
                        origin_access_control=origin_access_control,
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "*.json": cloudfront.BehaviorOptions(
                    origin=origins.S3BucketOrigin.with_origin_access_control(
                        frontend_bucket,
                        origin_access_control=origin_access_control,
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "/icons/*": cloudfront.BehaviorOptions(
                    origin=origins.S3BucketOrigin.with_origin_access_control(
                        frontend_bucket,
                        origin_access_control=origin_access_control,
                    ),
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
            },
            # error_responses=[
            #     cloudfront.ErrorResponse(
            #         http_status=404,
            #         response_http_status=200,
            #         response_page_path="/index.html",
            #         ttl=Duration.seconds(0),  # Disable error caching
            #     ),
            #     cloudfront.ErrorResponse(
            #         http_status=403,
            #         response_http_status=200,
            #         response_page_path="/index.html",
            #         ttl=Duration.seconds(0),  # Disable error caching
            #     )
            # ],
            enable_ipv6=True,
            enabled=True,
        )

        ############################################################################
        #
        # TODO Lab 4.1 - Deploy React frontend build files to S3
        #
        ############################################################################

        frontend_deployment = s3deploy.BucketDeployment(
            self, "CNS203FrontendDeployment",
            sources=[s3deploy.Source.asset("../react-frontend/build")],
            destination_bucket=frontend_bucket,
            prune=True,  # Remove files not in source
            retain_on_delete=False,  # Clean up on stack deletion
        )

        ############################################################################
        #
        # Create DynamoDB tables with CNS203 prefix
        #
        ############################################################################

        # Create Cart table for storing user carts
        cart_table = dynamodb.Table(
            self, "CNS203CartTable",
            table_name="CNS203-ecommerce-carts",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Create Orders table for storing completed orders
        orders_table = dynamodb.Table(
            self, "CNS203OrdersTable",
            table_name="CNS203-ecommerce-orders",
            partition_key=dynamodb.Attribute(
                name="customer_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="order_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Create Customers table for storing customer accounts
        customers_table = dynamodb.Table(
            self, "CNS203CustomersTable",
            table_name="CNS203-ecommerce-customers",
            partition_key=dynamodb.Attribute(
                name="customer_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Create Idempotency table for Lambda function idempotency
        idempotency_table = dynamodb.Table(
            self, "CNS203IdempotencyTable",
            table_name="CNS203-idempotency-table",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expiration",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        ############################################################################
        # 
        # TODO: Lab 1.1 - Add EventBridge custom bus and SQS queues here
        # 
        ############################################################################


        # Create Lambda layer for third-party dependencies with CNS203 prefix
        powertools_layer = _lambda.LayerVersion(
            self, "CNS203PowertoolsLayer",
            code=_lambda.Code.from_asset("./lambda/layers/third_party"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_13],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            description="AWS Powertools and other third-party dependencies for CNS203",
        )

        ############################################################################
        #
        # TODO: Lab 1.2 - Add EventBridge integration role here
        #
        ############################################################################


        # Common Lambda function configuration
        lambda_environment = {
            "POWERTOOLS_SERVICE_NAME": "CNS203-ecommerce-backend",
            "POWERTOOLS_METRICS_NAMESPACE": "CNS203ECommerce",
            "POWERTOOLS_LOG_LEVEL": "INFO",
            "POWERTOOLS_LOGGER_SAMPLE_RATE": "0.1",
            "POWERTOOLS_LOGGER_LOG_EVENT": "true",
            "POWERTOOLS_METRICS_CAPTURE_COLD_START_METRIC": "true",
            # Enable X-Ray tracing in Powertools
            "POWERTOOLS_TRACER_CAPTURE_RESPONSE": "true",
            "POWERTOOLS_TRACER_CAPTURE_ERROR": "true",
            "CART_TABLE_NAME": cart_table.table_name,
            "ORDERS_TABLE_NAME": orders_table.table_name,
            "CUSTOMERS_TABLE_NAME": customers_table.table_name,
            "IDEMPOTENCY_TABLE_NAME": idempotency_table.table_name
        }

        # Modify Cart Lambda Function with CNS203 prefix
        modify_cart_function = _lambda.Function(
            self, "CNS203ModifyCartFunction",
            function_name="CNS203-modify-cart-function",
            runtime=_lambda.Runtime.PYTHON_3_13,
            architecture=_lambda.Architecture.ARM_64,
            handler="modify_cart_function.lambda_handler",
            code=_lambda.Code.from_asset(
                "./lambda/functions/modify_cart_function"),
            layers=[powertools_layer],
            environment=lambda_environment,
            timeout=Duration.seconds(30),
            memory_size=512,
            tracing=_lambda.Tracing.ACTIVE,  # Enable X-Ray tracing
            log_group=shared_log_group,
        )

        # Checkout Lambda Function with CNS203 prefix
        checkout_function = _lambda.Function(
            self, "CNS203CheckoutFunction",
            function_name="CNS203-checkout-function",
            runtime=_lambda.Runtime.PYTHON_3_13,
            architecture=_lambda.Architecture.ARM_64,
            handler="checkout_function.lambda_handler",
            code=_lambda.Code.from_asset("./lambda/functions/checkout_function"),
            layers=[powertools_layer],
            environment=lambda_environment,
            # Longer timeout for checkout process
            timeout=Duration.seconds(60),
            memory_size=1024,  # More memory for checkout processing
            tracing=_lambda.Tracing.ACTIVE,  # Enable X-Ray tracing
            log_group=shared_log_group,
        )

        ############################################################################
        #
        # TODO: Lab 3.1 - Add new Lambda functions for event-driven architecture here
        #
        ############################################################################



        ############################################################################
        #
        # TODO: Lab 1.4 - Add Checkout Status API Endpoint here
        #
        ############################################################################



        # Grant DynamoDB permissions to Lambda functions
        cart_table.grant_read_write_data(modify_cart_function)
        cart_table.grant_read_write_data(checkout_function)
        orders_table.grant_read_write_data(checkout_function)
        customers_table.grant_read_write_data(checkout_function)

        # Grant X-Ray tracing permissions to Lambda functions
        xray_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets",
                "xray:GetSamplingStatisticSummaries"
            ],
            resources=["*"]
        )

        modify_cart_function.add_to_role_policy(xray_policy)
        checkout_function.add_to_role_policy(xray_policy)

        ############################################################################
        #
        # TODO: Lab 1.3 - Replace Lambda integrations with direct EventBridge integrations
        # 
        # Be sure to replace the two definitions below this comment block with the workshop code.
        #
        ############################################################################

        # Create API Gateway integrations
        modify_cart_integration = apigateway.LambdaIntegration(
            modify_cart_function,
            request_templates={"application/json": '{"statusCode": "200"}'}
        )

        checkout_integration = apigateway.LambdaIntegration(
            checkout_function,
            request_templates={"application/json": '{"statusCode": "200"}'}
        )


        ############################################################################
        #
        # Create API resources and methods
        #
        ############################################################################

        # Cart resource
        cart_resource = api.root.add_resource("cart")
        cart_resource.add_method(
            "POST", modify_cart_integration)    # Create cart
        cart_resource.add_method("GET", modify_cart_integration)     # Get cart
        cart_resource.add_method(
            "PUT", modify_cart_integration)     # Update cart
        cart_resource.add_method(
            "DELETE", modify_cart_integration)  # Delete cart

        # Checkout resource
        checkout_resource = api.root.add_resource("checkout")
        checkout_resource.add_method(
            "POST", checkout_integration)   # Process checkout
        
        
        ############################################################################
        #
        # TODO: Lab 3.2 - Add EventBridge rules and SQS event sources here
        #
        ############################################################################


        ############################################################################
        #
        # Stack Outputs with CNS203 prefix
        #
        ############################################################################

        CfnOutput(
            self, "CNS203ApiUrl",
            value=api.url,
            description="API Gateway URL for the CNS203 E-Commerce Backend"
        )

        CfnOutput(
            self, "CNS203CartTableName",
            value=cart_table.table_name,
            description="DynamoDB Cart Table Name for CNS203"
        )

        CfnOutput(
            self, "CNS203OrdersTableName",
            value=orders_table.table_name,
            description="DynamoDB Orders Table Name for CNS203"
        )

        CfnOutput(
            self, "CNS203CustomersTableName",
            value=customers_table.table_name,
            description="DynamoDB Customers Table Name for CNS203"
        )

        CfnOutput(
            self, "CNS203ModifyCartFunctionName",
            value=modify_cart_function.function_name,
            description="Modify Cart Lambda Function Name for CNS203"
        )

        CfnOutput(
            self, "CNS203CheckoutFunctionName",
            value=checkout_function.function_name,
            description="Checkout Lambda Function Name for CNS203"
        )

        # Frontend hosting outputs
        CfnOutput(
            self, "CNS203FrontendBucketName",
            value=frontend_bucket.bucket_name,
            description="S3 Bucket Name for CNS203 Frontend Hosting"
        )

        CfnOutput(
            self, "CNS203CloudFrontDistributionId",
            value=frontend_distribution.distribution_id,
            description="CloudFront Distribution ID for CNS203 Frontend"
        )

        CfnOutput(
            self, "CNS203CloudFrontDomainName",
            value=frontend_distribution.distribution_domain_name,
            description="CloudFront Domain Name for CNS203 Frontend"
        )

        CfnOutput(
            self, "CNS203FrontendUrl",
            value=f"https://{frontend_distribution.distribution_domain_name}",
            description="Complete Frontend URL for CNS203 E-Commerce"
        )

##########################################################################################################################
#
# CDK Nag - DO NOT MODIFY ANYTHING BELOW THIS COMMENT BLOCK
#
# The following code is used to perform security checks against our CDK code definitions
# Please don't modify any of the code below this section.
#
##########################################################################################################################

        # Apply CDK Nag checks
        # Aspects.of(self).add(AwsSolutionsChecks(verbose=True))
        # Add cdk-nag suppressions for S3 bucket (demo environment)

        NagSuppressions.add_resource_suppressions(
            frontend_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "S3 access logging not required for demo environment"
                },
                {
                    "id": "AwsSolutions-S10",
                    "reason": "SSL enforcement handled by CloudFront for demo environment"
                }
            ]
        )

        # Add cdk-nag suppressions for CloudFront distribution (demo environment)
        NagSuppressions.add_resource_suppressions(
            frontend_distribution,
            [
                {
                    "id": "AwsSolutions-CFR1",
                    "reason": "Geo restrictions not required for demo environment"
                },
                {
                    "id": "AwsSolutions-CFR2",
                    "reason": "WAF integration not required for demo environment"
                },
                {
                    "id": "AwsSolutions-CFR3",
                    "reason": "CloudFront access logging not required for demo environment"
                },
                {
                    "id": "AwsSolutions-CFR4",
                    "reason": "Default CloudFront certificate acceptable for demo environment"
                }
            ]
        )

        # Add cdk-nag suppressions for S3 deployment Lambda (created automatically by CDK)
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/ServiceRole",
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "S3 deployment Lambda uses AWS managed policies, acceptable for demo environment",
                    "appliesTo": ["Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
                }
            ]
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/ServiceRole/DefaultPolicy",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "S3 deployment requires wildcard permissions for CDK assets and target bucket, acceptable for demo environment",
                    "appliesTo": [
                        "Action::s3:GetBucket*",
                        "Action::s3:GetObject*", 
                        "Action::s3:List*",
                        "Action::s3:Abort*",
                        "Action::s3:DeleteObject*",
                        "Resource::arn:<AWS::Partition>:s3:::cdk-hnb659fds-assets-<AWS::AccountId>-<AWS::Region>/*",
                        "Resource::<CNS203FrontendBucket1EF492CE.Arn>/*",
                        "Resource::*"
                    ]
                }
            ]
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C",
            [
                {
                    "id": "AwsSolutions-L1",
                    "reason": "S3 deployment Lambda uses CDK managed runtime, acceptable for demo environment"
                }
            ]
        )

        # Add cdk-nag suppressions for Lambda functions (demo environment)
        NagSuppressions.add_resource_suppressions(
            modify_cart_function.role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": ("AWS managed policy AWSLambdaBasicExecutionRole "
                               "is appropriate for Lambda functions"),
                    "appliesTo": ["Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            checkout_function.role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": ("AWS managed policy AWSLambdaBasicExecutionRole "
                               "is appropriate for Lambda functions"),
                    "appliesTo": ["Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
                }
            ]
        )

        # Add suppressions for Lambda function default policies (created automatically by CDK)
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/CNS203ModifyCartFunction/ServiceRole/DefaultPolicy",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard permissions required for CloudWatch Logs and X-Ray tracing",
                    "appliesTo": ["Resource::*"]
                }
            ]
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/CNS203CheckoutFunction/ServiceRole/DefaultPolicy",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard permissions required for CloudWatch Logs and X-Ray tracing",
                    "appliesTo": ["Resource::*"]
                }
            ]
        )

        # Add suppression for S3 bucket policy (created automatically by CDK for CloudFront OAC)
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/CNS203FrontendBucket/Policy",
            [
                {
                    "id": "AwsSolutions-S10",
                    "reason": ("SSL enforcement handled by CloudFront for demo environment, "
                               "bucket policy created automatically for OAC")
                }
            ]
        )

        # Add cdk-nag suppressions for API Gateway CloudWatch role (demo environment)
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/CNS203ECommerceApi/CloudWatchRole",
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "AWS managed policy for API Gateway CloudWatch logging is acceptable for demo environment",
                    "appliesTo": ["Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"]
                }
            ]
        )

        # Add cdk-nag suppressions for API Gateway (demo environment)
        NagSuppressions.add_resource_suppressions(
            api,
            [
                {
                    "id": "AwsSolutions-APIG2",
                    "reason": "Request validation not required for demo environment"
                }
            ]
        )

        # Add cdk-nag suppressions for API Gateway deployment stage
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/CNS203CdkBackendStack/CNS203ECommerceApi/DeploymentStage.prod",
            [
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "API Gateway access logging not required for demo environment"
                },
                {
                    "id": "AwsSolutions-APIG3",
                    "reason": "WAF integration not required for demo environment"
                },
                {
                    "id": "AwsSolutions-APIG6",
                    "reason": "CloudWatch logging not required for demo environment"
                }
            ]
        )

        # Add cdk-nag suppressions for API Gateway methods (demo environment uses header-based auth)
        for method_path in [
            "/CNS203CdkBackendStack/CNS203ECommerceApi/Default/cart/POST",
            "/CNS203CdkBackendStack/CNS203ECommerceApi/Default/cart/GET",
            "/CNS203CdkBackendStack/CNS203ECommerceApi/Default/cart/PUT",
            "/CNS203CdkBackendStack/CNS203ECommerceApi/Default/cart/DELETE",
            "/CNS203CdkBackendStack/CNS203ECommerceApi/Default/checkout/POST"
        ]:
            NagSuppressions.add_resource_suppressions_by_path(
                self,
                method_path,
                [
                    {
                        "id": "AwsSolutions-APIG4",
                        "reason": ("Demo environment uses header-based authentication "
                                   "(x-user-id) instead of formal authorization")
                    },
                    {
                        "id": "AwsSolutions-COG4",
                        "reason": "Demo environment does not use Cognito User Pools, uses header-based authentication"
                    }
                ]
            )