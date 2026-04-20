FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl unzip make python3 python3-pip ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/aws.zip \
  && unzip -q /tmp/aws.zip -d /tmp \
  && /tmp/aws/install \
  && rm -rf /tmp/aws /tmp/aws.zip

ARG TF_VERSION=1.9.8
RUN curl -sSL "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip" -o /tmp/tf.zip \
  && unzip -q /tmp/tf.zip -d /usr/local/bin \
  && rm /tmp/tf.zip \
  && terraform version

USER jenkins
