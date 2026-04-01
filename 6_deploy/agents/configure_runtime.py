from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import boto3, json, time, os, sys

environment_variables_file = os.path.expanduser("~/environment/env.sh")

STACK_NAME = "path-to-production-gen-ai-application"
OUTPUT_NAME = "WorkshopRoleArn"


def get_stack_output(cf, stack_name, output_key):
    resp = cf.describe_stacks(StackName=stack_name)
    stacks = resp.get("Stacks", [])
    if not stacks:
        raise RuntimeError(f"Stack not found: {stack_name}")
    for o in stacks[0].get("Outputs", []):
        if o.get("OutputKey") == output_key:
            return o.get("OutputValue")
    raise RuntimeError(f"Output {output_key} not found in stack {stack_name}")


def role_name_from_arn(role_arn: str) -> str:
    return role_arn.split("/")[-1]


def ensure_agentcore_in_trust_policy(iam, role_name: str):
    role = iam.get_role(RoleName=role_name)["Role"]
    policy = role["AssumeRolePolicyDocument"]

    def has_agentcore(stmt):
        principal = stmt.get("Principal", {})
        svc = principal.get("Service")
        if isinstance(svc, str):
            return svc == "bedrock-agentcore.amazonaws.com"
        if isinstance(svc, list):
            return "bedrock-agentcore.amazonaws.com" in svc
        return False

    if any(has_agentcore(s) for s in policy.get("Statement", [])):
        return

    new_stmt = {
        "Effect": "Allow",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }
    policy.setdefault("Statement", []).append(new_stmt)

    iam.update_assume_role_policy(
        RoleName=role_name,
        PolicyDocument=json.dumps(policy)
    )


def main():
    region = Session().region_name
    rt = Runtime()
    agent_name = "barista_agent"

    cf = boto3.client("cloudformation", region_name=region)
    iam = boto3.client("iam", region_name=region)

    print("Fetching execution role from CloudFormation output...")
    exec_role_arn = get_stack_output(cf, STACK_NAME, OUTPUT_NAME)
    exec_role_name = role_name_from_arn(exec_role_arn)
    print(f"Using execution role: {exec_role_arn}")

    print("Ensuring trust policy allows bedrock-agentcore.amazonaws.com...")
    ensure_agentcore_in_trust_policy(iam, exec_role_name)

    print("Configuring runtime with specified execution role...")
    resp = rt.configure(
        entrypoint="barista_supervisor_agent.py",
        execution_role=exec_role_arn,
        auto_create_execution_role=False,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name=agent_name,
    )
    print("Configure response:", resp)

    ENV_KEYS = [
        "ORDERS_KNOWLEDGE_BASE_ID",
        "STORES_KNOWLEDGE_BASE_ID",
        "MENU_KNOWLEDGE_BASE_ID",
        "PAYMENTS_KNOWLEDGE_BASE_ID",
        "PROMOS_KNOWLEDGE_BASE_ID",
        "REGION",
        "MODEL_ARN",
        "MODEL_ID",
        "S3_BUCKET_NAME",
        "GUARDRAIL_ID",
        "GUARDRAIL_VERSION"
    ]
    env_vars = {k: os.environ[k] for k in ENV_KEYS if k in os.environ}
    print("Passing env vars to AgentCore:", list(env_vars.keys()))

    print("Launching agent...")
    launch_result = rt.launch(env_vars=env_vars, auto_update_on_conflict=True)
    print("Launch response:", launch_result)

    end_status = {"READY", "CREATE_FAILED", "DELETE_FAILED", "UPDATE_FAILED"}
    status = rt.status().endpoint["status"]
    print("Status:", status)
    while status not in end_status:
        time.sleep(10)
        status = rt.status().endpoint["status"]
        print("Status:", status)

    endpoint_info = rt.status().endpoint
    runtime_arn = endpoint_info.get("agentRuntimeArn")
    if not runtime_arn:
        print("agentRuntimeArn unavailable; nothing written to env.sh.", file=sys.stderr)
        return

    os.makedirs(os.path.dirname(environment_variables_file), exist_ok=True)
    with open(environment_variables_file, "a", encoding="utf-8") as f:
        f.write(f'export AGENT_RUNTIME_ARN="{runtime_arn}"\n')

    print(f'Wrote AGENT_RUNTIME_ARN to {environment_variables_file}')


if __name__ == "__main__":
    main()
