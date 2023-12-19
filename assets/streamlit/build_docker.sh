# Configure Account and region

AWS_ACCOUNT_ID=$1
AWS_REGION='us-east-1'

IMAGE_TAG='latest'
ECR_REPOSITORY='cdk-hnb659fds-container-assets-454674044397-us-east-1'
# ECR_REPOSITORY='public.ecr.aws/v1a3q6c0/streamlit-temp-stack:latest'
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/v1a3q6c0
docker build . --tag $IMAGE_TAG
docker tag $IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
eval $(aws ecr get-login --no-include-email)
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest