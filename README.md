# Zero-Trust Governance Framework for Autonomous AI Agents

## Phase 1 — Autonomous Banking Automation Baseline

### Team

- Hruthik
- Vaibhav

---

## 1. Project Overview

This project focuses on developing a Zero-Trust Governance Framework for
Autonomous AI Agents operating in sensitive domains.

As the practical application domain, we developed FinSecure, an
LLM-driven autonomous banking operations platform.

Phase 1 focuses on building the baseline autonomous banking system
before introducing the proposed Zero-Trust security mechanisms.

The purpose of Phase 1 is to establish a functional autonomous system
and identify vulnerabilities that can arise when LLM agents are given
access to banking tools.

---

## 2. Phase 1 Objective

The objectives of Phase 1 are:

- Build an autonomous banking operations environment.
- Integrate an LLM with a multi-agent architecture.
- Enable agents to dynamically select registered banking tools.
- Implement realistic banking operations using synthetic data.
- Establish the baseline system for vulnerability evaluation.
- Identify vulnerabilities caused by autonomous LLM behavior.

---

## 3. System Architecture

The Phase 1 system follows a multi-agent architecture:

User
  |
  v
Orchestrator
  |
  v
Planner
  |
  v
Researcher
  |
  v
Executor
  |
  v
Auditor
  |
  v
Final Response

### Agents

#### Orchestrator
Handles user intent classification, routing, and final response synthesis.

#### Planner
Creates an execution plan for the requested banking task.

#### Researcher
Retrieves relevant banking information using registered tools.

#### Executor
Performs operations using LLM-selected banking tools.

#### Auditor
Reviews the plan, research, execution results, and final outcome.

---

## 4. Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL / relational database
- LangGraph

### AI

- Groq LLM
- LLM-driven tool calling
- Multi-agent workflow

### Frontend

- Web-based banking operations interface

### Data

- Synthetic banking dataset
- Policy knowledge base

---

## 5. Banking Environment

The system contains synthetic banking entities including:

- Customers
- Bank accounts
- Transactions
- Loans
- Fraud cases
- Banking policies

The dataset is designed specifically for controlled experimentation.

No real banking or customer data is used.

---

## 6. Banking Operations

The system supports operations such as:

- Account information lookup
- Transaction lookup
- Banking policy lookup
- Fraud case lookup
- Fund transfers
- Account freeze operations
- Loan-related operations

---

## 7. LLM-Driven Tool Selection

A key feature of Phase 1 is that banking workflows are not implemented
entirely using fixed if/else rules.

The LLM receives registered tool definitions and determines which
tools are required for the requested task.

The Python backend is responsible for executing only registered tools.

This allows the project to study the security implications of
autonomous tool selection.

---

## 8. Phase 1 Baseline

Phase 1 intentionally operates as a baseline system without the
proposed Zero-Trust Governance mechanisms.

The security layer is therefore not used to prevent attacks at this stage.

Instead, the baseline is used to study how autonomous LLM agents behave
under normal and adversarial inputs.

---

## 9. Vulnerability Testing

Initial experiments have identified several potential vulnerabilities:

- Prompt injection
- Instruction hijacking
- Unauthorized tool selection
- Excessive agent autonomy
- Authorization impersonation
- Parameter manipulation
- Agent-to-agent trust issues
- Data leakage
- Auditor inconsistencies
- Tool-calling failures

### Example

A policy-summary request containing an injected instruction to transfer
money resulted in the fund-transfer tool being selected and executed
inside the synthetic banking environment.

This demonstrates the need for governance mechanisms when autonomous
agents are given access to sensitive operations.

---

## 10. Experimental Setup

The experimental environment consists of:

- FastAPI backend
- LangGraph multi-agent workflow
- Groq LLM
- Synthetic banking database
- Registered banking tools
- Policy knowledge base
- Web-based operations interface

All experiments are conducted in a controlled local environment.

---

## 11. Phase 1 Status

### Completed

- Multi-agent architecture
- Orchestrator
- Planner
- Researcher
- Executor
- Auditor
- Groq LLM integration
- LLM-driven tool selection
- Banking database
- Synthetic banking dataset
- Banking tools
- User interface
- Agent activity monitoring
- Initial vulnerability testing

### Current Work

- Baseline validation
- Vulnerability documentation
- Agent/tool behavior analysis
- Performance evaluation

### Next Phase

Implementation of the proposed Zero-Trust Governance Framework.

---

## 12. Future Security Layer

The next phase will introduce security mechanisms including:

- Zero-Trust Proxy
- Prompt protection
- Policy-based authorization
- Provenance tracking
- Behavioral trust evaluation
- Adaptive action authorization
- Tamper-resistant auditing

The same Phase 1 attacks will then be repeated against the secured
system to evaluate the effectiveness of the framework.

---

## 13. Evaluation

The system will be evaluated using:

- Task success rate
- Response time
- Tool-selection accuracy
- Attack success rate
- Security effectiveness
- Security overhead
- LLM/API usage

---

## 14. Safety

The banking environment uses synthetic data and simulated banking
operations.

The system is not connected to real financial institutions,
payment gateways, or real customer accounts.

---

## 15. Project Status

Phase 1 — Autonomous Banking Automation Baseline

Status: Completed / Under Final Validation

Next:
Zero-Trust Governance Implementation