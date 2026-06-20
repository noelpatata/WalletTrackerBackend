pipeline {
    agent any
    parameters {
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to build')
        string(name: 'IMAGE_VERSION', defaultValue: 'latest', description: 'Docker image version tag')
    }
    environment {
        VAULT_ADDR = credentials('vault-addr')
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: "${params.GIT_BRANCH}", url: 'https://github.com/noelpatata/WalletTrackerAPI.git'
            }
        }
        stage('Vault dependent Stages') {
            steps {
                script {
                    withCredentials([[$class: 'VaultTokenCredentialBinding', credentialsId: 'vault-token', vaultAddr: env.VAULT_ADDR]]) {
                    withVault(
                        configuration: [
                            vaultUrl: env.VAULT_ADDR,
                            vaultCredentialId: 'vault-token',
                            engineVersion: 2
                        ],
                        vaultSecrets: [
                            [
                                path: "secret/wallet-tracker/backend",
                                engineVersion: 2,
                                secretValues: [
                                    [envVar: 'REGISTRY',        vaultKey: 'REGISTRY_IP'],
                                    [envVar: 'DOCKER_USERNAME', vaultKey: 'REGISTRY_USER'],
                                    [envVar: 'DOCKER_PASSWORD', vaultKey: 'REGISTRY_PASSWORD'],
                                    [envVar: 'DTRACK_URL',      vaultKey: 'DTRACK_URL'],
                                    [envVar: 'DTRACK_API_KEY',  vaultKey: 'DTRACK_API_KEY']
                                ]
                            ]
                        ]
                    ) {
                        sh 'mkdir -p dependency-check-report'
                        sh 'uv export --project app --no-dev --format requirements-txt -o dependency-check-report/pinned-deps.txt'
                        sh 'uvx cyclonedx-py requirements dependency-check-report/pinned-deps.txt --pyproject app/pyproject.toml -o dependency-check-report/sbom.xml --of XML'
                        sh 'curl -s -X POST "${DTRACK_URL}/api/v1/bom" -H "X-Api-Key: ${DTRACK_API_KEY}" -H "Content-Type: multipart/form-data" -F "projectName=wallet-tracker-api" -F "projectVersion=0.1.0" -F "bom=@dependency-check-report/sbom.xml"'

                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv() {
                            sh "${scannerHome}/bin/sonar-scanner"
                        }

                        def imageTag = params.IMAGE_VERSION
                        sh 'docker build -t ${REGISTRY}/wallet-tracker:' + imageTag + ' ./app'
                        sh 'echo "${DOCKER_PASSWORD}" | docker login ${REGISTRY} -u "${DOCKER_USERNAME}" --password-stdin' +
                           ' && docker push ${REGISTRY}/wallet-tracker:' + imageTag +
                           ' && docker logout ${REGISTRY}'

                        dir('terraform') {
                            sh 'terraform init'
                            retry(3) {
                                sh 'terraform plan'
                            }
                            retry(3) {
                                sh 'terraform apply -auto-approve'
                            }
                        }
                    }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dependency-check-report/sbom.xml', allowEmptyArchive: true
                }
            }
        }
    }
}
