# 06 - ASVS Audit Update Prompt

Update the ASVS audit for the current app version.

Tasks:
1. Check the latest stable OWASP ASVS version.
2. Record the ASVS version inside the audit document.
3. Use the current app version for the audit filename.
4. Review the ASVS Control Register.
5. Mark controls as Passed, Failed or Not Applicable.
6. Add evidence references.
7. Explain every Not Applicable control.
8. Calculate score as Passed applicable controls / Applicable controls x 100.
9. Confirm the score is at least 90%.
10. Generate `ASVS Audit (App version number).pdf`.
11. Update README and CHANGELOG.

Rules:
- Do not claim a control passes without evidence.
- Do not mark controls Not Applicable without a reason.
- Record remediation actions for failed controls.
