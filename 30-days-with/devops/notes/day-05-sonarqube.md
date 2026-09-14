---
source: https://youtube.com/watch?v=adeZbnxFhak
study: 30-days-with/devops
date: 2026-09-14
tags: [sonarqube, static-analysis, code-quality, code-coverage, jenkins]
---

# Day 5 — SonarQube

## Summary
SonarQube is a security and static analysis tool we run against our source code. It detects the programming languages in the project automatically and picks the rule set to scan with based on that.

## Key points
- Used for **code quality checks**: bugs, code smells, vulnerabilities.
- A **code smell** is a characteristic in the source code that suggests a deeper design problem, even though the code still works properly:
  - **Bloaters** — long methods or classes, long parameter lists.
  - **Couplers** — excessive dependencies between classes (feature envy, tight coupling), which reduces modularity.
  - **Change preventers** — structures that make modification difficult because a single change requires edits in several places (shotgun surgery).
- **Code coverage** is the amount of code covered while scanning. 80% or more is good; below that is bad.
- **JaCoCo** is the third-party tool that generates the code coverage shown inside SonarQube.
- Sonar uses different **rules** to find the issues in the source code.
- Triple quotes are used to write multiple lines in a Jenkins pipeline.
