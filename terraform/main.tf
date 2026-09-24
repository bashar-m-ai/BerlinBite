terraform {

  required_version = ">= 1.6"
  required_providers {

    aws    = { source = "hashicorp/aws", version = "~> 6.0" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}
provider "aws" {
  region = var.region
}
provider "aws" {

  alias  = "global"
  region = "us-east-1"
}
# The frontend travels with the API: one image, one origin, no CORS configuration.
data "aws_availability_zones" "available" {
  state = "available"
}
resource "aws_vpc" "app" {

  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "berlinbite" }
}
resource "aws_internet_gateway" "app" {
  vpc_id = aws_vpc.app.id
}
resource "aws_subnet" "public" {

  count             = 2
  vpc_id            = aws_vpc.app.id
  cidr_block        = cidrsubnet(aws_vpc.app.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}
resource "aws_route_table" "public" {

  vpc_id = aws_vpc.app.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app.id
  }
}
resource "aws_route_table_association" "public" {

  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}
resource "aws_security_group" "alb" {

  name_prefix = "berlinbite-alb-"
  vpc_id      = aws_vpc.app.id
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.cloudfront.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "task" {

  name_prefix = "berlinbite-task-"
  vpc_id      = aws_vpc.app.id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_ecr_repository" "app" {

  name                 = "berlinbite"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  force_delete = false
}
# Store secret values with the separate interactive setup script, never Terraform variables.
resource "aws_secretsmanager_secret" "google" {
  name = "berlinbite/google-places"
}
resource "aws_secretsmanager_secret" "openai" {
  name = "berlinbite/openai"
}
resource "aws_cloudwatch_log_group" "app" {

  name              = "/ecs/berlinbite"
  retention_in_days = 7
}
resource "aws_iam_role" "execution" {

  name               = "berlinbite-execution"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy_attachment" "execution" {

  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "secrets" {

  role   = aws_iam_role.execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [aws_secretsmanager_secret.google.arn, aws_secretsmanager_secret.openai.arn] }] })
}
resource "aws_ecs_cluster" "app" {
  name = "berlinbite"
}
resource "aws_ecs_task_definition" "app" {

  count                    = var.deploy_app ? 1 : 0
  family                   = "berlinbite"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  container_definitions = jsonencode([{ name = "app", image = "${aws_ecr_repository.app.repository_url}:${var.image_tag}", essential = true,
    portMappings     = [{ containerPort = 8000, protocol = "tcp" }],
    environment      = [{ name = "OPENAI_MODEL", value = var.openai_model }, { name = "MAX_REQUESTS_PER_MINUTE", value = "300" }],
    secrets          = [{ name = "GOOGLE_PLACES_API_KEY", valueFrom = aws_secretsmanager_secret.google.arn }, { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai.arn }],
    logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = var.region, awslogs-stream-prefix = "app" } },
    healthCheck      = { command = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2)\""], interval = 30, timeout = 5, retries = 3, startPeriod = 20 }
  }])
}
resource "aws_lb" "app" {

  name               = "berlinbite"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}
resource "aws_lb_target_group" "app" {

  name        = "berlinbite"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.app.id
  health_check {
    path = "/api/health"
  }
}
resource "random_password" "origin" {

  length  = 40
  special = false
}
resource "aws_lb_listener" "app" {

  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Forbidden"
      status_code  = "403"
    }
  }
}
resource "aws_lb_listener_rule" "origin" {

  listener_arn = aws_lb_listener.app.arn
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  condition {
    http_header {
      http_header_name = "X-Origin-Verify"
      values           = [random_password.origin.result]
    }
  }
}
resource "aws_ecs_service" "app" {

  count                             = var.deploy_app ? 1 : 0
  name                              = "berlinbite"
  cluster                           = aws_ecs_cluster.app.id
  task_definition                   = aws_ecs_task_definition.app[0].arn
  desired_count                     = var.min_tasks
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 60
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {

    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.task.id]
    assign_public_ip = true
  }
  load_balancer {

    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener_rule.origin, aws_iam_role_policy.secrets, aws_iam_role_policy_attachment.execution]
  lifecycle {
    ignore_changes = [desired_count]
  }
}
resource "aws_appautoscaling_target" "app" {

  count              = var.deploy_app ? 1 : 0
  max_capacity       = 4
  min_capacity       = var.min_tasks
  resource_id        = "service/${aws_ecs_cluster.app.name}/${aws_ecs_service.app[0].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
resource "aws_appautoscaling_policy" "cpu" {

  count              = var.deploy_app ? 1 : 0
  name               = "berlinbite-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app[0].resource_id
  scalable_dimension = aws_appautoscaling_target.app[0].scalable_dimension
  service_namespace  = "ecs"
  target_tracking_scaling_policy_configuration {

    target_value = 60
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
resource "aws_wafv2_web_acl" "app" {

  provider = aws.global
  name     = "berlinbite"
  scope    = "CLOUDFRONT"
  default_action {
    allow {

    }
  }
  rule {

    name     = "request-limit"
    priority = 1
    action {
      block {

      }
    }
    statement {
      rate_based_statement {
        limit              = 100
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "berlinbite-rate"
      sampled_requests_enabled   = false
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "berlinbite-waf"
    sampled_requests_enabled   = false
  }
}
resource "aws_cloudfront_distribution" "app" {

  enabled    = true
  comment    = "BerlinBite HTTPS entry point"
  web_acl_id = aws_wafv2_web_acl.app.arn
  origin {

    domain_name = aws_lb.app.dns_name
    origin_id   = "app"
    custom_header {
      name  = "X-Origin-Verify"
      value = random_password.origin.result
    }
    custom_origin_config {

      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {

    target_origin_id         = "app"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"
    compress                 = true
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
resource "aws_cloudwatch_metric_alarm" "errors" {

  alarm_name          = "berlinbite-target-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  dimensions          = { LoadBalancer = aws_lb.app.arn_suffix }
  treat_missing_data  = "notBreaching"
}
