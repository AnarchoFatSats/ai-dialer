# ECS Service Module

This module creates the ECS service for the AI Dialer application.

## Resources
- ECS Cluster
- Task Definition
- Service
- Auto Scaling

## Usage
```hcl
module "ecs_service" {
  source = "./modules/ecs_service"
  # Add variables
}
```
