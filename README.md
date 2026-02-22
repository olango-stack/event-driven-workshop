# Re:Invent 2025 CNS203 - E-Commerce Backend

A serverless e-commerce backend built with AWS CDK, featuring RESTful APIs for cart management and checkout processing.

## 🏗️ Architecture Overview

This project implements a serverless e-commerce backend using:

- **AWS API Gateway REST API** - RESTful endpoints for frontend integration
- **AWS Lambda Functions** - Serverless compute for business logic (ARM64, Python 3.13)
- **Amazon DynamoDB** - NoSQL database for cart and order persistence
- **AWS Powertools** - Enhanced logging, tracing, and metrics with EMF
- **AWS CDK (Python)** - Infrastructure as Code for deployment
- **Frontend Integration** - Designed to work with any frontend framework such as React

## 🎯 Project Scope

### Frontend Responsibilities

- Generate and manage user IDs
- Handle user interface and user experience
- Make API calls to backend services
- Manage client-side state and routing

### Backend Responsibilities

- **Cart Management**: Create, update, and manage shopping carts
- **Checkout Processing**: Complete end-to-end checkout workflow
- **Customer Management**: Create and manage customer accounts
- **Order Processing**: Handle order fulfillment and tracking
- **Email Communications**: Send welcome and transaction emails

## 🚀 API Endpoints

### Cart Management

All cart endpoints use `x-user-id` header parameter for security instead of path variables:

- `POST /cart` - Create a new shopping cart
  - Headers: `x-user-id: {user_id}`
- `GET /cart` - Retrieve user's cart
  - Headers: `x-user-id: {user_id}`
- `PUT /cart` - Update cart contents
  - Headers: `x-user-id: {user_id}`
- `DELETE /cart` - Clear/delete cart
  - Headers: `x-user-id: {user_id}`

### Checkout Process

- `POST /checkout` - Process complete checkout workflow
  - Headers: `x-user-id: {user_id}`

## 🔧 Lambda Functions

### 1. Modify Cart Function (`modify_cart_function.py`)

Handles all cart-related operations:

- Create new carts for users
- Add/remove items from existing carts
- Update item quantities
- Calculate cart totals and taxes
- Validate inventory availability
- Persist cart data to DynamoDB

### 2. Checkout Function (`checkout_function.py`)

Comprehensive checkout processing including:

#### Core Checkout Workflow:

1. **Inventory Reservation** - Reserve items to prevent overselling
2. **Payment Pre-Authorization** - Secure payment processing
3. **Fulfillment Submission** - Send order to fulfillment system
4. **Order Persistence** - Save order to customer account in DynamoDB
5. **Customer Account Management** - Create account for new customers
6. **Email Notifications** - Send welcome and/or transaction emails

#### Checkout Function Responsibilities:

- Validate cart contents and pricing
- Reserve inventory for all cart items
- Process payment pre-authorization
- Create customer account (if new customer)
- Generate and save order record to DynamoDB
- Submit fulfillment request to warehouse/shipping
- Send confirmation and welcome emails
- Handle rollback on any failure

## 📁 Project Structure

```
CNS203/
├── README.md                           # This file
├── deploy.sh                          # Deployment script
├── react-frontend/                    # Frontend application (future)
└── cdk-backend/                       # AWS CDK Backend
    ├── app.py                         # CDK app entry point
    ├── cdk.json                       # CDK configuration
    ├── requirements.txt               # Python dependencies
    ├── requirements-dev.txt           # Development dependencies
    ├── .gitignore                     # Git ignore rules
    ├── cdk_backend/
    │   ├── __init__.py
    │   └── cdk_backend_stack.py       # Main CDK stack definition
    ├── lambda/
    │   ├── functions/
    │   │   ├── checkout_function/
    │   │   │   └── checkout_function.py
    │   │   └── modify_cart_function/
    │   │       └── modify_cart_function.py
    │   └── layers/
    │       └── third_party/
    │           └── requirements.txt    # Lambda layer dependencies
    └── tests/
        ├── __init__.py
        └── unit/
            ├── __init__.py
            └── test_cdk_backend_stack.py
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate permissions
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Node.js (for CDK CLI)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd CNS203
   ```

2. **Set up Python virtual environment**

   ```bash
   cd cdk-backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap
   ```

## 🚀 Deployment

### Using CDK Commands

```bash
cd cdk-backend

# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy

# Destroy resources (when needed)
cdk destroy
```

### Using Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## 🧪 Testing

```bash
cd cdk-backend

# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=cdk_backend
```

## 🔒 Security Considerations

- All API endpoints will implement proper authentication
- Payment processing follows PCI DSS compliance guidelines
- Customer data is encrypted at rest and in transit
- IAM roles follow principle of least privilege
- Input validation on all API endpoints

## 📊 Monitoring & Observability

- CloudWatch Logs for all Lambda functions
- CloudWatch Metrics for API Gateway and Lambda
- X-Ray tracing for distributed request tracking
- Custom business metrics for cart and checkout operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT-0 License - see the LICENSE file for details.

## 🆘 Support

For questions and support:

- Create an issue in the repository
- Review the AWS CDK documentation
- Check AWS Lambda best practices

---

**Status**: 🚧 In Development - Core infrastructure and Lambda functions in progress
