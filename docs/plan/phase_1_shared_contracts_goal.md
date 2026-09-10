# Phase 1 — Shared Contracts and Safe Execution

Status: in progress  
Schedule: weeks 1-2

## Goal

Establish one reliable execution contract shared by WhatsApp, CLI, LangGraph,
and the `xninetzy` MCP server. Xninetzy V1 is a local-first, single-owner,
CPU-only Personal Learning OS and Life OS that closes this loop:

`Capture -> Understand -> Plan -> Execute -> Review -> Adapt`

## Design decisions

- Shared domains and the central registry own business logic. Interfaces only
  inject verified identity, render responses, and invoke shared operations.
- The registry is the canonical catalogue. No MCP-only wrapper may hide or
  replace a registry tool schema.
- A tool manifest declares stability, feature pack, risk, approval,
  idempotency, and evidence requirements. Legacy tool names remain compatible
  through V2.
- Every external write, submission, cross-contact delivery, and final action
  passes through an action gate. Approval binds the verified owner, exact
  payload hash, action type, and expiry.
- Deterministic identity, policy, and retrieval checks happen before LLM tool
  selection. The model cannot alter authorization or risk metadata.

## Scope

1. Remove MCP schema drift through registry-derived exposure.
2. Introduce the manifest and action-gate foundation without breaking stable
   tool names.
3. Adopt the gate for KRS war arming, QA submission, and HEBAT submission
   workflows while preserving existing confirmation flows during migration.
4. Add focused parity and safety tests.
5. Update progress documentation with verification evidence.

## Acceptance gate

- MCP exposes every canonical tool argument except server-injected identity.
- A policy decision with `requires_approval=true` cannot lead to an external
  mutation until an exact, non-expired approval is validated.
- Existing tool names continue to resolve from every supported interface.
- Tests prove schema parity and blocked unapproved writes.

## Implementation order
