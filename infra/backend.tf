#################### load balancer rules ################
resource "aws_lb_target_group" "backend" {
  name     = "${var.title}-${var.infra_version}-backend-tg"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = data.terraform_remote_state.base.outputs.vpc_main
  target_type = "ip" 

  health_check {
    path                = "/health"
    protocol            = "HTTPS"
    matcher             = "200"
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
  }

  tags = {
    Name = "${var.title}-${var.infra_version}-backend-tg"
  }
}

resource "aws_lb_listener_rule" "backend" {
  listener_arn = data.terraform_remote_state.main.outputs.aws_lb_main_listener_arn
  priority     = 50

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    host_header {
      values = [data.terraform_remote_state.base.outputs.aws_route53_record_owlspeak_name]
    }
  }

  condition {
    path_pattern {
      values = ["/api","/api/*"]
    }
  }

  tags = {
    Name = "${var.title}-${var.infra_version}-backend-listener-rule"
  }
}

resource "aws_security_group_rule" "lb_to_backend" {
  security_group_id = data.terraform_remote_state.main.outputs.aws_lb_main_sg_id
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  source_security_group_id = aws_security_group.backend.id
}

############### backend pod ################
resource "aws_security_group" "backend" {
  name        = "${var.title}-${var.infra_version}-backend-sg"
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
    Name = "${var.title}-${var.infra_version}-backend-sg"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                = "${var.title}-${var.infra_version}-backend-task"
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
          "awslogs-stream-prefix" = "ecs/backend"
        }
      },
    },
    {
      name      = "service",
      image     = "${var.image_registry}/owlspeak/backend:1.0.0",
      essential = true,
      portMappings = [
        {
          name          = "backend-8000-tcp",
          containerPort = 8000,
          hostPort      = 8000,
          protocol      = "tcp",
          appProtocol   = "http"
        }
      ],
      secrets = [   
        {
          name      = "GOOGLE_API_KEY",
          valueFrom = "${var.api_secret_arn}:GOOGLE_API_KEY::"
        }    
      ]
      environment = [
        {
          name = "ROOT_PATH"
          value = "/api"
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-create-group" = "true",
          "awslogs-group"        = "${var.title}-${var.infra_version}",
          "awslogs-region"       = var.region,
          "awslogs-stream-prefix"= "ecs/backend"
        },
      }
    }]
  )
}

resource "aws_ecs_service" "backend" {
  name            = "${var.title}-${var.infra_version}-backend-srv"
  cluster         = data.terraform_remote_state.main.outputs.aws_ecs_cluster_main_id
  task_definition = aws_ecs_task_definition.backend.family
  desired_count   = 1

  launch_type     = "FARGATE"

  network_configuration {
    subnets = data.terraform_remote_state.base.outputs.public_subnets
    assign_public_ip = true
    security_groups = [aws_security_group.backend.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "proxy"
    container_port   = 443
  }
  deployment_controller {
    type = "ECS"
  }
  tags = {
    Name = "${var.title}-${var.infra_version}-backend-srv"
  }
}