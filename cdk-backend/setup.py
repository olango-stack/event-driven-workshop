# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

import setuptools

setuptools.setup(
    name="cdk-backend",
    version="0.0.1",
    description="CNS203 Event-Driven E-Commerce Backend",
    author="Amazon Web Services",
    license="MIT-0",
    packages=setuptools.find_packages(),
    install_requires=[
        "aws-cdk-lib>=2.210.0",
        "constructs>=10.0.0,<11.0.0",
        "cdk-nag>=2.36.57",
        "boto3>=1.40.5",
        "aws-lambda-powertools[all]>=3.18.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)