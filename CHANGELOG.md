# CHANGELOG


## v0.1.0 (2026-07-02)

### Continuous Integration

- Switch to self-hosted runner for local deploy, pull image instead of building
  ([`68d487f`](https://github.com/Norlik13/CEZI_zen/commit/68d487f2e8926ab10252ef1ea3083b6b7804cdeb))


## v0.1.0-rc.1 (2026-07-01)

### Continuous Integration

- Add python-semantic-release with Docker image versioning Automate versioning via Conventional
  Commits. On push to master, python-semantic-release computes the next version, tags it, publishes
  a GitHub release + changelog, and the Docker image is built and pushed to ghcr.io tagged with both
  the version and latest.
  ([`0b61107`](https://github.com/Norlik13/CEZI_zen/commit/0b611079daea3898de333f215f68d15b50463573))

- Split CI and CD, remove duplicate SonarQube workflow
  ([`8cc64e4`](https://github.com/Norlik13/CEZI_zen/commit/8cc64e463c6be5be48504a9de5ed497b0373a13a))

Separate verification (CI) from delivery/deployment (CD):

- Delete build.yml: it duplicated ci.yml's tests+coverage and used SonarQube while the project
  actually uses SonarCloud (sonar.organization confirms it). - Remove the docker job from ci.yml so
  CI is purely install, tests, coverage, SonarCloud and flake8. The versioned image is built by the
  release pipeline (release.yml) and tagged with the semantic version. - Add deploy.yml: manual
  (workflow_dispatch) CD template that pulls the published ghcr.io image by version tag and runs it
  via docker compose. Requires DEPLOY_HOST/DEPLOY_USER/DEPLOY_SSH_KEY secrets and switching
  docker-compose.prod.yml from `build: .` to `image:`.

- Trigger SonarCloud on push to develop as well
  ([`707fee1`](https://github.com/Norlik13/CEZI_zen/commit/707fee1b1d38b73c5e454992215cddc67f8a5f7a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Use ubuntu-latest runner instead of self-hosted
  ([`adfca80`](https://github.com/Norlik13/CEZI_zen/commit/adfca800d9794925d55037a99150067b9eaa6e9d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Pipeline CI local + SonarCloud + GitFlow
  ([`47380b0`](https://github.com/Norlik13/CEZI_zen/commit/47380b0c09e6ae1596b2b3a7afd7e997fff19340))

- GitHub Actions sur runner self-hosted (local) - Étapes : pip install → django check → tests avec
  coverage → SonarCloud - sonar-project.properties pour l'analyse Python/Django - README : stratégie
  GitFlow, tableau pipeline CI, badges SonarCloud - requirements.txt complet (whitenoise, gunicorn,
  coverage) - .gitignore et nginx/nginx.conf ajoutés au dépôt

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
