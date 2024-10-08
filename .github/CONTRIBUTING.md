# Contributing to Unifier
> [!NOTE]
> This is the repository for **Unifier**. To contribute to Unifier Micro, please go to the [Unifier Micro
> repository](https://github.com/greeeen-dev/unifier-micro).

Thank you for showing your interest in helping us make Unifier better!

## Reporting bugs
If you found a bug, please open a GitHub issue using the **Bug report** template.
- If there's already an issue for the bug, **do not open another one**, and add on to the existing issue instead. You
  are free to add more details about the bug, this way we can more easily patch bugs.
- If the bug is limited to a specific branch (e.g. main, dev), please say so in the **Additional context** section.
- If you're reporting bugs that happen when a certain plugin is installed, we recommend you open an issue on the plugin's 
  repository instead.
  - If you or/and the plugin maintainers are **absolutely sure** that the issue is caused by Unifier and not the plugin,
    you may open an issue on this repository.

## Suggesting a feature
If you have feedback for us, please open a GitHub issue using the **Feature request** template.
- If there's already an issue for the feature request, **do not open another one**, and add on to the existing issue. You
  are free to add on to the feedback by giving your suggestions on how the feature could be implemented.
- If your feature request is related to a bug in an existing issue (e.g. suggesting a potential solution to a problem),
  please add on to the bug report instead.

## Contributing code/localization
If you wish to contribute your code to the project or help us translate Unifier,, please **fork the repository**, add your
changes to your fork, then open a Pull request.
- If your PR fixes a bug or addresses a feature request, please reference the relevant issues. This way, people (including
  us) can know if we need to do work to fix an issue, or if we just need to merge a PR.
  If your changes are **purely cosmetic**, please don't open a PR, unless the changes **significantly improve** the
  readability of the source code.
- Please make sure you've tested your code. Include screenshots/screen recordings in the PR so we know how your changes will
  work.
  - **This includes your language JSON files.** Please make sure they have the correct syntax. Also, check that all of your
    translated strings load properly.

### Testing Unifier
To test the modifications you have made, you will need to install Unifier. Please follow [this 
guide](https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started) to learn how to install and configure Unifier so 
you can test the modified code before opening a PR.

### The bot crashes on boot!
If your changes only modify the core and core extensions (sysmgr.py, lockdown.py), you may test Unifier by running `python3
unifier.py core`.

If your changes modify other system extensions, please review your code. If you're absolutely sure the crash isn't caused by
your code, but rather ours, let us know.

## Low-quality submissions
We reserve all rights to reject any contributions to our project. When you create a low-quality submission, it will be
closed/rejected, and we may restrict you from contributing any further to our repository. So please don't waste our time by
doing this.
