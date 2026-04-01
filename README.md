

# Multi-Agent Generative AI System on AWS

This repository contains a **proof-of-concept multi-agent architecture** for restaurant and retail workflows, covering:

* Menu management
* Orders
* Payments
* Promotions
* Stores

It demonstrates how to build **production-ready agentic AI applications** using **Amazon Bedrock**, **Strands SDK**, and **multi-agent collaboration (MAC) systems**. The system integrates **knowledge bases (RAG)** and a **supervisor agent** to orchestrate tasks across specialized sub-agents.

---

## Complete Path-to-Production Workflow

1. **Ideation & Business Modeling** – Define AI use cases and quantify business value.
2. **Data Strategy** – Implement domain-specific data sources and integrate with knowledge bases.
3. **Multi-Agent System Development** – Build, orchestrate, and test specialized AI agents for a coffee shop scenario.

**Key technologies include:**

* **Bedrock Knowledge Bases** for retrieval-augmented generation (RAG)
* **Strands SDK** for creating specialized AI agents
* **Supervisor Agent** to orchestrate multi-agent collaboration across business domains

This workflow demonstrates how to **design, build, and validate agentic AI solutions** capable of handling complex business workflows through intelligent task orchestration and domain-specific expertise.

---

##Objectives

By the end of this project, you will be able to:

1. **Design and validate AI use cases**

   * Use interactive Streamlit applications for ideation and quantitative business value modeling

2. **Implement a comprehensive data strategy**

   * Provision and configure domain-specific data sources:

     * Amazon DynamoDB
     * Amazon Aurora MySQL
     * Amazon S3
   * Integrate these sources with knowledge bases

3. **Create and configure knowledge bases**

   * Use **Bedrock** with S3 data sources and **Amazon OpenSearch Serverless** vector storage

4. **Build specialized AI agents**

   * Using the **Strands SDK** framework
   * Domains: Orders, Menu, Stores, Payments, Promotions

5. **Implement a Multi-Agent Collaboration (MAC) system**

   * Deploy a **Barista Supervisor agent** to orchestrate tasks across sub-agents

6. **Test and validate the complete agentic AI system**

   * Conduct interactive natural language scenario testing

##Architecture

![Main Architecture](architecture/Main%20Architecture.png)

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
