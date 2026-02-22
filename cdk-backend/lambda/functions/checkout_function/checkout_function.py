# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

"""Checkout function for CNS203 e-commerce backend."""
import json
import os
from re import match
from uuid import uuid4
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime, timezone

from time import sleep
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
cart_table = dynamodb.Table(os.environ['CART_TABLE_NAME'])
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE_NAME'])
customers_table = dynamodb.Table(os.environ['CUSTOMERS_TABLE_NAME'])


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


def validate_user_id(user_id: str) -> bool:
    """Validate user_id to prevent NoSQL injection attacks"""
    if not user_id or not isinstance(user_id, str):
        return False

    # Allow only alphanumeric characters, hyphens, and underscores
    # This prevents injection attacks while allowing valid UUIDs
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not match(pattern, user_id):
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
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Process complete checkout workflow:
    1. Reserve inventory
    2. Pre-authorize payment
    3. Submit fulfillment
    4. Save order to customer account
    5. Create customer account if new
    6. Send welcome/transaction emails
    """

    try:
        # Extract user ID from headers
        headers = event.get('headers', {})
        user_id = headers.get('x-user-id') or headers.get('X-User-Id')

        if not user_id:
            logger.error("Missing x-user-id header")
            metrics.add_metric(name="MissingUserIdError",
                               unit=MetricUnit.Count, value=1)
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
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

        # Parse checkout data
        if not event.get('body'):
            logger.error("Missing request body")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Request body is required'})
            }

        checkout_data = json.loads(event['body'])
        # Convert floats to Decimals for DynamoDB compatibility
        checkout_data = convert_floats_to_decimal(checkout_data)
        logger.info("Processing checkout for user: %s", user_id)

        # Execute checkout workflow
        checkout_result = process_checkout(user_id, checkout_data, context)
        # Add Sleep for 5 second to mimic a distributed system
        sleep(5)

        metrics.add_metric(name="CNS203CheckoutSuccess",
                           unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(checkout_result, cls=DecimalEncoder)
        }

    except (json.JSONDecodeError, KeyError, ValueError) as validation_error:
        logger.error("Request validation error: %s", str(validation_error))
        metrics.add_metric(name="ValidationError",
                           unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid request format'})
        }
    except (ClientError, RuntimeError):
        logger.exception("Unexpected error in checkout process")
        metrics.add_metric(name="CheckoutError",
                           unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }


@tracer.capture_method
def process_checkout(user_id: str, checkout_data: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Execute the complete checkout workflow"""

    # Generate order ID
    order_id = str(uuid4())
    logger.info("Starting checkout process for order: %s", order_id)

    try:
        # Step 1: Get and validate cart
        cart = get_user_cart(user_id)
        if not cart or not cart.get('items'):
            raise ValueError("Cart is empty or not found")

        # Step 2: Reserve inventory
        inventory_reservation = reserve_inventory(cart['items'], order_id)
        logger.info("Inventory reserved for order: %s", order_id)

        # Step 3: Pre-authorize payment
        payment_auth = pre_authorize_payment(
            checkout_data.get('payment_info', {}),
            cart['total_amount'],
            order_id
        )
        logger.info("Payment pre-authorized for order: %s", order_id)

        # Step 4: Create/update customer account
        customer_info = checkout_data.get('customer_info', {})
        customer_id = create_or_update_customer(user_id, customer_info)
        logger.info("Customer account processed: %s", customer_id)

        # Step 5: Create order record
        # Add reservation and payment data to checkout_data for order record
        checkout_data['inventory_reservation'] = inventory_reservation
        checkout_data['payment_auth'] = payment_auth

        order_record = create_order_record(
            order_id=order_id,
            customer_id=customer_id,
            cart=cart,
            checkout_data=checkout_data,
            context=context
        )
        logger.info("Order record created: %s", order_id)

        # Step 6: Submit to fulfillment system
        fulfillment_result = submit_fulfillment(order_record)
        logger.info("Fulfillment submitted for order: %s", order_id)

        # Step 7: Send emails
        email_result = send_checkout_emails(customer_info, order_record)
        logger.info("Emails sent for order: %s", order_id)

        # Step 8: Clear cart after successful checkout
        clear_user_cart(user_id)
        logger.info("Cart cleared for user: %s", user_id)

        # Record metrics
        metrics.add_metric(name="OrderValue", unit=MetricUnit.Count,
                           value=float(cart['total_amount']))
        metrics.add_metric(name="OrderItemCount",
                           unit=MetricUnit.Count, value=cart['item_count'])

        return {
            'order_id': order_id,
            'customer_id': customer_id,
            'status': 'completed',
            'total_amount': cart['total_amount'],
            'fulfillment_tracking': str(fulfillment_result.get('tracking_number', '')) if fulfillment_result.get('tracking_number') else None,
            'email_sent': email_result.get('success', False)
        }

    except (ClientError, ValueError, KeyError) as checkout_error:
        logger.error("Checkout failed for order %s: %s",
                     order_id, str(checkout_error))
        # Rollback operations
        rollback_checkout(order_id, locals())
        raise


@tracer.capture_method
def get_user_cart(user_id: str) -> Dict[str, Any]:
    """Retrieve user's cart from DynamoDB"""
    try:
        response = cart_table.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except ClientError as db_error:
        logger.error("Failed to get cart for user %s: %s", user_id, db_error)
        raise


@tracer.capture_method
def reserve_inventory(items: list, order_id: str) -> Dict[str, Any]:
    """Reserve inventory for cart items"""
    # This would integrate with your inventory management system
    # For now, we'll simulate the reservation
    logger.info("Reserving inventory for %d items", len(items))

    reserved_items = []
    for item in items:
        # Simulate inventory check and reservation
        reserved_items.append({
            'product_id': item.get('product_id'),
            'quantity': item.get('quantity'),
            'reserved': True,
            'reservation_id': "res_" + str(uuid4())
        })

    metrics.add_metric(name="InventoryReserved",
                       unit=MetricUnit.Count, value=len(reserved_items))
    return {
        'order_id': order_id,
        'reserved_items': reserved_items,
        'status': 'reserved'
    }


@tracer.capture_method
def pre_authorize_payment(payment_info: Dict[str, Any], amount: Decimal, order_id: str) -> Dict[str, Any]:
    """Pre-authorize payment for the order"""
    # This would integrate with your payment processor
    # For now, we'll simulate the pre-authorization
    logger.info("Pre-authorizing payment of $%s for order %s",
                amount, order_id)

    # Simulate payment processing
    auth_result = {
        'order_id': order_id,
        'amount': amount,
        'authorization_id': f"auth_{uuid4()}",
        'status': 'authorized',
        'payment_method': payment_info.get('method', 'credit_card')
    }

    metrics.add_metric(name="PaymentAuthorized",
                       unit=MetricUnit.Count, value=1)
    return auth_result


@tracer.capture_method
def create_or_update_customer(user_id: str, customer_info: Dict[str, Any]) -> str:
    """Create new customer account or update existing one"""
    customer_id = customer_info.get('customer_id', user_id)

    try:
        # Check if customer exists
        response = customers_table.get_item(Key={'customer_id': customer_id})
        is_new_customer = 'Item' not in response

        # Prepare customer record
        customer_record = {
            'customer_id': customer_id,
            'email': customer_info.get('email'),
            'first_name': customer_info.get('first_name'),
            'last_name': customer_info.get('last_name'),
            'phone': customer_info.get('phone'),
            'shipping_address': customer_info.get('shipping_address', {}),
            'billing_address': customer_info.get('billing_address', {}),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        if is_new_customer:
            customer_record['created_at'] = datetime.now(
                timezone.utc).isoformat()
            metrics.add_metric(name="NewCustomerCreated",
                               unit=MetricUnit.Count, value=1)
            logger.info("Creating new customer: %s", customer_id)
        else:
            logger.info("Updating existing customer: %s", customer_id)

        # Save customer record
        customers_table.put_item(Item=customer_record)

        return customer_id

    except ClientError as customer_error:
        logger.error("Failed to create/update customer %s: %s",
                     customer_id, customer_error)
        raise


@tracer.capture_method
def create_order_record(order_id: str, customer_id: str, cart: Dict[str, Any],
                        checkout_data: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Create order record in DynamoDB"""

    # Extract nested data from checkout_data
    inventory_reservation = checkout_data.get('inventory_reservation', {})
    payment_auth = checkout_data.get('payment_auth', {})

    # Get addresses from either top-level or nested in customer_info
    shipping_address = (
        checkout_data.get('shipping_address') or 
        checkout_data.get('customer_info', {}).get('shipping_address', {})
    )
    billing_address = (
        checkout_data.get('billing_address') or 
        checkout_data.get('customer_info', {}).get('billing_address', {})
    )

    order_record = {
        'customer_id': customer_id,
        'order_id': order_id,
        'items': cart['items'],
        'total_amount': cart['total_amount'],
        'item_count': cart['item_count'],
        'status': 'processing',
        'shipping_address': shipping_address,
        'billing_address': billing_address,
        'inventory_reservation': inventory_reservation,
        'payment_authorization': payment_auth,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'request_id': context.aws_request_id
    }

    try:
        orders_table.put_item(Item=order_record)
        logger.info("Order record created: %s", order_id)
        return order_record
    except ClientError as order_error:
        logger.error("Failed to create order record %s: %s",
                     order_id, order_error)
        raise


@tracer.capture_method
def submit_fulfillment(order_record: Dict[str, Any]) -> Dict[str, Any]:
    """Submit order to fulfillment system"""
    # This would integrate with your fulfillment/shipping system
    # For now, we'll simulate the submission
    logger.info("Submitting order %s to fulfillment", order_record['order_id'])

    fulfillment_result = {
        'order_id': order_record['order_id'],
        'tracking_number': f"TRK{uuid4().hex[:10].upper()}",
        'estimated_delivery': '3-5 business days',
        'status': 'submitted'
    }

    metrics.add_metric(name="FulfillmentSubmitted",
                       unit=MetricUnit.Count, value=1)
    return fulfillment_result


@tracer.capture_method
def send_checkout_emails(customer_info: Dict[str, Any], order_record: Dict[str, Any]) -> Dict[str, Any]:
    """Send welcome and/or transaction emails"""
    # This would integrate with your email service (SES, etc.)
    # For now, we'll simulate sending emails

    email = customer_info.get('email')
    if not email:
        logger.warning("No email address provided for customer")
        return {'success': False, 'reason': 'No email address'}

    logger.info("Sending checkout emails to %s", email)

    # Simulate email sending
    email_result = {
        'success': True,
        'transaction_email_sent': True,
        'welcome_email_sent': customer_info.get('is_new_customer', False),
        'email_address': email
    }

    metrics.add_metric(name="EmailsSent", unit=MetricUnit.Count, value=1)
    return email_result


@tracer.capture_method
def clear_user_cart(user_id: str) -> None:
    """Clear user's cart after successful checkout"""
    try:
        cart_table.delete_item(Key={'user_id': user_id})
        logger.info("Cart cleared for user: %s", user_id)
    except ClientError as clear_error:
        logger.error("Failed to clear cart for user %s: %s",
                     user_id, clear_error)
        # Don't raise exception as this is not critical for checkout success


@tracer.capture_method
def rollback_checkout(order_id: str, checkout_state: Dict[str, Any]) -> None:
    """Rollback checkout operations in case of failure"""
    logger.error("Rolling back checkout for order: %s", order_id)

    # Rollback inventory reservation
    if 'inventory_reservation' in checkout_state:
        logger.info(
            f"Rolling back inventory reservation for order: {order_id}")
        # Implement inventory rollback logic

    # Rollback payment authorization
    if 'payment_auth' in checkout_state:
        logger.info(
            f"Rolling back payment authorization for order: {order_id}")
        # Implement payment rollback logic

    metrics.add_metric(name="CheckoutRollback", unit=MetricUnit.Count, value=1)
