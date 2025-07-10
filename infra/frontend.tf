#################### load balancer rules ################
resource "aws_lb_target_group" "frontend" {
  name     = "${var.title}-${var.infra_version}-frontend-tg"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = data.terraform_remote_state.base.outputs.vpc_main
  target_type = "ip" 

  # health_check {
  #   path                = "/health"
  #   protocol            = "HTTPS"
  #   matcher             = "200"
  #   enabled             = true
  #   healthy_threshold   = 2
  #   unhealthy_threshold = 2
  #   timeout             = 5
  #   interval            = 30
  # }

  tags = {
    Name = "${var.title}-${var.infra_version}-frontend-tg"
  }
}

resource "aws_lb_listener_rule" "frontend" {
  listener_arn = data.terraform_remote_state.main.outputs.aws_lb_main_listener_arn
  priority     = 950

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  condition {
    host_header {
      values = [data.terraform_remote_state.base.outputs.aws_route53_record_owlspeak_name]
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  tags = {
    Name = "${var.title}-${var.infra_version}-frontend-listener-rule"
  }
}

resource "aws_security_group_rule" "lb_to_frontend" {
  security_group_id = data.terraform_remote_state.main.outputs.aws_lb_main_sg_id
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  source_security_group_id = aws_security_group.frontend.id
}

############### frontend pod ################
resource "aws_security_group" "frontend" {
  name        = "${var.title}-${var.infra_version}-frontend-sg"
  description = "Backend pod security group"
  vpc_id      = data.terraform_remote_state.base.outputs.vpc_main

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    # from_port   = 80
    # to_port     = 80
    protocol    = "tcp"
    security_groups = [data.terraform_remote_state.main.outputs.aws_lb_main_sg_id]
  }

  tags = {
    Name = "${var.title}-${var.infra_version}-frontend-sg"
  }
}

resource "aws_ecs_task_definition" "frontend" {
  family                = "${var.title}-${var.infra_version}-frontend-task"
  network_mode          = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn    = data.terraform_remote_state.base.outputs.ecs_execution_role_arn
  # task_role_arn         = var.ecs_role
  cpu                   = "512"
  memory                = "2048"

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      ### proxy sidecar
      name      = "proxy",
      image     = "${var.image_registry}/portfolio/proxy:1.1.0",
      essential = true,
      secrets = [
        {
          name      = "FULLCHAIN",
          valueFrom = "${var.secret_arn}:FULLCHAIN::"
        },
        {
          name      = "PRIVKEY",
          valueFrom = "${var.secret_arn}:PRIVKEY::"
        }
      ],
      portMappings = [
        {
          name          = "nginx-443-tcp",
          containerPort = 443,
          hostPort      = 443,
          protocol      = "tcp",
          appProtocol   = "http2"
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-create-group" = "true",
          "awslogs-group" = "${var.title}-${var.infra_version}",
          "awslogs-region" = var.region,        
          "awslogs-stream-prefix" = "ecs/frontend"
        }
      },
    },
    {
      name      = "service",
      image     = "${var.image_registry}/owlspeak/frontend:1.0.0",
      essential = true,
      portMappings = [
        {
          name          = "frontend-8000-tcp",
          containerPort = 8000,
          hostPort      = 8000,
          protocol      = "tcp",
          appProtocol   = "http"
        }
      ],
      environment = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-create-group" = "true",
          "awslogs-group"        = "${var.title}-${var.infra_version}",
          "awslogs-region"       = var.region,
          "awslogs-stream-prefix"= "ecs/frontend"
        },
      }
    }]
  )
}

resource "aws_ecs_service" "frontend" {
  name            = "${var.title}-${var.infra_version}-frontend-srv"
  cluster         = data.terraform_remote_state.main.outputs.aws_ecs_cluster_main_id
  task_definition = aws_ecs_task_definition.frontend.family
  desired_count   = 1

  launch_type     = "FARGATE"

  network_configuration {
    subnets = data.terraform_remote_state.base.outputs.public_subnets
    assign_public_ip = true
    security_groups = [aws_security_group.frontend.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "proxy"
    container_port   = 443
  }
  deployment_controller {
    type = "ECS"
  }
  tags = {
    Name = "${var.title}-${var.infra_version}-frontend-srv"
  }
}