def safeBranch() {
    return env.BRANCH_NAME.replaceAll('[^A-Za-z0-9_.-]', '-')
}

def deploysToStaging() {
    return env.BRANCH_NAME in ['develop', 'main'] || env.BRANCH_NAME.startsWith('feature/')
}

pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }
    environment {
        IMAGE_NAME = 'system-health-dashboard'
        IMAGE_TAG = "${safeBranch()}-${env.BUILD_NUMBER}"
        CONTAINER_NAME = "health-check-${safeBranch()}-${env.BUILD_NUMBER}"
        STATE_DIR = '/var/jenkins_home/release-state'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -1'
            }
        }
        stage('Install') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m pytest
                '''
            }
        }
        stage('Build') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:latest .'
                sh 'docker images ${IMAGE_NAME}'
            }
        }
        stage('Tag') {
            steps {
                sh 'docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${IMAGE_TAG}'
                sh 'docker images ${IMAGE_NAME}'
            }
        }
        stage('Health check') {
            steps {
                sh '''
                    docker run -d --name ${CONTAINER_NAME} -e APP_ENV=ci ${IMAGE_NAME}:${IMAGE_TAG}
                    sleep 5
                    docker exec ${CONTAINER_NAME} python -c "import urllib.request; r = urllib.request.urlopen('http://localhost:5000/health'); print(r.status, r.read())"
                '''
            }
        }
        stage('Deploy to Staging') {
            when { expression { deploysToStaging() } }
            steps {
                script { env.STAGING_DEPLOYED = 'true' }
                sh './scripts/deploy.sh staging ${IMAGE_TAG}'
            }
        }
        stage('Smoke test (staging)') {
            when { expression { deploysToStaging() } }
            steps {
                sh './scripts/smoke_test.sh http://app-staging:5000'
            }
        }
        stage('Verify monitoring') {
            when { expression { deploysToStaging() } }
            steps {
                sh './scripts/verify_monitoring.sh staging http://prometheus:9090'
            }
        }
        stage('Approval gate') {
            when { branch 'main' }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    script {
                        env.APPROVER = input(
                            message: "Deploy ${IMAGE_NAME}:${IMAGE_TAG} to production?",
                            ok: 'Deploy to production',
                            submitterParameter: 'APPROVER'
                        )
                        echo "Release ${IMAGE_TAG} approved by ${env.APPROVER}"
                    }
                }
            }
        }
        stage('Deploy to Production') {
            when { branch 'main' }
            steps {
                script { env.PRODUCTION_DEPLOYED = 'true' }
                sh './scripts/deploy.sh production ${IMAGE_TAG}'
            }
        }
        stage('Smoke test (production)') {
            when { branch 'main' }
            steps {
                sh './scripts/smoke_test.sh http://app-production:5000'
            }
        }
    }
    post {
        always {
            sh 'docker rm -f ${CONTAINER_NAME} || true'
        }
        failure {
            script {
                if (env.PRODUCTION_DEPLOYED == 'true') {
                    sh './scripts/rollback.sh production'
                } else if (env.STAGING_DEPLOYED == 'true') {
                    sh './scripts/rollback.sh staging'
                }
            }
        }
    }
}
