pipeline {
    agent any
    environment {
        IMAGE_NAME = 'system-health-dashboard'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        CONTAINER_NAME = "health-check-${env.BUILD_NUMBER}"
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
    }
    post {
        always {
            sh 'docker rm -f ${CONTAINER_NAME} || true'
        }
    }
}