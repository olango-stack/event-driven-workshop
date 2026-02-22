#!/bin/bash
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

# Script to create the remaining Lambda functions for Lab 2
# This saves participants from copying and pasting large amounts of code

set -e

echo "🚀 Creating remaining Lambda functions..."

# Create directories
mkdir -p /project/cdk-backend/lambda/functions/inventory_processor
mkdir -p /project/cdk-backend/lambda/functions/payment_processor  
mkdir -p /project/cdk-backend/lambda/functions/fulfillment_processor
mkdir -p /project/cdk-backend/lambda/functions/checkout_status_function

# Create inventory_processor.py
cat > /project/cdk-backend/lambda/functions/inventory_processor/inventory_processor.py << 'EOF'
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

import json
import os
import random
import time
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.data_classes import SQSEvent

logger = Logger()
tracer = Tracer()
metrics = Metrics()

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE_NAME'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def convert_floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    sqs_event = SQSEvent(event)

    for record in sqs_event.records:
        message = json.loads(record.body)
        order_id = message['order_id']
        customer_id = message['user_id']
        cart = message['cart']

        logger.info(f"Processing inventory for order {order_id}")

        # Simulate inventory reservation delay (1-2 seconds)
        processing_time = random.uniform(1, 2)
        logger.info(f"Simulating inventory reservation for {processing_time:.2f} seconds")
        time.sleep(processing_time)

        try:
            # Simulate inventory reservation
            reservation_result = reserve_inventory(cart['items'], order_id)

            # Update order status
            update_order_status(order_id, customer_id, 'inventory_reserved', {
                'inventory_reservation': convert_floats_to_decimal(reservation_result)
            })

            # Send to payment processing
            sqs.send_message(
                QueueUrl=os.environ['PAYMENT_QUEUE_URL'],
                MessageBody=json.dumps({
                    **message,
                    'inventory_reservation': reservation_result
                }, cls=DecimalEncoder)
            )

            logger.info(f"Inventory reserved for order {order_id}")
            metrics.add_metric(name="InventoryReserved", unit="Count", value=1)

        except Exception as e:
            logger.error(f"Inventory processing failed for order {order_id}: {str(e)}")
            update_order_status(order_id, customer_id, 'failed', {'error_message': str(e)})
            raise

    return {'statusCode': 200}

@tracer.capture_method
def reserve_inventory(items: list, order_id: str) -> dict:
    """Simulate inventory reservation"""
    reserved_items = []

    for item in items:
        converted_item = convert_floats_to_decimal(item)
        reserved_items.append({
            'product_id': converted_item.get('product_id'),
            'quantity': converted_item.get('quantity'),
            'reserved': True,
            'reservation_id': f"res_{uuid4().hex[:8]}"
        })

    return {
        'order_id': order_id,
        'reserved_items': reserved_items,
        'status': 'reserved',
        'reservation_timestamp': datetime.now(timezone.utc).isoformat()
    }

def update_order_status(order_id: str,customer_id: str, status: str, additional_data: dict = None):
    """Update order status in DynamoDB"""
    update_expression = "SET #status = :status, updated_at = :updated_at"
    expression_values = {
        ':status': status,
        ':updated_at': datetime.now(timezone.utc).isoformat()
    }

    if additional_data:
        converted_data = convert_floats_to_decimal(additional_data)
        for key, value in converted_data.items():
            update_expression += f", {key} = :{key}"
            expression_values[f":{key}"] = value

    orders_table.update_item(
        Key={
            'customer_id': customer_id,
            'order_id': order_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues=expression_values
    )
EOF

# Create payment_processor.py
cat > /project/cdk-backend/lambda/functions/payment_processor/payment_processor.py << 'EOF'
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

import json
import os
import time
import random
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.data_classes import SQSEvent
from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer

logger = Logger()
tracer = Tracer()
metrics = Metrics()

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE_NAME'])
cart_table = dynamodb.Table(os.environ['CART_TABLE_NAME'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

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

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
@idempotent(persistence_store=DynamoDBPersistenceLayer(table_name=os.environ.get('IDEMPOTENCY_TABLE_NAME', 'idempotency-table')))
def lambda_handler(event, context):
    sqs_event = SQSEvent(event)

    for record in sqs_event.records:
        message = json.loads(record.body)
        order_id = message['order_id']
        user_id = message['user_id']
        cart = message['cart']
        checkout_data = message['checkout_data']
        checkout_data = convert_floats_to_decimal(checkout_data)

        logger.info(f"Processing payment for order {order_id}")

        try:
            # Simulate payment authorization
            payment_result = authorize_payment(
                checkout_data.get('payment_info', {}),
                cart['total_amount'],
                order_id
            )

            # Update order status
            update_order_status(order_id, user_id, 'payment_authorized', {
                'payment_authorization': payment_result
            })

            # Send to fulfillment
            sqs.send_message(
                QueueUrl=os.environ['FULFILLMENT_QUEUE_URL'],
                MessageBody=json.dumps({
                    **message,
                    'payment_authorization': payment_result
                }, cls=DecimalEncoder)
            )

            # Clear user's cart after successful payment
            clear_cart(user_id)

            logger.info(f"Payment authorized for order {order_id}")
            metrics.add_metric(name="PaymentAuthorized", unit="Count", value=1)

        except Exception as e:
            logger.error(f"Payment processing failed for order {order_id}: {str(e)}")
            update_order_status(order_id, user_id, 'payment_failed', {'error_message': str(e)})
            raise

    return {'statusCode': 200}

@tracer.capture_method
def authorize_payment(payment_info: dict, amount: Decimal, order_id: str) -> dict:
    """Simulate payment authorization"""
    # Simulate payment processing delay (1-3 seconds)
    processing_time = random.uniform(1, 3)
    logger.info(f"Simulating payment processing for {processing_time:.2f} seconds")
    time.sleep(processing_time)
    
    return {
        'order_id': order_id,
        'amount': amount,
        'authorization_id': f"auth_{uuid4().hex[:10]}",
        'status': 'authorized',
        'payment_method': payment_info.get('method', 'credit_card'),
        'authorization_timestamp': datetime.now(timezone.utc).isoformat()
    }

def clear_cart(user_id: str):
    """Clear user's cart after successful payment"""
    try:
        cart_table.delete_item(Key={'user_id': user_id})
        logger.info(f"Cart cleared for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to clear cart for user {user_id}: {str(e)}")

def update_order_status(order_id: str, user_id: str, status: str, additional_data: dict = None):
    """Update order status in DynamoDB"""
    update_expression = "SET #status = :status, updated_at = :updated_at"
    expression_values = {
        ':status': status,
        ':updated_at': datetime.now(timezone.utc).isoformat()
    }

    if additional_data:
        converted_data = convert_floats_to_decimal(additional_data)
        for key, value in converted_data.items():
            update_expression += f", {key} = :{key}"
            expression_values[f":{key}"] = value

    orders_table.update_item(
        Key={
            'customer_id': user_id,
            'order_id': order_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues=expression_values
    )
EOF

# Create fulfillment_processor.py
cat > /project/cdk-backend/lambda/functions/fulfillment_processor/fulfillment_processor.py << 'EOF'
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

import json
import os
import time
import random
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.data_classes import SQSEvent
from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE_NAME'])

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

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
@idempotent(persistence_store=DynamoDBPersistenceLayer(table_name=os.environ.get('IDEMPOTENCY_TABLE_NAME', 'idempotency-table')))
def lambda_handler(event, context):
    sqs_event = SQSEvent(event)

    for record in sqs_event.records:
        message = json.loads(record.body)
        order_id = message['order_id']
        user_id = message['user_id']

        logger.info(f"Processing fulfillment for order {order_id}")

        try:
            # Simulate fulfillment processing
            fulfillment_result = process_fulfillment(order_id, message)

            # Update order status to completed
            update_order_status(order_id, user_id, 'completed', {
                'fulfillment_info': convert_floats_to_decimal(fulfillment_result)
            })

            logger.info(f"Fulfillment completed for order {order_id}")
            metrics.add_metric(name="FulfillmentCompleted", unit="Count", value=1)

        except Exception as e:
            logger.error(f"Fulfillment processing failed for order {order_id}: {str(e)}")
            update_order_status(order_id, user_id, 'failed', {'error_message': str(e)})
            raise

    return {'statusCode': 200}

@tracer.capture_method
def process_fulfillment(order_id: str, order_data: dict) -> dict:
    """Simulate fulfillment processing"""
    # Simulate fulfillment processing (1-2 seconds)
    processing_time = random.uniform(1, 2)
    logger.info(f"Simulating fulfillment processing for {processing_time:.2f} seconds")
    time.sleep(processing_time)
    return {
        'order_id': order_id,
        'tracking_number': f"TRK{uuid4().hex[:10].upper()}",
        'estimated_delivery': '3-5 business days',
        'status': 'shipped',
        'fulfillment_timestamp': datetime.now(timezone.utc).isoformat()
    }

def update_order_status(order_id: str, user_id: str, status: str, additional_data: dict = None):
    """Update order status in DynamoDB"""
    update_expression = "SET #status = :status, updated_at = :updated_at"
    expression_values = {
        ':status': status,
        ':updated_at': datetime.now(timezone.utc).isoformat()
    }

    if additional_data:
        converted_data = convert_floats_to_decimal(additional_data)
        for key, value in converted_data.items():
            update_expression += f", {key} = :{key}"
            expression_values[f":{key}"] = value

    orders_table.update_item(
        Key={
            'customer_id': user_id,
            'order_id': order_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues=expression_values
    )
EOF

# Create checkout_status_function.py
cat > /project/cdk-backend/lambda/functions/checkout_status_function/checkout_status_function.py << 'EOF'
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

import json
import os
from typing import Dict, Any
from decimal import Decimal

from boto3 import resource
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

# Initialize Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize AWS clients
dynamodb = resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE_NAME'])

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal objects to float for JSON serialization"""
    def default(self, o):
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

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Get checkout status by request ID"""
    try:
        # Extract request ID from path parameters
        path_parameters = event.get('pathParameters', {})
        request_id = path_parameters.get('requestId')

        if not request_id:
            logger.error("Missing requestId in path parameters")
            metrics.add_metric(name="MissingRequestIdError", unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'requestId is required'})
            }

        logger.info("Getting checkout status for request: %s", request_id)

        # Get order status by request ID
        order_status = get_order_status_by_request_id(request_id)

        if not order_status:
            logger.warning("Order not found for request ID: %s", request_id)
            metrics.add_metric(name="OrderNotFound", unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Order not found'})
            }

        metrics.add_metric(name="CheckoutStatusSuccess", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(order_status, cls=DecimalEncoder)
        }

    except Exception as error:
        logger.exception("Unexpected error in checkout status")
        metrics.add_metric(name="CheckoutStatusError", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }

@tracer.capture_method
def get_order_status_by_request_id(request_id: str) -> Dict[str, Any]:
    """Get order status by request ID from DynamoDB"""
    try:
        # Scan the orders table to find order with matching request_id
        response = orders_table.scan(
            FilterExpression="request_id = :request_id",
            ExpressionAttributeValues={':request_id': request_id}
        )

        items = response.get('Items', [])
        if not items:
            return None

        order = items[0]  # Take the first matching order
        
        # Map order status to frontend-expected format
        status_mapping = {
            'processing': 'processing',
            'inventory_reserved': 'processing', 
            'payment_authorized': 'processing',
            'completed': 'completed',
            'failed': 'failed',
            'payment_failed': 'failed'
        }

        # Calculate progress based on status
        progress_mapping = {
            'processing': 25,
            'inventory_reserved': 50,
            'payment_authorized': 75,
            'completed': 100,
            'failed': 0,
            'payment_failed': 0
        }

        current_status = order.get('status', 'processing')
        mapped_status = status_mapping.get(current_status, 'processing')
        progress = progress_mapping.get(current_status, 25)

        result = {
            'status': mapped_status,
            'progress': progress,
            'orderId': order.get('order_id'),
            'requestId': request_id,
            'created_at': order.get('created_at'),
            'updated_at': order.get('updated_at')
        }

        # Add error message if failed
        if mapped_status == 'failed' and 'error_message' in order:
            result['error_message'] = order['error_message']

        logger.info("Order status retrieved for request %s: %s", request_id, mapped_status)
        return result

    except ClientError as db_error:
        logger.error("Failed to get order status for request %s: %s", request_id, db_error)
        raise
EOF

echo "✅ All remaining Lambda functions created successfully!"
echo ""
echo "Created functions:"
echo "  📦 inventory_processor"
echo "  💳 payment_processor" 
echo "  🚚 fulfillment_processor"
echo "  📊 checkout_status_function"
echo ""
echo "Ready for Lab 3 deployment! 🚀"