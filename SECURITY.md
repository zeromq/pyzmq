# Security Policies and Procedures

This document outlines security procedures and general policies for the pyzmq project.

- [Reporting a Bug](#reporting-a-bug)
- [Disclosure Policy](#disclosure-policy)
- [Comments on this Policy](#comments-on-this-policy)

## Reporting a Bug

Thank you for improving the security of pyzmq. We appreciate your efforts and
responsible disclosure and will make every effort to acknowledge your
contributions.

Report security bugs by emailing the lead maintainer at benjaminrk AT gmail.com.

The lead maintainer will acknowledge your email as promptly as possible,
and will follow up with a more detailed response.

When the issue is confirmed, a GitHub security advisory will be created to discuss resolutions.
We will endeavor to keep you informed of the progress towards a fix and full
announcement, and may ask for additional information or guidance.

Report security bugs in libzmq itself or other packages to the mainainers of those packages.

## Disclosure Policy

When the security team receives a security bug report, they will assign it to a
primary handler. This person will coordinate the fix and release process,
involving the following steps:

- Confirm the problem and determine the affected versions.
- Audit code to find any potential similar problems.
- Prepare fixes for all releases still under maintenance. These fixes will be
  released as fast as possible to npm.

## Comments on this Policy

If you have suggestions on how this process could be improved please submit a
pull request.
