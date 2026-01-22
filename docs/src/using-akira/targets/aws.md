# AWS Targets

Test LLMs on AWS Bedrock and SageMaker.

## AWS Bedrock

### Prerequisites

- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Bedrock model access enabled in your AWS account

### Setup

```
akira> target bedrock https://bedrock-runtime.us-east-1.amazonaws.com \
    -m anthropic.claude-3-sonnet-20240229-v1:0
```

### Options

| Option | Description |
|--------|-------------|
| `-m, --model` | Bedrock model ID |
| `--region` | AWS region |

### Available Models

```bash
# Claude on Bedrock
-m anthropic.claude-3-opus-20240229-v1:0
-m anthropic.claude-3-sonnet-20240229-v1:0
-m anthropic.claude-3-haiku-20240307-v1:0

# Llama 2 on Bedrock
-m meta.llama2-70b-chat-v1
-m meta.llama2-13b-chat-v1

# Amazon Titan
-m amazon.titan-text-express-v1
```

### Authentication

Bedrock uses AWS Signature Version 4. Ensure your credentials have `bedrock:InvokeModel` permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "*"
    }
  ]
}
```

## AWS SageMaker

### Setup

```
akira> target sagemaker https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/my-llm-endpoint/invocations
```

### Custom Endpoint

For SageMaker endpoints with custom input/output:

```
akira> target api https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/my-endpoint/invocations \
    --request-template '{"inputs": "$payload", "parameters": {"max_new_tokens": 200}}' \
    --response-path '0.generated_text'
```

### Authentication

SageMaker also uses AWS Signature Version 4. Required permission:

```json
{
  "Effect": "Allow",
  "Action": "sagemaker:InvokeEndpoint",
  "Resource": "arn:aws:sagemaker:*:*:endpoint/my-llm-endpoint"
}
```

## Example Session

```
akira> target bedrock https://bedrock-runtime.us-east-1.amazonaws.com \
    -m anthropic.claude-3-sonnet-20240229-v1:0
[+] Target configured: bedrock

akira> use extraction/system_prompt_leak
akira> run
[*] Running system_prompt_leak...
```

## Cost Considerations

- Bedrock charges per token
- SageMaker charges for endpoint uptime + inference
- Monitor costs in AWS Cost Explorer
