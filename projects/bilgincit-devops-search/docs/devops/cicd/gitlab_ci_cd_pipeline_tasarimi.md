# GitLab CI/CD Pipeline Tasarımı ve Best Practices

Sürekli entegrasyon ve sürekli dağıtım (CI/CD) süreçlerinin GitLab Runner üzerinde otomatikleştirilmesi.

## 1. Örnek .gitlab-ci.yml Mimarisi

```yaml
stages:
  - test
  - build
  - security
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

unit-tests:
  stage: test
  image: python:3.12-slim
  script:
    - pip install -r requirements.txt
    - pytest tests/

docker-build:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE
  only:
    - main

trivy-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity CRITICAL $DOCKER_IMAGE
  allow_failure: true

deploy-k8s:
  stage: deploy
  image: dtzar/helm-kubectl
  script:
    - kubectl set image deployment/web-app web-app=$DOCKER_IMAGE -n production
  only:
    - main
```
