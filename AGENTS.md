## Workflow

Use simpler easy to read for humans language when possible, don't overcomplicate any text if it doesn't provide any real benefit

**Questions are READ ONLY** Don't modify any code when asked a question, only modify when an order is given

Don't modify this file without permission.

Organize the tickets into folders depending on the status so the project is better organized and easier for the humans in the loop to review and keep track of the tickets, separate them in these folders: DONE, TO_REVIEW, OPEN, BLOCKED, IN_PROGRESS.

## Ticket completion and human review

When implementation and checks finish, decide whether the user must review anything.

- If no human review is needed, move the ticket to `DONE`.
- If human review is needed, move the ticket to `TO_REVIEW`. Do not mark it as `DONE` until the review passes.
- State exactly what the user must check, how to check it, and the expected result. Use a short numbered checklist with concrete actions, file paths, commands, or screens when relevant.
- Keep each review step direct and independently verifiable. Replace vague instructions such as "confirm it works" with a specific action and expected result.
- Require human review when automated checks cannot verify user-visible behavior, content quality, or environment-specific behavior.
