# Application Load Balancer Module

This module creates the ALB for the AI Dialer application.

## Resources
- Application Load Balancer
- Target Groups
- Listeners (HTTP/HTTPS)
- SSL Certificates

## Usage
```hcl
module "alb" {
  source = "./modules/alb"
  # Add variables
}
```
