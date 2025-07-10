# #################### load balancer rules ################
# resource "aws_lb_target_group" "core" {
#   name     = "${var.title}-${var.infra_version}-core-api-tg"
#   port     = 443
#   protocol = "HTTPS"
#   vpc_id   = data.terraform_remote_state.base.outputs.vpc_main
#   target_type = "ip" 

#   health_check {
#     path                = "/health"
#     protocol            = "HTTPS"
#     matcher             = "200"
#     enabled             = true
#     healthy_threshold   = 2
#     unhealthy_threshold = 2
#     timeout             = 5
#     interval            = 30
#   }

#   tags = {
#     Name = "${var.title}-${var.infra_version}-core-api-tg"
#   }
# }

# resource "aws_lb_listener_rule" "core" {
#   listener_arn = aws_lb_listener.main.arn
#   priority     = 100

#   action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.core.arn
#   }

#   condition {
#     path_pattern {
#       values = ["/api","/api/*"]
#     }
#   }

#   tags = {
#     Name = "${var.title}-${var.infra_version}-core-api-listener-rule"
#   }
# }

# resource "aws_security_group_rule" "lb_to_core" {
#   security_group_id = aws_security_group.lb_main.id
#   type              = "egress"
#   from_port         = 443
#   to_port           = 443
#   protocol          = "tcp"
#   source_security_group_id = aws_security_group.core.id
# }

# ############### core api pod ################
# resource "aws_security_group" "core" {
#   name        = "${var.title}-${var.infra_version}-core-api-sg"
#   description = "Core pod security group"
#   vpc_id      = data.terraform_remote_state.base.outputs.vpc_main

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   ingress {
#     from_port   = 443
#     to_port     = 443
#     # from_port   = 80
#     # to_port     = 80
#     protocol    = "tcp"
#     security_groups = [aws_security_group.lb_main.id]
#   }

#   tags = {
#     Name = "${var.title}-${var.infra_version}-core-api-sg"
#   }
# }

# resource "aws_ecs_task_definition" "core_api" {
#   family                = "${var.title}-${var.infra_version}-core-api-task"
#   network_mode          = "awsvpc"
#   requires_compatibilities = ["FARGATE"]
#   execution_role_arn    = data.terraform_remote_state.base.outputs.ecs_execution_role_arn
#   # task_role_arn         = var.ecs_role
#   cpu                   = "512"
#   memory                = "2048"

#   runtime_platform {
#     operating_system_family = "LINUX"
#     cpu_architecture        = "ARM64"
#   }

#   container_definitions = jsonencode([
#     {
#       ### proxy sidecar
#       name      = "proxy",
#       image     = "363560690820.dkr.ecr.us-west-2.amazonaws.com/portfolio/proxy:1.0.0",
#       essential = true,
#       secrets = [
#         {
#           name      = "FULLCHAIN",
#           valueFrom = "${var.secret_arn}:FULLCHAIN::"
#         },
#         {
#           name      = "PRIVKEY",
#           valueFrom = "${var.secret_arn}:PRIVKEY::"
#         }
#       ],
#       portMappings = [
#         {
#           name          = "nginx-443-tcp",
#           containerPort = 443,
#           hostPort      = 443,
#           protocol      = "tcp",
#           appProtocol   = "http2"
#         }
#       ],
#       logConfiguration = {
#         logDriver = "awslogs",
#         options = {
#           "awslogs-create-group" = "true",
#           "awslogs-group" = "${var.title}-${var.infra_version}",
#           "awslogs-region" = var.region,        
#           "awslogs-stream-prefix" = "ecs/core"
#         }
#       },
#     },
#     {
#       name      = "service",
#       image     = "363560690820.dkr.ecr.us-west-2.amazonaws.com/portfolio/core:1.2.2",
#       essential = true,
#       portMappings = [
#         {
#           name          = "core-api-8000-tcp",
#           containerPort = 8000,
#           hostPort      = 8000,
#           protocol      = "tcp",
#           appProtocol   = "http"
#         }
#       ],
#       secrets = [
#         {
#           name      = "PAYMENT_API_KEY",
#           valueFrom = "${var.api_secret_arn}:PAYMENT_API_KEY::"
#         },       
#         {
#           name      = "PAYMENT_ENDPOINT_SECRET",
#           valueFrom = "${var.api_secret_arn}:PAYMENT_ENDPOINT_SECRET::"
#         },     
#         {
#           name      = "DB_PASSWORD",
#           valueFrom = "${var.api_secret_arn}:DB_PASSWORD::"
#         },     
#         {
#           name      = "BACKEND_CLIENT_ID",
#           valueFrom = "${var.api_secret_arn}:BACKEND_CLIENT_ID::"
#         },     
#         {
#           name      = "BACKEND_CLIENT_SECRET",
#           valueFrom = "${var.api_secret_arn}:BACKEND_CLIENT_SECRET::"
#         },     
#       ]
#       environment = [
#         {
#           name = "ROOT_PATH"
#           value = "/api"
#         },
#         {
#           name = "CORS"
#           value = "https://${data.terraform_remote_state.base.outputs.aws_route53_record_main_name},https://${data.terraform_remote_state.base.outputs.aws_route53_record_main_name}/*"
#           # value = "https://${data.terraform_remote_state.base.outputs.aws_route53_record_main_name},https://${data.terraform_remote_state.base.outputs.aws_route53_record_main_name}/*,http://localhost:3000"
#         },
#         {
#           name = "AUTHORITY"
#           value = "https://keypointvision.us.auth0.com"
#           # value = "https://dev-xn55n1r8bjp2vykg.us.auth0.com"
#         },
#         {
#           name = "AUDIENCE"
#           value = "https://portfolio.keypointvision.com/api"
#           # value = "https://portfolio.keypointvision.com/api/dev"
#         },
#         {
#           name = "AUTH0_AUDIENCE"
#           value = "https://keypointvision.us.auth0.com/api/v2/"
#           # value = "https://dev-xn55n1r8bjp2vykg.us.auth0.com/api/v2/
#         },
#         {
#           name = "PAYMENT_PRICE_ID"
#           value = "price_1PJ8w306xBmQFHMFn1gYQ3qO"
#           # value = "price_1PJ97l06xBmQFHMFkHDXZPgF"
#         },
#         {
#           name = "SHOP_FACE_URL"
#           # value = "http://localhost:3000"
#           # value = "https://exp.keypointvision.org"
#           value = "https://portfolio.keypointvision.com"
#         },
#         {
#           name = "DB_NAME"
#           value = "postgres"
#         },
#         {
#           name = "DB_USER"
#           value = "api_service_account"
#         },
#         {
#           name = "DB_HOST"
#           value = "portfolio-benson-postgres-db.cvoygq2ss2j7.us-west-2.rds.amazonaws.com"
#           # value = "exp-alan-postgres-db.cvoygq2ss2j7.us-west-2.rds.amazonaws.com"
#         },
#         {
#           name = "DB_PORT"
#           value = "5432"
#         },
#       ],
#       logConfiguration = {
#         logDriver = "awslogs",
#         options = {
#           "awslogs-create-group" = "true",
#           "awslogs-group"        = "${var.title}-${var.infra_version}",
#           "awslogs-region"       = var.region,
#           "awslogs-stream-prefix"= "ecs/core"
#         },
#       }
#     }]
#   )
# }

# resource "aws_ecs_service" "core" {
#   name            = "${var.title}-${var.infra_version}-core-api-srv"
#   cluster         = aws_ecs_cluster.main.id
#   task_definition = aws_ecs_task_definition.core_api.family
#   desired_count   = 1

#   launch_type     = "FARGATE"

#   network_configuration {
#     subnets = data.terraform_remote_state.base.outputs.public_subnets
#     assign_public_ip = true
#     security_groups = [aws_security_group.core.id]
#   }
#   load_balancer {
#     target_group_arn = aws_lb_target_group.core.arn
#     container_name   = "proxy"
#     container_port   = 443
#   }
#   deployment_controller {
#     type = "ECS"
#   }
#   tags = {
#     Name = "${var.title}-${var.infra_version}-core-api-srv"
#   }
# }

# ###################### link postgres #########################
# resource "aws_security_group_rule" "core_ingress_postgres" {
#   security_group_id = aws_security_group.postgres.id
#   type              = "ingress"
#   from_port         = 5432
#   to_port           = 5432
#   protocol          = "tcp"
#   source_security_group_id = aws_security_group.core.id
# }