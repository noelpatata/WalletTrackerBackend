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
                                    [envVar: 'NVD_API_KEY',     vaultKey: 'NVD_API_KEY']
                                ]
                            ]
                        ]
                    ) {
                        sh 'mkdir -p dependency-check-report'
                        dependencyCheck(
                            additionalArguments: '--scan app/requirements.txt --enableExperimental --project wallet-tracker-api --format JSON --format HTML --out dependency-check-report --nvdApiKey ${NVD_API_KEY}',
                            odcInstallation: 'owasp dependency check 12.2.2'
                        )

                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv() {
                            sh "${scannerHome}/bin/sonar-scanner"
                        }

                        /*def imageTag = params.IMAGE_VERSION
                        sh 'docker build -t ${REGISTRY}/wallet-tracker:' + imageTag + ' ./app'
                        sh 'echo "${DOCKER_PASSWORD}" | docker login ${REGISTRY} -u "${DOCKER_USERNAME}" --password-stdin' +
                           ' && docker push ${REGISTRY}/wallet-tracker:' + imageTag +
                           ' && docker logout ${REGISTRY}'*/

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
            post {
                always {
                    archiveArtifacts artifacts: 'dependency-check-report/**/*', allowEmptyArchive: true
                    dependencyCheckPublisher pattern: 'dependency-check-report/dependency-check-report.json'
                }
            }
        }
    }
}
