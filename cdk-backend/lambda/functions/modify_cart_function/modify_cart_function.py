# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

"""
Lambda function for managing shopping cart operations.

This module provides functionality to create, update, and manage shopping carts
for the CNS203 e-commerce application using DynamoDB as the backend storage.
"""
import json
import os
import re
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

# Initialize Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
cart_table = dynamodb.Table(os.environ['CART_TABLE_NAME'])


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal objects to float for JSON serialization"""

    def default(self, o):
        """Convert Decimal objects to float for JSON serialization."""
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def get_cors_headers():
    """Return standard CORS headers for all responses"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-user-id',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }


def validate_user_id(user_id: str) -> bool:
    """Validate user_id to prevent NoSQL injection attacks"""
    if not user_id or not isinstance(user_id, str):
        return False

    # Allow only alphanumeric characters, hyphens, and underscores
    # This prevents injection attacks while allowing valid UUIDs
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, user_id):
        return False

    # Reasonable length limits
    if len(user_id) < 1 or len(user_id) > 128:
        return False

    return True


def convert_floats_to_decimal(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], _context: LambdaContext) -> Dict[str, Any]:
    """
    Handle cart operations: CREATE, READ, UPDATE, DELETE
    Expects x-user-id header for user identification
    """

    try:
        # Extract HTTP method and user ID from headers
        http_method = event.get('httpMethod', '')
        headers = event.get('headers', {})
        user_id = headers.get('x-user-id') or headers.get('X-User-Id')

        if not user_id:
            logger.error("Missing x-user-id header")
            metrics.add_metric(name="MissingUserIdError",
                               unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-user-id',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({'error': 'x-user-id header is required'})
            }

        # Validate user_id to prevent NoSQL injection
        if not validate_user_id(user_id):
            logger.error("Invalid user_id format: %s", user_id)
            metrics.add_metric(name="InvalidUserIdError",
                               unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid user_id format'})
            }

        logger.info("Processing %s request for user: %s", http_method, user_id)

        # Route to appropriate handler based on HTTP method
        if http_method == 'POST':
            response = create_cart(user_id, event.get('body'), _context)
        elif http_method == 'GET':
            response = get_cart(user_id)
        elif http_method == 'PUT':
            response = update_cart(user_id, event.get('body'), _context)
        elif http_method == 'DELETE':
            response = delete_cart(user_id)
        else:
            logger.error("Unsupported HTTP method: %s", http_method)
            metrics.add_metric(name="UnsupportedMethodError",
                               unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }

        metrics.add_metric(name="CNS203CartOperationSuccess",
                           unit=MetricUnit.Count, value=1)
        return response

    except ClientError as client_error:
        logger.exception(
            "DynamoDB client error in cart operation: %s", str(client_error))
        metrics.add_metric(name="CartOperationError",
                           unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Database operation failed'})
        }
    except (ValueError, KeyError) as validation_error:
        logger.exception(
            "Validation error in cart operation: %s", str(validation_error))
        metrics.add_metric(name="CartValidationError",
                           unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid request data'})
        }


@tracer.capture_method
def create_cart(user_id: str, body: str, _context: LambdaContext) -> Dict[str, Any]:
    """Create a new cart for the user"""
    try:
        # Parse request body
        if body:
            cart_data = json.loads(body)
        else:
            cart_data = {'items': []}

        # Convert floats to Decimals for DynamoDB compatibility
        cart_data = convert_floats_to_decimal(cart_data)

        # Create cart item
        cart_item = {
            'user_id': user_id,
            'items': cart_data.get('items', []),
            'total_amount': Decimal('0.00'),
            'item_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # Calculate totals
        cart_item = calculate_cart_totals(cart_item)

        # Save to DynamoDB
        cart_table.put_item(Item=cart_item)

        logger.info("Created cart for user: %s", user_id)
        metrics.add_metric(name="CartCreated", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps(cart_item, cls=DecimalEncoder)
        }

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }


@tracer.capture_method
def get_cart(user_id: str) -> Dict[str, Any]:
    """Retrieve user's cart"""
    try:
        response = cart_table.get_item(Key={'user_id': user_id})

        if 'Item' not in response:
            logger.info("Cart not found for user: %s", user_id)
            metrics.add_metric(name="CartNotFound",
                               unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Cart not found'})
            }

        cart = response['Item']
        logger.info("Retrieved cart for user: %s", user_id)
        metrics.add_metric(name="CartRetrieved",
                           unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(cart, cls=DecimalEncoder)
        }

    except ClientError as get_cart_error:
        logger.error("DynamoDB error: %s", get_cart_error)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Database error'})
        }


@tracer.capture_method
def update_cart(user_id: str, body: str, _context: LambdaContext) -> Dict[str, Any]:
    """Update user's cart"""
    try:
        if not body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Request body is required'})
            }

        cart_data = json.loads(body)
        # Convert floats to Decimals for DynamoDB compatibility
        cart_data = convert_floats_to_decimal(cart_data)

        # Get existing cart
        response = cart_table.get_item(Key={'user_id': user_id})

        if 'Item' not in response:
            logger.info(
                f"Cart not found for user: {user_id}, creating new cart")
            return create_cart(user_id, body, _context)

        # Update cart
        cart_item = response['Item']
        cart_item['items'] = cart_data.get('items', cart_item['items'])
        cart_item['updated_at'] = datetime.now(timezone.utc).isoformat()

        # Recalculate totals
        cart_item = calculate_cart_totals(cart_item)

        # Save updated cart
        cart_table.put_item(Item=cart_item)

        logger.info("Updated cart for user: %s", user_id)
        metrics.add_metric(name="CartUpdated", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(cart_item, cls=DecimalEncoder)
        }

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }


@tracer.capture_method
def delete_cart(user_id: str) -> Dict[str, Any]:
    """Delete user's cart"""
    try:
        cart_table.delete_item(Key={'user_id': user_id})

        logger.info("Deleted cart for user: %s", user_id)
        metrics.add_metric(name="CartDeleted", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 204,
            'headers': get_cors_headers(),
            'body': ''
        }

    except ClientError as delete_cart_error:
        logger.error("DynamoDB error: %s", delete_cart_error)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Database error'})
        }


@tracer.capture_method
def calculate_cart_totals(cart_item: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate cart totals and item count"""
    items = cart_item.get('items', [])
    total_amount = Decimal('0.00')
    item_count = 0

    for item in items:
        quantity = item.get('quantity', 0)
        price = Decimal(str(item.get('price', 0)))
        total_amount += price * quantity
        item_count += quantity

    cart_item['total_amount'] = total_amount
    cart_item['item_count'] = item_count

    # Add metrics for cart value
    metrics.add_metric(name="CartValue", unit=MetricUnit.Count,
                       value=float(total_amount))
    metrics.add_metric(name="CartItemCount",
                       unit=MetricUnit.Count, value=item_count)

    return cart_item
