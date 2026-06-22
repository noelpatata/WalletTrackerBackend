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
                git branch: "${params.GIT_BRANCH}", url: 'https://github.com/noelpatata/WalletTrackerBackend.git'
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
                                    [envVar: 'NVD_API_KEY',     vaultKey: 'NVD_API_KEY'],
                                    [envVar: 'DTRACK_URL',      vaultKey: 'DTRACK_BASE_URL'],
                                    [envVar: 'DTRACK_API_KEY',  vaultKey: 'DTRACK_API_KEY']
                                ]
                            ]
                        ]
                    ) {
                        sh 'mkdir -p dependency-check-report'

                        catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                            dependencyCheck(
                                additionalArguments: '--scan app/pyproject.toml --enableExperimental --project wallet-tracker-api --format JSON --out dependency-check-report --nvdApiKey ${NVD_API_KEY}',
                                odcInstallation: 'owasp dependency check 12.2.2'
                            )
                        }

                        def imageTag = params.IMAGE_VERSION
                        sh 'docker build -t ${REGISTRY}/wallet-tracker:' + imageTag + ' ./app'

                        sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock anchore/syft ${REGISTRY}/wallet-tracker:' + imageTag + ' -o cyclonedx-xml > dependency-check-report/sbom-cyclonedx.xml'

                        def projName = sh(script: "python3 -c \"import tomllib; f=open('app/pyproject.toml','rb'); print(tomllib.load(f)['project']['name'])\"", returnStdout: true).trim()
                        def projVersion = sh(script: "python3 -c \"import tomllib; f=open('app/pyproject.toml','rb'); print(tomllib.load(f)['project']['version'])\"", returnStdout: true).trim()

                        sh 'curl -s -X POST "${DTRACK_URL}/api/v1/bom" -H "X-Api-Key: ${DTRACK_API_KEY}" -H "Content-Type: multipart/form-data" -F "projectName=' + projName + '" -F "projectVersion=' + projVersion + '" -F "bom=@dependency-check-report/sbom-cyclonedx.xml"'

                        sh 'docker run --rm -v "$(pwd)/dependency-check-report:/reports" --entrypoint sh ${REGISTRY}/wallet-tracker:' + imageTag + ' -c "pip install -q cyclonedx-bom 2>/dev/null && cyclonedx-py environment > /reports/sbom-cyclonedx-pyonly.xml"'
                        sh 'curl -s -X POST "${DTRACK_URL}/api/v1/bom" -H "X-Api-Key: ${DTRACK_API_KEY}" -H "Content-Type: multipart/form-data" -F "projectName=' + projName + '-py-deps" -F "projectVersion=' + projVersion + '" -F "bom=@dependency-check-report/sbom-cyclonedx-pyonly.xml"'

                        sh 'python3 dtrack-to-sonarqube.py'

                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv() {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.externalIssuesReportPaths=dependency-check-report/dtrack-findings.json"
                        }

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
                    archiveArtifacts artifacts: 'dependency-check-report/**/*', allowEmptyArchive: true
                    dependencyCheckPublisher pattern: 'dependency-check-report/dependency-check-report.xml'
                }
            }
        }
    }
}
