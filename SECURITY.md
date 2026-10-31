# Security policy

Report vulnerabilities privately through GitHub private vulnerability reporting when enabled, or contact the maintainer through the profile contact channel. Do not open public issues containing credentials or actionable undisclosed vulnerabilities.

The supported version is main. `app/vuln.py` is an intentionally unsafe analysis fixture: never start or package it. The release build packages only `app/server.py`.

Changes to workflows, scanner policy, baselines, gate code and tests require trusted maintainer review. A passing workflow cannot establish that its own modified enforcement code is trustworthy. Require an independent reviewer and protected required checks before using this reference for production delivery.
