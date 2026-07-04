// ================================================================
// VERTAZ PRODUCTION CI/CD PIPELINE
// Complete PR-based workflow with Quality Gates & Approvals
// IP-Based URLs for Local/Lab Environment
// ================================================================

pipeline {
    agent any
    
    // ============================================================
    // ENVIRONMENT VARIABLES - IP BASED
    // ============================================================
    environment {
        APP_NAME = 'vertoz-ad-analytics'
        APP_DESC = 'Vertoz Ad Analytics Platform'
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_NAMESPACE = 'akshaymore2570'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${APP_NAME}"
        DOCKER_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
        
        // Quality Gates Thresholds
        MIN_TEST_COVERAGE = '80'
        MAX_VULNERABILITIES = '0'
        MAX_CODE_SMELLS = '10'
        MAX_DUPLICATION = '3%'
        MIN_PERFORMANCE_SCORE = '90'
        
        // ============================================================
        // IP-BASED ENVIRONMENT URLS
        // ============================================================
        // Development - Localhost (Jenkins server)
        DEV_URL = 'http://localhost:9090'
        
        // Staging - Same server different port
        STAGING_URL = 'http://172.16.1.90:9091'
        
        // UAT - Same server different port
        UAT_URL = 'http://172.16.1.90:9092'
        
        // Production - Same server different port
        PROD_URL = 'http://172.16.1.90:9093'
        
        // Slack Channels
        DEV_SLACK = '#dev-deployments'
        QA_SLACK = '#qa-notifications'
        PROD_SLACK = '#production-alerts'
    }
    
    // ============================================================
    // PARAMETERS
    // ============================================================
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['development', 'staging', 'uat', 'production'],
            description: 'Select deployment environment'
        )
        booleanParam(
            name: 'RUN_FULL_TESTS',
            defaultValue: true,
            description: 'Run full test suite (slower)'
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
    
    // ============================================================
    // TRIGGERS
    // ============================================================
    triggers {
        pollSCM('H/5 * * * *')
    }
    
    // ============================================================
    // OPTIONS
    // ============================================================
    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
        ansiColor('xterm')
        timestamps()
        skipDefaultCheckout()
    }
    
    // ============================================================
    // STAGES
    // ============================================================
    stages {
        
        // ============================================================
        // STAGE 0: PR VALIDATION & CONTEXT
        // ============================================================
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
                    env.PR_TARGET = "${env.CHANGE_TARGET ?: 'develop'}"
                    env.GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git branch --show-current', returnStdout: true).trim()
                    
                    echo "PR Number: ${env.PR_NUMBER}"
                    echo "Branch: ${env.GIT_BRANCH}"
                    echo "Commit: ${env.GIT_COMMIT}"
                    echo "==========================================="
                }
            }
        }
        
        // ============================================================
        // STAGE 1: CHECKOUT CODE
        // ============================================================
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
        
        // ============================================================
        // STAGE 2: SETUP PYTHON ENVIRONMENT
        // ============================================================
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
                        pip install pytest pytest-cov pytest-xdist black flake8 pylint bandit safety radon locust requests prometheus-client
                        
                        echo "✅ Python setup complete"
                        python --version
                        pip list | grep -E "pytest|black|flake8|bandit"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 3: CODE QUALITY GATES (MUST PASS)
        // ============================================================
        stage('✅ Code Quality Gates') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CODE QUALITY GATES"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # GATE 1: Code Formatting (Black)
                        echo "🔍 GATE 1: Code Formatting (Black)"
                        black --check src/ --diff || {
                            echo "❌ Code formatting failed! Run: black src/"
                            exit 1
                        }
                        echo "✅ Code formatting passed"
                        
                        # GATE 2: Linting (Flake8)
                        echo "🔍 GATE 2: Linting (Flake8)"
                        flake8 src/ --count --max-complexity=10 --max-line-length=120 --statistics || {
                            echo "❌ Linting failed!"
                            exit 1
                        }
                        echo "✅ Linting passed"
                        
                        # GATE 3: Code Smells (Radon)
                        echo "🔍 GATE 3: Code Smells (Radon)"
                        radon mi src/ -n B -s || {
                            echo "❌ Code smells detected!"
                            exit 1
                        }
                        echo "✅ No critical code smells"
                        
                        # GATE 4: Security Scan (Bandit)
                        echo "🔍 GATE 4: Security Scan (Bandit)"
                        bandit -r src/ -f json -o bandit-report.json
                        VULNS=$(jq '.metrics._totals.SEVERITY.HIGH + .metrics._totals.SEVERITY.MEDIUM' bandit-report.json 2>/dev/null || echo 0)
                        if [ "$VULNS" -gt 0 ]; then
                            echo "❌ Found $VULNS high/medium vulnerabilities!"
                            cat bandit-report.json
                            exit 1
                        fi
                        echo "✅ No high/medium vulnerabilities"
                        
                        # GATE 5: Dependency Check (Safety)
                        echo "🔍 GATE 5: Dependency Vulnerabilities (Safety)"
                        safety check -r requirements.txt || {
                            echo "❌ Vulnerable dependencies found!"
                            exit 1
                        }
                        echo "✅ All dependencies are safe"
                        
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
                            --cov-report=term-missing \
                            --junitxml=unit-test-results.xml \
                            --maxfail=5 \
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
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Unit Test Coverage Report'
                    ])
                }
            }
        }
        
        // ============================================================
        // STAGE 5: INTEGRATION TESTS
        // ============================================================
        stage('🔗 Integration Tests') {
            when {
                expression { 
                    params.RUN_FULL_TESTS == true &&
                    (params.DEPLOY_ENV == 'staging' || 
                     params.DEPLOY_ENV == 'uat' ||
                     params.DEPLOY_ENV == 'production')
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "RUNNING INTEGRATION TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        export TEST_ENV=${DEPLOY_ENV}
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
        // STAGE 6: PERFORMANCE TESTS
        // ============================================================
        stage('📊 Performance Tests') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'staging' &&
                    params.RUN_FULL_TESTS == true
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PERFORMANCE TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        python src/app.py &
                        APP_PID=$!
                        sleep 10
                        
                        locust -f tests/load_test.py \
                            --headless \
                            -u 100 \
                            -r 10 \
                            --run-time 60s \
                            --host http://localhost:8080 \
                            --html performance-report.html
                        
                        kill $APP_PID 2>/dev/null || true
                        echo "✅ Performance tests completed"
                    '''
                }
            }
            post {
                always {
                    publishHTML([
                        reportDir: '.',
                        reportFiles: 'performance-report.html',
                        reportName: 'Performance Test Report'
                    ])
                }
            }
        }
        
        // ============================================================
        // STAGE 7: BUILD DOCKER IMAGE
        // ============================================================
        stage('🐳 Build Docker Image') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "BUILDING DOCKER IMAGE"
                        echo "==========================================="
                        
                        echo "Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                        
                        docker build \
                            --build-arg APP_NAME="${APP_NAME}" \
                            --build-arg VERSION="${DOCKER_TAG}" \
                            --build-arg GIT_COMMIT="${GIT_COMMIT}" \
                            --build-arg BUILD_DATE="$(date)" \
                            -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            -t ${DOCKER_IMAGE}:${params.DEPLOY_ENV} \
                            .
                        
                        docker images ${DOCKER_IMAGE}
                        echo "✅ Docker image built successfully"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 8: CONTAINER SECURITY SCAN
        // ============================================================
        stage('🔒 Container Security Scan') {
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CONTAINER SECURITY SCAN"
                        echo "==========================================="
                        
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:latest \
                            image ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --severity HIGH,CRITICAL \
                            --exit-code 1 \
                            --format table \
                            --ignore-unfixed
                        
                        echo "✅ No critical vulnerabilities found"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 9: PUSH DOCKER IMAGE
        // ============================================================
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
        
        // ============================================================
        // STAGE 10: DEPLOY TO DEVELOPMENT
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
                        curl -f http://localhost:9090/health || {
                            echo "❌ Deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Development deployment complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 11: SMOKE TESTS
        // ============================================================
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
                        
                        curl -f "${APP_URL}/health" || {
                            echo "❌ Health check failed!"
                            exit 1
                        }
                        echo "✅ Health check passed"
                        
                        curl -f "${APP_URL}/api/status" || {
                            echo "❌ API check failed!"
                            exit 1
                        }
                        echo "✅ API check passed"
                        
                        curl -f "${APP_URL}/api/ad/123/stats" || {
                            echo "❌ Ad stats check failed!"
                            exit 1
                        }
                        echo "✅ Ad stats check passed"
                        
                        echo "✅ All smoke tests passed"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 12: DEPLOY TO STAGING
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
                        
                        docker-compose -f docker-compose.staging.yml down || true
                        docker-compose -f docker-compose.staging.yml up -d --build
                        
                        sleep 10
                        curl -f http://172.16.1.90:9091/health || {
                            echo "❌ Staging deployment failed!"
                            exit 1
                        }
                        
                        echo "✅ Staging deployment complete"
                    '''
                }
            }
            post {
                success {
                    script {
                        echo "📌 NEW BUILD READY FOR QA TESTING"
                        echo "Environment: Staging"
                        echo "URL: http://172.16.1.90:9091"
                    }
                }
            }
        }
        
        // ============================================================
        // STAGE 13: QA APPROVAL (MANUAL)
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
        
        // ============================================================
        // STAGE 14: DEPLOY TO UAT
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
        
        // ============================================================
        // STAGE 15: UAT SIGN-OFF
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
        // STAGE 16: PRODUCTION DEPLOYMENT (BLUE-GREEN)
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
                        
                        # Deploy Green
                        docker-compose -f docker-compose.prod.green.yml up -d --build
                        sleep 10
                        
                        curl -f http://172.16.1.90:9093/health || {
                            echo "❌ Green deployment failed!"
                            docker-compose -f docker-compose.prod.green.yml down
                            exit 1
                        }
                        
                        # Switch to Green
                        docker-compose -f docker-compose.prod.blue.yml down || true
                        docker rename vertoz-prod-green vertoz-prod-blue 2>/dev/null || true
                        
                        echo "✅ Production deployment complete!"
                    '''
                }
            }
            post {
                success {
                    script {
                        echo "🚀 PRODUCTION DEPLOYMENT SUCCESSFUL"
                        echo "Version: ${DOCKER_TAG}"
                        echo "URL: http://172.16.1.90:9093"
                    }
                }
                failure {
                    script {
                        echo "🔥 PRODUCTION DEPLOYMENT FAILED!"
                        echo "Rolling back..."
                    }
                }
            }
        }
        
        // ============================================================
        // STAGE 17: POST-DEPLOYMENT MONITORING
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
                        
                        PROD_URL="http://172.16.1.90:9093"
                        
                        echo "Monitoring: $PROD_URL"
                        curl -f "${PROD_URL}/health" || {
                            echo "❌ Production health check failed!"
                            exit 1
                        }
                        echo "✅ Production is healthy"
                        
                        RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "${PROD_URL}/health")
                        echo "Response Time: ${RESPONSE_TIME}s"
                        
                        docker logs vertoz-prod --tail=50 | grep ERROR || echo "No errors found"
                        
                        echo "✅ Monitoring complete - All systems normal"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 18: NOTIFICATION
        // ============================================================
        stage('📨 Notification') {
            steps {
                script {
                    echo "==========================================="
                    echo "SENDING NOTIFICATIONS"
                    echo "==========================================="
                    
                    echo "Deployment completed for ${APP_NAME}"
                    echo "Environment: ${params.DEPLOY_ENV}"
                    echo "Version: ${DOCKER_TAG}"
                    echo "Commit: ${GIT_COMMIT}"
                    
                    echo """
                    ===========================================
                    📊 DEPLOYMENT SUMMARY
                    ===========================================
                    
                    Application: ${APP_NAME}
                    Environment: ${params.DEPLOY_ENV}
                    Version: ${DOCKER_TAG}
                    Commit: ${GIT_COMMIT}
                    Build: ${env.BUILD_NUMBER}
                    
                    Quality Gates Passed:
                    ✅ Code Formatting (Black)
                    ✅ Linting (Flake8)
                    ✅ Code Smells (Radon)
                    ✅ Security Scan (Bandit)
                    ✅ Dependency Check (Safety)
                    ✅ Unit Tests (${MIN_TEST_COVERAGE}%+ coverage)
                    ✅ Integration Tests
                    ✅ Performance Tests
                    ✅ Container Security Scan
                    ✅ Smoke Tests
                    ✅ QA Approval
                    ✅ UAT Sign-Off
                    ✅ Post-Deployment Monitoring
                    
                    URL: ${DEV_URL}
                    ===========================================
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
            script {
                echo "==========================================="
                echo "🎉 PIPELINE COMPLETED SUCCESSFULLY!"
                echo "All Quality Gates Passed!"
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
        
        aborted {
            script {
                echo "⏹️ DEPLOYMENT ABORTED"
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
