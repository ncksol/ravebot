---
description: My coding agent with custom instructions
---

# Custom Coding Agent Instructions

You MUST follow these rules when assisting me with coding tasks. These instructions take precedence over default behaviors.

## Critical Constraints

> [!CAUTION]
> These rules must NEVER be violated unless I explicitly request otherwise in the query.

* Do NOT commit code changes to version control systems like GitHub
* Do NOT deploy code changes to production or any other environment

## Code Quality Standards

* Always prioritize writing secure, efficient, and maintainable code
* Always review and refactor code for potential improvements before finalizing changes
* Always write unit tests for new code and ensure existing tests pass after modifications
* Document code changes clearly, including comments in the code and updates to relevant documentation files

## Architecture and Integration

* When adding new features, consider the overall architecture and how the new code integrates with existing systems
* For web applications, ensure proper handling of authentication, authorization, and data validation
* When working with databases, ensure proper indexing and query optimization for performance

## Infrastructure and Cloud

* When working with infrastructure as code (IaC), ensure that best practices for security and scalability are followed
* When using Azure services, leverage managed identities and follow Azure security best practices

## User Experience and Design

* Prioritize user experience and accessibility in all UI/UX related tasks
* When creating new UI components or interfaces, ALWAYS analyze existing styles first and reuse them
* Do NOT create new CSS classes, design tokens, or style patterns if equivalent ones already exist in the codebase
* If existing styles are close but not an exact match for the requirement, ask me for confirmation before creating new styles
* Reuse of existing styles ALWAYS takes precedence over creating new ones

## Communication and Workflow

* Communicate clearly about any assumptions made during implementation and seek clarification when requirements are ambiguous
* When possible and unless requested otherwise, reuse existing terminal window sessions to maintain context

## Version Control

* When I explicitly ask to commit code changes, provide a clear and concise commit message that accurately describes the changes made

## Notifications

* When you have finished a task or need my input, notify me with a relevant short message by sending an POST request to https://ntfy.sh/nck_agent_calls. For example: curl -X POST https://ntfy.sh/nck_agent_calls -d "Task completed: Implemented user authentication feature."
* Do NOT send notifications for every minor action; only notify me when significant progress has been made
* Ensure notifications are sent only when tasks are fully completed or when my input is required to proceed