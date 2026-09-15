---
source: https://youtube.com/watch?v=1K_OPDOIb5U
study: 30-days-with/devops
date: 2026-09-15
tags: [owasp, dependency-check, security, vulnerabilities, dependencies, jenkins]
---

# Day 6: OWASP Dependency Check

## Summary
OWASP Dependency Check is used to find vulnerabilities in the libraries a project depends on. It is the counterpart to SonarQube: Sonar scans the source code we wrote, Dependency Check scans the third-party code we pulled in.

## Key points
- A packaged application (jar/war) is made of two parts: **source code + dependencies**.
  - SonarQube covers the source code side.
  - OWASP Dependency Check covers the dependencies side.
- The libraries themselves come from **mvnrepository.com** and other public library sites.
- OWASP can find vulnerabilities for many types of languages, not just Java.

## Where it runs in the pipeline
- The dependency check runs **after the build**. The build is what resolves and downloads the full dependency tree, so before it there is nothing complete to scan.
- In Maven it is the `dependency-check-maven` plugin, normally bound to the `verify` phase, which comes after `package`.
- In Jenkins it is its own stage placed after the build stage, scanning the workspace where the resolved jars already sit.
- It works off a local copy of the NVD (National Vulnerability Database), so the first run is slow while that database downloads, and it reports each finding with a CVE id and a severity.
