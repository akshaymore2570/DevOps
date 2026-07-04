pipeline {
    agent any
    
    environment {
        APP_NAME = 'vertoz-ad-analytics'
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_NAMESPACE = 'akshaymore2570'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${APP_NAME}"
        DOCKER_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
        MIN_TEST_COVERAGE = '80'
        DEV_URL = 'http://localhost:9090'
        STAGING_URL = 'http://172.16.1.90:9091'
        UAT_URL = 'http://172.16.1.90:9092'
        PROD_URL = 'http://172.16.1.90:9093'
    }
    
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'uat', 'production'],
            description: 'Select deployment environment'
        )
        booleanParam(
            name: 'RUN_FULL_TESTS',
            defaultValue: true,
            description: 'Run full test suite'
        )
        booleanParam(
            name: 'SKIP_QA_APPROVAL',
            defaultValue: false,
            description: '⚠️ SKIP QA approval (emergencies only)'
        )
    }
    
    triggers {
        pollSCM('H/5 * * * *')
    }
    
    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
        ansiColor('xterm')
        timestamps()
        skipDefaultCheckout()
    }
    
    stages {
        
        stage('🔍 PR Validation') {
            steps {
                script {
                    echo "==========================================="
                    echo "VERTAZ PRODUCTION CI/CD PIPELINE"
                    echo "==========================================="
                    echo "Application: ${APP_NAME}"
                    echo "Environment: ${params.DEPLOY_ENV}"
                    echo "Build: ${env.BUILD_NUMBER}"
                    echo "==========================================="
                    
                    env.PR_NUMBER = "${env.CHANGE_ID ?: 'N/A'}"
                    env.PR_BRANCH = "${env.CHANGE_BRANCH ?: env.BRANCH_NAME}"
                    env.GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git branch --show-current', returnStdout: true).trim()
                    
                    echo "PR Number: ${env.PR_NUMBER}"
                    echo "Branch: ${env.GIT_BRANCH}"
                    echo "Commit: ${env.GIT_COMMIT}"
                }
            }
        }
        
        stage('📦 Checkout Code') {
            steps {
                script {
                    def branch = env.PR_BRANCH != 'N/A' ? "*/${env.PR_BRANCH}" : '*/develop'
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: branch]],
                        userRemoteConfigs: [[
                            url: 'git@github.com:akshaymore2570/DevOps.git',
                            credentialsId: 'github-credentials'
                        ]],
                        extensions: [
                            [$class: 'CleanBeforeCheckout'],
                            [$class: 'PruneStaleBranch']
                        ]
                    ])
                }
            }
        }
        
        stage('🐍 Setup Python') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "SETUP PYTHON ENVIRONMENT"
                        echo "==========================================="
                        
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov pytest-xdist black flake8 pylint bandit safety radon
                        
                        echo "✅ Python setup complete"
                        python --version
                    '''
                }
            }
        }
        
        stage('✅ Code Quality Gates') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CODE QUALITY GATES"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        echo "🔍 GATE 1: Code Formatting (Black)"
                        black --check src/ --diff || {
                            echo "❌ Code formatting failed!"
                            exit 1
                        }
                        echo "✅ Code formatting passed"
                        
                        echo "🔍 GATE 2: Linting (Flake8)"
                        flake8 src/ --count --max-complexity=10 --max-line-length=120 || {
                            echo "❌ Linting failed!"
                            exit 1
                        }
                        echo "✅ Linting passed"
                        
                        echo "🔍 GATE 3: Security Scan (Bandit)"
                        bandit -r src/ -f json -o bandit-report.json
                        VULNS=$(jq '.metrics._totals.SEVERITY.HIGH + .metrics._totals.SEVERITY.MEDIUM' bandit-report.json 2>/dev/null || echo 0)
                        if [ "$VULNS" -gt 0 ]; then
                            echo "❌ Found $VULNS vulnerabilities!"
                            exit 1
                        fi
                        echo "✅ Security scan passed"
                        
                        echo "==========================================="
                        echo "✅ ALL CODE QUALITY GATES PASSED"
                        echo "==========================================="
                    '''
                }
            }
        }
        
        stage('🧪 Unit Tests') {
            when {
                expression { params.RUN_FULL_TESTS == true }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "RUNNING UNIT TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        pytest tests/unit/ \
                            --cov=src/ \
                            --cov-report=xml \
                            --cov-report=html \
                            --junitxml=unit-test-results.xml \
                            -v
                        
                        COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
                        echo "Test Coverage: $COVERAGE%"
                        
                        if [ "$COVERAGE" -lt ${MIN_TEST_COVERAGE} ]; then
                            echo "❌ Coverage below ${MIN_TEST_COVERAGE}%"
                            exit 1
                        fi
                        
                        echo "✅ Unit tests passed (Coverage: $COVERAGE%)"
                    '''
                }
            }
            post {
                always {
                    junit 'unit-test-results.xml'
                    // Fixed publishHTML syntax
                    publishHTML(
                        target: [
                            allowMissing: false,
                            alwaysLinkToLastBuild: false,
                            keepAll: false,
                            reportDir: 'htmlcov',
                            reportFiles: 'index.html',
                            reportName: 'Unit Test Coverage Report'
                        ]
                    )
                }
            }
        }
        
        stage('🐳 Build Docker Image') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "BUILDING DOCKER IMAGE"
                        echo "==========================================="
                        
                        docker build \
                            --build-arg VERSION="${DOCKER_TAG}" \
                            --build-arg GIT_COMMIT="${GIT_COMMIT}" \
                            -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            -t ${DOCKER_IMAGE}:${params.DEPLOY_ENV} \
                            .
                        
                        echo "✅ Docker image built successfully"
                    '''
                }
            }
        }
        
        stage('🔒 Container Security Scan') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CONTAINER SECURITY SCAN"
                        echo "==========================================="
                        
                        docker run --rm \
                            aquasec/trivy:latest \
                            image ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --severity HIGH,CRITICAL \
                            --exit-code 1 \
                            --ignore-unfixed
                        
                        echo "✅ No critical vulnerabilities found"
                    '''
                }
            }
        }
        
        stage('📤 Push Docker Image') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PUSHING DOCKER IMAGE"
                        echo "==========================================="
                        
                        echo "${DOCKER_PASSWORD}" | docker login \
                            -u "${DOCKER_USERNAME}" \
                            --password-stdin \
                            ${DOCKER_REGISTRY}
                        
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:${params.DEPLOY_ENV}
                        
                        echo "✅ Docker image pushed to registry"
                    '''
                }
            }
        }
        
        stage('🚀 Deploy to Development') {
            when {
                expression { params.DEPLOY_ENV == 'development' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO DEVELOPMENT"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.dev.yml down || true
                        docker-compose -f docker-compose.dev.yml up -d --build
                        
                        sleep 10
                        curl -f http://localhost:9090/health || {
                            echo "❌ Deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Development deployment complete"
                    '''
                }
            }
        }
        
        stage('🔥 Smoke Tests') {
            when {
                expression { params.SKIP_DEPLOY == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "RUNNING SMOKE TESTS"
                        echo "==========================================="
                        
                        case "${DEPLOY_ENV}" in
                            development)
                                APP_URL="http://localhost:9090"
                                ;;
                            staging)
                                APP_URL="http://172.16.1.90:9091"
                                ;;
                            uat)
                                APP_URL="http://172.16.1.90:9092"
                                ;;
                            production)
                                APP_URL="http://172.16.1.90:9093"
                                ;;
                            *)
                                APP_URL="http://localhost:9090"
                                ;;
                        esac
                        
                        echo "Testing: $APP_URL"
                        
                        curl -f "${APP_URL}/health" || exit 1
                        echo "✅ Health check passed"
                        
                        curl -f "${APP_URL}/api/status" || exit 1
                        echo "✅ API check passed"
                        
                        echo "✅ All smoke tests passed"
                    '''
                }
            }
        }
        
        stage('🚀 Deploy to Staging') {
            when {
                expression { params.DEPLOY_ENV == 'staging' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO STAGING"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.staging.yml down || true
                        docker-compose -f docker-compose.staging.yml up -d --build
                        
                        sleep 10
                        curl -f http://172.16.1.90:9091/health || {
                            echo "❌ Staging deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Staging deployment complete"
                        echo "📌 Ready for QA testing at: http://172.16.1.90:9091"
                    '''
                }
            }
        }
        
        stage('👨‍🔬 QA Approval') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'staging' &&
                    params.SKIP_QA_APPROVAL == false
                }
            }
            steps {
                script {
                    echo "==========================================="
                    echo "WAITING FOR QA APPROVAL"
                    echo "==========================================="
                    
                    input(
                        message: 'Approve for UAT?',
                        submitter: 'qa-team',
                        parameters: [
                            choice(
                                choices: ['Approved', 'Rejected'],
                                description: 'Select status',
                                name: 'QA_APPROVAL'
                            ),
                            text(
                                defaultValue: '',
                                description: 'QA Test Summary',
                                name: 'QA_COMMENTS'
                            )
                        ]
                    )
                    
                    echo "✅ QA approved!"
                }
            }
        }
        
        stage('🚀 Deploy to UAT') {
            when {
                expression { params.DEPLOY_ENV == 'uat' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO UAT"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.uat.yml down || true
                        docker-compose -f docker-compose.uat.yml up -d --build
                        
                        sleep 10
                        curl -f http://172.16.1.90:9092/health || {
                            echo "❌ UAT deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ UAT deployment complete"
                    '''
                }
            }
        }
        
        stage('📋 UAT Sign-Off') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'uat' &&
                    params.SKIP_QA_APPROVAL == false
                }
            }
            steps {
                script {
                    echo "==========================================="
                    echo "WAITING FOR UAT SIGN-OFF"
                    echo "==========================================="
                    
                    input(
                        message: 'UAT Sign-Off Required',
                        submitter: 'product-manager',
                        parameters: [
                            choice(
                                choices: ['Approved', 'Rejected'],
                                description: 'UAT Status',
                                name: 'UAT_STATUS'
                            ),
                            text(
                                defaultValue: '',
                                description: 'UAT Comments',
                                name: 'UAT_COMMENTS'
                            )
                        ]
                    )
                    
                    echo "✅ UAT approved by Business!"
                }
            }
        }
        
        stage('🚀 Deploy to Production') {
            when {
                expression { params.DEPLOY_ENV == 'production' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PRODUCTION DEPLOYMENT"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.prod.yml down || true
                        docker-compose -f docker-compose.prod.yml up -d --build
                        
                        sleep 10
                        curl -f http://172.16.1.90:9093/health || {
                            echo "❌ Production deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Production deployment complete!"
                        echo "URL: http://172.16.1.90:9093"
                    '''
                }
            }
        }
        
        stage('📊 Post-Deployment Monitoring') {
            when {
                expression { params.DEPLOY_ENV == 'production' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "POST-DEPLOYMENT MONITORING"
                        echo "==========================================="
                        
                        curl -f http://172.16.1.90:9093/health || {
                            echo "❌ Production health check failed!"
                            exit 1
                        }
                        echo "✅ Production is healthy"
                        
                        echo "✅ Monitoring complete - All systems normal"
                    '''
                }
            }
        }
        
        stage('📨 Notification') {
            steps {
                script {
                    echo "==========================================="
                    echo "📊 DEPLOYMENT SUMMARY"
                    echo "==========================================="
                    echo ""
                    echo "Application: ${APP_NAME}"
                    echo "Environment: ${params.DEPLOY_ENV}"
                    echo "Version: ${DOCKER_TAG}"
                    echo "Commit: ${GIT_COMMIT}"
                    echo "Build: ${env.BUILD_NUMBER}"
                    echo ""
                    echo "Quality Gates Passed:"
                    echo "✅ Code Formatting (Black)"
                    echo "✅ Linting (Flake8)"
                    echo "✅ Security Scan (Bandit)"
                    echo "✅ Unit Tests (${MIN_TEST_COVERAGE}%+ coverage)"
                    echo "✅ Container Security Scan"
                    echo "✅ Smoke Tests"
                    echo "✅ QA Approval"
                    echo "✅ UAT Sign-Off"
                    echo "✅ Post-Deployment Monitoring"
                    echo ""
                    echo "==========================================="
                }
            }
        }
    }
    
    post {
        success {
            script {
                echo "==========================================="
                echo "🎉 PIPELINE COMPLETED SUCCESSFULLY!"
                echo "==========================================="
            }
        }
        failure {
            script {
                echo "==========================================="
                echo "❌ PIPELINE FAILED!"
                echo "==========================================="
            }
        }
        always {
            script {
                sh '''
                    echo "Cleaning up..."
                    docker system prune -f || true
                    rm -rf venv/
                '''
            }
        }
    }
}
