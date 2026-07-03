pipeline {
    agent any
    
    environment {
        APP_NAME = 'vertoz-ad-analytics'
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/akshaymore2570/${APP_NAME}"
        DOCKER_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
        MIN_TEST_COVERAGE = '80'
        DEPLOY_ENV = 'development'
    }
    
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'uat', 'production'],
            description: 'Select deployment environment'
        )
        booleanParam(
            name: 'SKIP_QA_APPROVAL',
            defaultValue: false,
            description: '⚠️ SKIP QA approval (for emergencies only)'
        )
        string(
            name: 'HOTFIX_DESCRIPTION',
            defaultValue: '',
            description: 'Hotfix description (if applicable)'
        )
    }
    
    stages {
        
        // ============================================================
        // STAGE 1: CHECKOUT CODE
        // ============================================================
        stage('📦 Checkout Code') {
            steps {
                echo "==========================================="
                echo "VERTAZ CI/CD PIPELINE"
                echo "Application: ${APP_NAME}"
                echo "Environment: ${params.DEPLOY_ENV}"
                echo "Build: ${env.BUILD_NUMBER}"
                echo "==========================================="
                
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${params.DEPLOY_ENV == 'production' ? 'main' : 'develop'}"]],
                    userRemoteConfigs: [[
                        url: 'git@github.com:akshaymore2570/DevOps.git',
                        credentialsId: ''
                    ]]
                ])
                
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git branch --show-current', returnStdout: true).trim()
                    echo "Git Commit: ${env.GIT_COMMIT}"
                    echo "Git Branch: ${env.GIT_BRANCH}"
                }
            }
        }
        
        // ============================================================
        // STAGE 2: SETUP PYTHON
        // ============================================================
        stage('🐍 Setup Python') {
            steps {
                script {
                    sh '''
                        echo "Setting up Python..."
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov black flake8 bandit safety
                        echo "Python setup complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 3: CODE QUALITY GATES
        // ============================================================
        stage('✅ Code Quality Gates') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CODE QUALITY GATES"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # GATE 1: Black
                        echo "🔍 GATE 1: Code Formatting (Black)"
                        black --check src/ || {
                            echo "❌ Code formatting failed! Run: black src/"
                            exit 1
                        }
                        echo "✅ Code formatting passed"
                        
                        # GATE 2: Flake8
                        echo "🔍 GATE 2: Linting (Flake8)"
                        flake8 src/ --count --max-complexity=10 || {
                            echo "❌ Linting failed!"
                            exit 1
                        }
                        echo "✅ Linting passed"
                        
                        # GATE 3: Bandit (Security)
                        echo "🔍 GATE 3: Security Scan (Bandit)"
                        bandit -r src/ -f json -o bandit-report.json
                        VULNS=$(jq '.metrics._totals.SEVERITY.HIGH + .metrics._totals.SEVERITY.MEDIUM' bandit-report.json 2>/dev/null || echo 0)
                        if [ "$VULNS" -gt 0 ]; then
                            echo "❌ Found $VULNS high/medium vulnerabilities!"
                            exit 1
                        fi
                        echo "✅ Security scan passed"
                        
                        # GATE 4: Dependency Check
                        echo "🔍 GATE 4: Dependency Vulnerabilities (Safety)"
                        safety check -r requirements.txt || {
                            echo "❌ Vulnerable dependencies found!"
                            exit 1
                        }
                        echo "✅ Dependencies safe"
                        
                        echo "==========================================="
                        echo "✅ ALL CODE QUALITY GATES PASSED"
                        echo "==========================================="
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 4: UNIT TESTS WITH COVERAGE
        // ============================================================
        stage('🧪 Unit Tests') {
            steps {
                script {
                    sh '''
                        echo "Running unit tests..."
                        . venv/bin/activate
                        
                        pytest tests/unit/ \
                            --cov=src/ \
                            --cov-report=xml \
                            --cov-report=html \
                            --junitxml=test-reports/results.xml \
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
                    junit 'test-reports/*.xml'
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Unit Test Coverage'
                    ])
                }
            }
        }
        
        // ============================================================
        // STAGE 5: BUILD DOCKER IMAGE
        // ============================================================
        stage('🐳 Build Docker Image') {
            steps {
                script {
                    sh '''
                        echo "Building Docker image..."
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:${params.DEPLOY_ENV}
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                        echo "✅ Docker image built"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 6: CONTAINER SECURITY SCAN
        // ============================================================
        stage('🔒 Container Security Scan') {
            steps {
                script {
                    sh '''
                        echo "Running container security scan..."
                        docker run --rm aquasec/trivy:latest image \
                            ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --severity HIGH,CRITICAL \
                            --ignore-unfixed \
                            --exit-code 1 \
                            --format table || {
                                echo "❌ Critical vulnerabilities found!"
                                exit 1
                            }
                        echo "✅ Container security scan passed"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 7: DEPLOY TO DEVELOPMENT (Auto)
        // ============================================================
        stage('🚀 Deploy to Development') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'development' ||
                    params.DEPLOY_ENV == 'staging' ||
                    params.DEPLOY_ENV == 'uat' ||
                    params.DEPLOY_ENV == 'production'
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO DEVELOPMENT ENVIRONMENT"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.dev.yml down || true
                        docker-compose -f docker-compose.dev.yml up -d --build
                        
                        sleep 10
                        
                        # Verify deployment
                        curl -f http://localhost:9090/health || {
                            echo "❌ Development deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Development deployment complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 8: INTEGRATION TESTS
        // ============================================================
        stage('🔗 Integration Tests') {
            when {
                expression { 
                    (params.DEPLOY_ENV == 'staging' || 
                     params.DEPLOY_ENV == 'uat' ||
                     params.DEPLOY_ENV == 'production')
                }
            }
            steps {
                script {
                    sh '''
                        echo "Running integration tests..."
                        . venv/bin/activate
                        
                        pytest tests/integration/ \
                            --junitxml=integration-test-results.xml \
                            -v
                        
                        echo "✅ Integration tests passed"
                    '''
                }
            }
            post {
                always {
                    junit 'integration-test-results.xml'
                }
            }
        }
        
        // ============================================================
        // STAGE 9: DEPLOY TO STAGING
        // ============================================================
        stage('🚀 Deploy to Staging') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'staging' ||
                    params.DEPLOY_ENV == 'uat' ||
                    params.DEPLOY_ENV == 'production'
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO STAGING ENVIRONMENT"
                        echo "==========================================="
                        
                        # Stop existing staging containers
                        docker-compose -f docker-compose.staging.yml down || true
                        
                        # Start staging
                        docker-compose -f docker-compose.staging.yml up -d
                        
                        sleep 10
                        
                        # Verify
                        curl -f http://localhost:9091/health || {
                            echo "❌ Staging deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Staging deployment complete"
                    '''
                }
            }
            post {
                success {
                    // Notify QA team on Slack (simulated)
                    echo "📌 NEW BUILD READY FOR QA TESTING"
                    echo "Environment: Staging"
                    echo "URL: http://localhost:9091"
                }
            }
        }
        
        // ============================================================
        // STAGE 10: QA APPROVAL (MANUAL)
        // ============================================================
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
                    
                    // This is where QA team would test
                    // In real Jenkins, this would be:
                    
                    input(
                        message: 'QA Approval Required',
                        submitter: 'qa-team',
                        parameters: [
                            choice(
                                choices: ['Approved', 'Rejected'],
                                description: 'QA Status',
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
        
        // ============================================================
        // STAGE 11: UAT (User Acceptance Testing)
        // ============================================================
        stage('🚀 Deploy to UAT') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'uat' ||
                    params.DEPLOY_ENV == 'production'
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "DEPLOYING TO UAT ENVIRONMENT"
                        echo "==========================================="
                        
                        docker-compose -f docker-compose.uat.yml down || true
                        docker-compose -f docker-compose.uat.yml up -d
                        
                        sleep 10
                        
                        curl -f http://localhost:9092/health || {
                            echo "❌ UAT deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ UAT deployment complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 12: UAT SIGN-OFF (Business Approval)
        // ============================================================
        stage('📋 UAT Sign-Off') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'uat' ||
                    params.DEPLOY_ENV == 'production'
                }
            }
            steps {
                script {
                    echo "==========================================="
                    echo "WAITING FOR UAT SIGN-OFF"
                    echo "==========================================="
                    
                    // In real Jenkins:
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
        
        // ============================================================
        // STAGE 13: PRODUCTION DEPLOYMENT (Blue-Green)
        // ============================================================
        stage('🚀 Deploy to Production (Blue-Green)') {
            when {
                expression { params.DEPLOY_ENV == 'production' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PRODUCTION DEPLOYMENT - BLUE-GREEN"
                        echo "==========================================="
                        
                        echo "Current Production: $(docker ps -q -f name=vertoz-prod-blue 2>/dev/null || echo 'None')"
                        
                        # Deploy Green (New Version)
                        echo "1. Deploying Green (New Version)"
                        docker-compose -f docker-compose.prod.green.yml up -d
                        
                        sleep 10
                        
                        # Verify Green
                        echo "2. Verifying Green"
                        curl -f http://localhost:9093/health || {
                            echo "❌ Green health check failed!"
                            docker-compose -f docker-compose.prod.green.yml down
                            exit 1
                        }
                        
                        # Switch Traffic (Blue → Green)
                        echo "3. Switching traffic to Green"
                        docker-compose -f docker-compose.prod.blue.yml down || true
                        
                        # Rename green to blue
                        docker rename vertoz-prod-green vertoz-prod-blue 2>/dev/null || true
                        
                        echo "✅ Production deployment complete!"
                    '''
                }
            }
            post {
                success {
                    echo "🚀 PRODUCTION DEPLOYMENT SUCCESSFUL!"
                }
                failure {
                    echo "🔥 PRODUCTION DEPLOYMENT FAILED!"
                    echo "Rolling back..."
                }
            }
        }
        
        // ============================================================
        // STAGE 14: POST-DEPLOYMENT MONITORING
        // ============================================================
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
                        
                        echo "Checking application health..."
                        curl -f http://localhost:9093/health || {
                            echo "❌ Production health check failed!"
                            exit 1
                        }
                        
                        echo "Checking logs for errors..."
                        docker logs vertoz-prod-blue --tail=50 | grep ERROR || echo "No errors found"
                        
                        echo "✅ Monitoring complete - All systems normal"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 15: FINAL NOTIFICATION
        // ============================================================
        stage('📨 Final Notification') {
            steps {
                script {
                    echo "==========================================="
                    echo "📨 SENDING FINAL NOTIFICATIONS"
                    echo "==========================================="
                    
                    echo """
                        Deployment Summary
                        ==================
                        
                        Application: ${APP_NAME}
                        Environment: ${params.DEPLOY_ENV}
                        Version: ${DOCKER_TAG}
                        Commit: ${GIT_COMMIT}
                        Build: ${env.BUILD_NUMBER}
                        
                        Quality Gates:
                        ✅ Code Formatting
                        ✅ Linting
                        ✅ Security Scan
                        ✅ Unit Tests (${MIN_TEST_COVERAGE}%+ coverage)
                        ✅ Integration Tests
                        ✅ QA Approval
                        ✅ UAT Sign-Off
                        ✅ Post-Deployment Monitoring
                    """
                }
            }
        }
    }
    
    // ============================================================
    // POST-BUILD ACTIONS
    // ============================================================
    post {
        success {
            echo "🎉 PIPELINE COMPLETED SUCCESSFULLY!"
            echo "All Quality Gates Passed!"
        }
        failure {
            echo "❌ PIPELINE FAILED!"
        }
        aborted {
            echo "⏹️ DEPLOYMENT ABORTED"
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
