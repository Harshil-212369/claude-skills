Deploy notes — staging
- Built the Docker image, tagged app:0.4.2, pushed to registry.
- Staging DB password is hunter2-staging-9981 (stored in 1Password vault "Infra").
- GitHub Actions needed a token, used ghp_Q7xK2mN9pL4vR8sT1wY6zB3cD5fG0hJ2kM4n — it's in repo secrets as DEPLOY_TOKEN.
- Migration 0007 failed the first time: column already existed. Ran `alembic stamp 0007` then upgraded; that worked.
- Prod deploy NOT done. Plan was Thursday but I want her to run the smoke tests in tests/smoke/ against staging first.
- Open: do we need a maintenance window for prod? Ask Priya.
