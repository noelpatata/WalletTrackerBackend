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
                                    [envVar: 'DTRACK_URL',      vaultKey: 'DTRACK_BASE_URL'],
                                    [envVar: 'DTRACK_API_KEY',  vaultKey: 'DTRACK_API_KEY']
                                ]
                            ]
                        ]
                    ) {
                        def imageTag = params.IMAGE_VERSION
                        def imageRef = "\${REGISTRY}/wallet-tracker:${imageTag}"

                        sh 'docker build -t ' + imageRef + ' ./app'

                        sh 'mkdir -p dependency-check-report'
                        sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock anchore/syft ' + imageRef + ' -o cyclonedx-xml > dependency-check-report/sbom.xml'
                        sh 'curl -s -X POST "${DTRACK_URL}/api/v1/bom" -H "X-Api-Key: ${DTRACK_API_KEY}" -H "Content-Type: multipart/form-data" -F "projectName=wallet-tracker-api" -F "projectVersion=0.1.0" -F "bom=@dependency-check-report/sbom.xml"'

                        sh 'python3 dtrack-to-sonarqube.py'

                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv() {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.externalIssuesReportPaths=dependency-check-report/dtrack-findings.json"
                        }

                        sh 'echo "${DOCKER_PASSWORD}" | docker login ${REGISTRY} -u "${DOCKER_USERNAME}" --password-stdin' +
                           ' && docker push ' + imageRef +
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
