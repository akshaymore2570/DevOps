cd /mnt/vertoz-pipeline

cat > Jenkinsfile << 'EOF'
pipeline {
    agent any
    
    environment {
        APP_NAME = 'vertoz-ad-analytics'
        DOCKER_IMAGE = "vertoz-ad-analytics"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        MIN_TEST_COVERAGE = '60'
    }
    
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'production'],
            description: 'Select deployment environment'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run unit tests'
        )
        booleanParam(
            name: 'SKIP_DEPLOY',
            defaultValue: false,
            description: 'Skip deployment'
        )
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo "==========================================="
                echo "VERTAZ CI/CD PIPELINE"
                echo "Application: ${APP_NAME}"
                echo "Build: ${env.BUILD_NUMBER}"
                echo "==========================================="
                
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    userRemoteConfigs: [[
                        url: 'git@github.com:akshaymore2570/DevOps.git',
                        credentialsId: ''
                    ]]
                ])
                
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Git Commit: ${env.GIT_COMMIT}"
                }
            }
        }
        
        stage('Setup Python') {
            steps {
                script {
                    sh '''
                        echo "Setting up Python..."
                        python3 -m venv venv
                        source venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov black flake8
                        echo "Python setup complete"
                    '''
                }
            }
        }
        
        stage('Code Quality') {
            steps {
                script {
                    sh '''
                        echo "Running code quality checks..."
                        source venv/bin/activate
                        black --check src/ || exit 1
                        echo "Code formatting passed"
                        flake8 src/ --count --max-complexity=10 || exit 1
                        echo "Linting passed"
                    '''
                }
            }
        }
        
        stage('Unit Tests') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                script {
                    sh '''
                        echo "Running unit tests..."
                        source venv/bin/activate
                        pytest tests/unit/ --cov=src/ --cov-report=xml --cov-report=term --junitxml=test-reports/results.xml -v || true
                        COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
                        echo "Coverage: $COVERAGE%"
                        echo "Unit tests completed"
                    '''
                }
            }
            post {
                always {
                    junit 'test-reports/*.xml'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    sh '''
                        echo "Building Docker image..."
                        docker build -t ${APP_NAME}:${DOCKER_TAG} .
                        docker tag ${APP_NAME}:${DOCKER_TAG} ${APP_NAME}:latest
                        echo "Docker image built"
                    '''
                }
            }
        }
        
        stage('Deploy Locally') {
            when {
                expression { params.SKIP_DEPLOY == false }
            }
            steps {
                script {
                    sh '''
                        echo "Deploying with Docker Compose..."
                        docker-compose down || true
                        docker-compose up -d --build
                        sleep 10
                        echo "Deployment complete"
                    '''
                }
            }
        }
        
        stage('Smoke Tests') {
            when {
                expression { params.SKIP_DEPLOY == false }
            }
            steps {
                script {
                    sh '''
                        echo "Running smoke tests..."
                        curl -f http://localhost:9090/health || exit 1
                        echo "Health check passed"
                        curl -f http://localhost:9090/api/status || exit 1
                        echo "API check passed"
                        echo "All smoke tests passed"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "PIPELINE COMPLETED SUCCESSFULLY!"
        }
        failure {
            echo "PIPELINE FAILED!"
        }
        always {
            script {
                sh '''
                    echo "Cleaning up..."
                    docker system prune -f || true
                '''
            }
        }
    }
}
EOF

echo "Jenkinsfile updated!"
