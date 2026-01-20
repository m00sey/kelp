.PHONY: run deploy build tf-init tf-plan tf-apply

# Local development
run:
	uv run uvicorn kelp.web:app --reload --host 0.0.0.0 --port 8000

# Deployment
deploy:
	cd deploy/ansible && ansible-playbook -i inventory.ini playbook.yml

# Build docker image locally
build:
	docker build -f deploy/Dockerfile -t kelp:latest .

# Terraform commands
tf-init:
	cd deploy/terraform && terraform init

tf-plan:
	cd deploy/terraform && terraform plan

tf-apply:
	cd deploy/terraform && terraform apply
