# Multi Agent on AWS

This repository contains a proof-of-concept multi-agent architecture for a restaurant/retail workflow (menu, orders, payments, promos, stores) with AWS tooling and deployment scripts.

## Repository Layout

- `1_business_modeling/` - business value model samples
- `2_data_strategy/` - data source definitions and helpers for menu, orders, payments, promos, stores
- `3_proof_of_concept/` - agents and knowledge base setup scripts for local/dev proof-of-concept
  - `agents/` - agent orchestration Python code
  - `knowledge_bases/` - KB setup scripts
- `4_monitor_and_evaluate/` - CloudWatch agent config and observability helper scripts
- `5_security_rai/` - least privilege policy and parameter store validation scripts
- `6_deploy/` - deployment pipeline for production/managed runtime
  - `agents/` - deployable agent entrypoints and runtime config
  - `scripts/` - CloudFormation/Cognito/web deployment scripts
  - `web-app/` - static frontend and web server for agent UI

## Quickstart

1. Install requirements:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Set up environment variables:
   ```bash
   .\setup_env.sh
   ```
3. Run proof-of-concept agents:
   ```bash
   cd 3_proof_of_concept/agents
   python barista_supervisor_agent.py
   ```
4. Deploy with AWS infrastructure scripts:
   ```bash
   cd 6_deploy/scripts
   .\deploy_stack.sh
   ```

## Local test utilities

- `2_data_strategy/*/configure_*_data_sources.sh` for local data loading
- `3_proof_of_concept/knowledge_bases/*_knowledge_base_setup.sh` for KB setup
- `6_deploy/web-app/serve.py` to run local web UI

## Project notes

- Designed to integrate with AWS Bedrock / LLM service and multi-agent coordination.
- Focused on data strategy (knowledge-base backed policies), observability, and least-privilege security.

## License

- MIT (`LICENSE` file)
