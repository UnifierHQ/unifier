# Security Policy
At UnifierHQ, we take user safety very seriously. We always try to 
implement features that help minimize or eliminate the effects malicious
actors can have on our community. However, we understand we are not 
perfect, and there may be vulnerabilities in our code that may impact 
the safety of hosters and users every now and then.

## Supported Versions
All Unifier release series will receive at least 4 months of bug fixes and
security updates after being superseded by a newer series. LTS release
series are supported for at least one year.

All EoL dates are in dd/mm/yyyy format.
| Version                        | Type     | Supported                    | EoL        |
| ------------------------------ | -------- | ---------------------------- | ---------- |
| 3.x (`elegant-elderberry`)     | release  | :white_check_mark: Supported | Not legacy |
| 2.x LTS (`daring-dragonfruit`) | legacy   | :white_check_mark: Supported | 17/09/2025 |
| 1.2.x (`cheerful-cranberry`)   | legacy   | :warning: Nearing EoL        | 05/12/2024 |
| < 1.2                          | eol      | :x: Unsupported              | EoL        |

### What do the types mean?
- `release`: This is the newest series and is in active development.
- `legacy`: This is an older series that will continue to receive bug
  patches and security updates.
- `extended`: This is an older series that should have been discontinued
  but continue to receive updates due to special circumstances.
- `eol`: This series is no longer maintained. They will not receive any
  updates.

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
- Destructive actions that can be done using eval command (it is your
  responsibility to know what you're doing, only report if there's a
  missing permissions check or something that we should actually take
  action on)
- etc.
