# Security Policies and Procedures

This document outlines security procedures and general policies for the pyzmq project.

- [Reporting a Bug](#reporting-a-bug)
- [Security Process](#security-process)
- [Comments on this Policy](#comments-on-this-policy)

## Reporting a Bug

Thank you for improving the security of pyzmq. We appreciate your efforts and
responsible disclosure and will make every effort to acknowledge your
contributions.

Please report vulnerabilities via GitHub's security reporting at
https://github.com/zeromq/pyzmq/security/advisories.
You may also report vulnerabilities by emailing the lead maintainer at benjaminrk AT gmail.com.
If you do so, please include your github username if you have one for the vulnerability process.

Maintainers will acknowledge the report as promptly as possible,
and will follow up with a more detailed response.

## Security Process

If you haven't used GitHub's vulnerability reporting, a draft GitHub security advisory will be created.
The draft advisory will be used to privately discuss fixes and disclosure,
including gathering more information from the reporter, as needed.
After the fix is available to users, the security advisory will be published, usually within 7 days of publishing.

Report security bugs in libzmq itself or other packages to the maintainers of those packages.

Once the draft advisory is created, we will take the following steps:

- Confirm the problem and determine the affected versions.
- Audit code to find any potential similar problems.
- Prepare fixes for all releases still under maintenance.
  This will usually be only the current major version.
  These fixes will be released as fast as possible to PyPI and conda-forge.
- Notify tidelift.
- Publish GitHub Security Advisory.

The timeline is on a best-effort basis.

## Comments on this Policy

Feel free to open a pull request or issue to suggest improvements to this process.
Contributions welcome!
