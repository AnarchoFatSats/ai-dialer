# VPC Module

This module creates the VPC infrastructure for the AI Dialer application.

## Resources
- VPC with appropriate CIDR
- Subnets (public/private)
- Internet Gateway
- NAT Gateways
- Route Tables
- Security Groups

## Usage
```hcl
module "vpc" {
  source = "./modules/vpc"
  # Add variables
}
```
