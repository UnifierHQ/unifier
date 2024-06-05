# Security Policy
At UnifierHQ, we take user safety very seriously. We constantly try to 
implement features that help minimize or eliminate the effects malicious
actors can have on our community. However, we understand we are not 
perfect, and there may be vulnerabilities in our code that may impact 
the safety of hosters and users every now and then.

## Supported Versions
Versions v1.2.x and newer will receive at least 6 months of bug fixes and
security updates after being superseded by a newer series. 

Currently, v1.1.x and newer receive security updates. Preceding versions
have been discontinued and will not be updated any further.
| Version | Type    | Supported                    | EoL        |
| ------- | ------- | ---------------------------- | ---------- |
| 2.0.x   | release | :white_check_mark: Supported | Not legacy |
| 1.2.x   | legacy  | :white_check_mark: Supported | 05/12/2024 |
| 1.1.x   | legacy  | :warning: Nearing EoL        | 05/07/2024 |
| < 1.1   | eol     | :x: Unsupported              | EoL        |

> [!NOTE]
> We have decided to extend v1.1.x support while we work on v2.

### What do the types mean?
- `release`: This is the newest series and is in active development.
- `legacy`: This is an older series that will continue to receive bug
  patches and security updates.
- `eol`: This series is no longer maintained.

## Reporting a Vulnerability
When you have found a vulnerability, DO NOT open a bug report. These 
reports will be taken down and may result in sanctions.

Instead, please either DM a developer on Discord, or report the 
vulnerability to us, so we can privately patch the vulnerability.

### What counts as a vulnerability?
Here are examples of what you **should** report to us as security
vulnerabilities:
- A bug in the code that allows third parties to get access to moderator
  permissions
- A bug in the code that allows third parties to execute malicious code
  on your system
- etc.

And examples of what you **shouldn't** report to us:
- Lack of protection against certain server raid types (this is better
  off as a **feature suggestion**)
- Lack of certain moderation tools (this is better off as a **feature
  suggestion**)
- Unprofessional moderation on Unifier instances (sort this out with your
  instance's admins)
- etc.
