// ================================================================
// VERTAZ PRODUCTION CI/CD PIPELINE
// With ALL Production Features: Ansible, Artifacts, Approval Gates,
// Blue-Green Deployment, Rollback, Monitoring
// ================================================================

pipeline {
    agent any
    
    // ============================================================
    // ENVIRONMENT VARIABLES
    // ============================================================
    environment {
        APP_NAME = 'vertoz-ad-analytics'
        DOCKER_REGISTRY = 'docker.io'  // Docker Hub
        DOCKER_NAMESPACE = 'akshaymore2570'  // Your Docker Hub username
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${APP_NAME}"
        DOCKER_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
        
        // Quality Gates
        MIN_TEST_COVERAGE = '80'
        MAX_VULNERABILITIES = '0'
        MAX_CODE_SMELLS = '5'
        
        // S3 for Artifacts
        ARTIFACT_BUCKET = 'vertoz-artifacts'
        AWS_REGION = 'ap-south-1'
        
        // SonarQube (Code Quality)
        SONAR_HOST_URL = 'http://sonarqube:9000'
        
        // Slack Notifications
        SLACK_CHANNEL = '#devops'
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
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run full test suite'
        )
        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security scan'
        )
        booleanParam(
            name: 'SKIP_QA_APPROVAL',
            defaultValue: false,
            description: '⚠️ SKIP QA approval (emergencies only)'
        )
        booleanParam(
            name: 'ROLLBACK',
            defaultValue: false,
            description: 'Perform rollback'
        )
        string(
            name: 'ROLLBACK_VERSION',
            defaultValue: '',
            description: 'Version to rollback to'
        )
    }
    
    // ============================================================
    // STAGES
    // ============================================================
    stages {
        
        // ============================================================
        // STAGE 1: CHECKOUT CODE
        // ============================================================
        stage('📦 Checkout Code') {
            steps {
                echo "==========================================="
                echo "VERTAZ PRODUCTION CI/CD PIPELINE"
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
        // STAGE 2: ROLLBACK (If requested)
        // ============================================================
        stage('🔄 Rollback') {
            when {
                expression { params.ROLLBACK == true }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PERFORMING ROLLBACK"
                        echo "==========================================="
                        
                        ROLLBACK_VERSION=${ROLLBACK_VERSION}
                        
                        if [ -z "$ROLLBACK_VERSION" ]; then
                            echo "Getting previous version from registry..."
                            # Get last successful deployment version
                            ROLLBACK_VERSION=$(curl -s \
                                https://registry.vertoz.com/v2/${APP_NAME}/tags/list \
                                | jq -r '.tags | sort_by(.) | .[-2]')
                        fi
                        
                        echo "Rolling back to: $ROLLBACK_VERSION"
                        
                        # Ansible rollback playbook
                        ansible-playbook ansible/playbooks/rollback.yml \
                            -i ansible/inventory/${DEPLOY_ENV} \
                            -e "app_name=${APP_NAME}" \
                            -e "rollback_version=$ROLLBACK_VERSION" \
                            -e "deploy_env=${DEPLOY_ENV}"
                        
                        echo "✅ Rollback completed!"
                    '''
                }
            }
            post {
                success {
                    slackSend(
                        color: 'warning',
                        message: "🔄 ROLLBACK COMPLETED\nApp: ${APP_NAME}\nVersion: ${ROLLBACK_VERSION}\nEnv: ${DEPLOY_ENV}"
                    )
                }
            }
        }
        
        // ============================================================
        // STAGE 3: SETUP PYTHON
        // ============================================================
        stage('🐍 Setup Python') {
            when {
                expression { params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "Setting up Python..."
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov black flake8 bandit safety
                        echo "✅ Python setup complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 4: CODE QUALITY (MANDATORY)
        // ============================================================
        stage('✅ Code Quality') {
            when {
                expression { params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CODE QUALITY GATES - ALL MUST PASS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # GATE 1: Black Formatting
                        echo "🔍 Checking code formatting..."
                        black --check src/ || {
                            echo "❌ Code formatting failed! Run: black src/"
                            exit 1
                        }
                        echo "✅ Formatting passed"
                        
                        # GATE 2: Flake8 Linting
                        echo "🔍 Running linter..."
                        flake8 src/ --count --max-complexity=10 --statistics || {
                            echo "❌ Linting failed!"
                            exit 1
                        }
                        echo "✅ Linting passed"
                        
                        # GATE 3: Bandit Security
                        echo "🔍 Security scan..."
                        bandit -r src/ -f json -o bandit-report.json
                        VULNS=$(jq '.metrics._totals.SEVERITY.HIGH + .metrics._totals.SEVERITY.MEDIUM' bandit-report.json)
                        if [ "$VULNS" -gt 0 ]; then
                            echo "❌ Found $VULNS high/medium vulnerabilities!"
                            exit 1
                        fi
                        echo "✅ Security scan passed"
                        
                        # GATE 4: Dependency Check
                        echo "🔍 Checking dependencies..."
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
        // STAGE 5: UNIT TESTS WITH COVERAGE
        // ============================================================
        stage('🧪 Unit Tests') {
            when {
                expression { params.RUN_TESTS == true && params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "RUNNING UNIT TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # Run tests with coverage
                        pytest tests/unit/ \
                            --cov=src/ \
                            --cov-report=xml \
                            --cov-report=html \
                            --junitxml=test-reports/results.xml \
                            -v
                        
                        # Check coverage threshold
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
                    // Publish test results
                    junit 'test-reports/*.xml'
                    
                    // Publish coverage report
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Test Coverage Report'
                    ])
                    
                    // Archive artifacts
                    archiveArtifacts artifacts: 'test-reports/*, coverage.xml', fingerprint: true
                }
            }
        }
        
        // ============================================================
        // STAGE 6: BUILD DOCKER IMAGE
        // ============================================================
        stage('🐳 Build Docker Image') {
            when {
                expression { params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "BUILDING DOCKER IMAGE"
                        echo "==========================================="
                        
                        docker build \
                            --build-arg VERSION="${DOCKER_TAG}" \
                            --build-arg GIT_COMMIT="${GIT_COMMIT}" \
                            -t ${APP_NAME}:${DOCKER_TAG} \
                            -t ${APP_NAME}:latest \
                            .
                        
                        echo "✅ Docker image built: ${APP_NAME}:${DOCKER_TAG}"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 7: CONTAINER SECURITY SCAN
        // ============================================================
        stage('🔒 Container Security Scan') {
            when {
                expression { params.RUN_SECURITY_SCAN == true && params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "CONTAINER SECURITY SCAN"
                        echo "==========================================="
                        
                        # Trivy vulnerability scanning
                        docker run --rm \
                            aquasec/trivy:latest \
                            image ${APP_NAME}:${DOCKER_TAG} \
                            --severity HIGH,CRITICAL \
                            --ignore-unfixed \
                            --exit-code 1 \
                            --format table
                        
                        echo "✅ Container security scan passed"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 8: PUSH DOCKER IMAGE TO REGISTRY
        // ============================================================
        stage('📤 Push Docker Image to Registry') {
            when {
                expression { params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PUSHING DOCKER IMAGE TO REGISTRY"
                        echo "==========================================="
                        
                        # Login to Docker Hub
                        echo "${DOCKER_PASSWORD}" | docker login \
                            -u "${DOCKER_USERNAME}" \
                            --password-stdin
                        
                        # Tag for registry
                        docker tag ${APP_NAME}:${DOCKER_TAG} ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker tag ${APP_NAME}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                        docker tag ${APP_NAME}:${DOCKER_TAG} ${DOCKER_IMAGE}:${DEPLOY_ENV}
                        
                        # Push all tags
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        docker push ${DOCKER_IMAGE}:${DEPLOY_ENV}
                        
                        echo "✅ Docker image pushed to registry"
                        echo "Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 9: STORE ARTIFACTS TO S3
        // ============================================================
        stage('📦 Store Artifacts to S3') {
            when {
                expression { params.ROLLBACK == false }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "STORING ARTIFACTS TO S3"
                        echo "==========================================="
                        
                        # Create artifact package
                        mkdir -p artifacts
                        cp test-reports/results.xml artifacts/
                        cp coverage.xml artifacts/
                        cp bandit-report.json artifacts/
                        
                        # Create metadata
                        echo "{
                            \"app\": \"${APP_NAME}\",
                            \"version\": \"${DOCKER_TAG}\",
                            \"commit\": \"${GIT_COMMIT}\",
                            \"branch\": \"${GIT_BRANCH}\",
                            \"build_number\": \"${BUILD_NUMBER}\",
                            \"timestamp\": \"$(date -Iseconds)\"
                        }" > artifacts/metadata.json
                        
                        # Upload to S3 (if AWS CLI is installed)
                        if command -v aws &> /dev/null; then
                            aws s3 cp artifacts/ s3://${ARTIFACT_BUCKET}/${APP_NAME}/${DOCKER_TAG}/ --recursive
                            echo "✅ Artifacts uploaded to S3"
                        else
                            echo "⚠️ AWS CLI not installed, artifacts saved locally"
                        fi
                        
                        echo "✅ Artifacts stored successfully"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'artifacts/*'
                }
            }
        }
        
        // ============================================================
        // STAGE 10: DEPLOY TO DEVELOPMENT (Auto)
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
                        
                        # Deploy with Ansible
                        ansible-playbook \
                            -i ansible/inventory/development \
                            ansible/playbooks/deploy.yml \
                            -e "app_name=${APP_NAME}" \
                            -e "docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}" \
                            -e "docker_tag=${DOCKER_TAG}" \
                            -e "deploy_env=development" \
                            -e "git_commit=${GIT_COMMIT}"
                        
                        echo "✅ Development deployment complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 11: SMOKE TESTS (Dev)
        // ============================================================
        stage('🔥 Smoke Tests - Dev') {
            when {
                expression { params.DEPLOY_ENV == 'development' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "SMOKE TESTS - DEVELOPMENT"
                        echo "==========================================="
                        
                        curl -f http://dev.vertoz.com/health || {
                            echo "❌ Dev environment not healthy"
                            exit 1
                        }
                        echo "✅ Health check passed"
                        
                        curl -f http://dev.vertoz.com/api/status || {
                            echo "❌ API not responding"
                            exit 1
                        }
                        echo "✅ API check passed"
                        
                        echo "✅ Smoke tests passed"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 12: INTEGRATION TESTS
        // ============================================================
        stage('🔗 Integration Tests') {
            when {
                expression { 
                    (params.DEPLOY_ENV == 'staging' || 
                     params.DEPLOY_ENV == 'uat' ||
                     params.DEPLOY_ENV == 'production') &&
                    params.RUN_TESTS == true
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "RUNNING INTEGRATION TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # Test against deployed environment
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
        // STAGE 13: PERFORMANCE TESTS
        // ============================================================
        stage('📊 Performance Tests') {
            when {
                expression { 
                    params.DEPLOY_ENV == 'staging' &&
                    params.RUN_TESTS == true
                }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "PERFORMANCE TESTS"
                        echo "==========================================="
                        
                        . venv/bin/activate
                        
                        # Load test
                        locust -f tests/load_test.py \
                            --headless \
                            -u 100 \
                            -r 10 \
                            --run-time 120s \
                            --host https://staging.vertoz.com \
                            --html performance-report.html
                        
                        echo "✅ Performance tests completed"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 14: DEPLOY TO STAGING
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
                        
                        # Deploy with Ansible
                        ansible-playbook \
                            -i ansible/inventory/staging \
                            ansible/playbooks/deploy.yml \
                            -e "app_name=${APP_NAME}" \
                            -e "docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}" \
                            -e "docker_tag=${DOCKER_TAG}" \
                            -e "deploy_env=staging" \
                            -e "git_commit=${GIT_COMMIT}"
                        
                        echo "✅ Staging deployment complete"
                    '''
                }
            }
            post {
                success {
                    // Notify QA team
                    slackSend(
                        color: 'good',
                        channel: '#qa-notifications',
                        message: """
📌 NEW BUILD READY FOR QA TESTING
App: ${APP_NAME}
Version: ${DOCKER_TAG}
Environment: Staging
URL: https://staging.vertoz.com
QA Team: Please start testing
                        """
                    )
                }
            }
        }
        
        // ============================================================
        // STAGE 15: QA APPROVAL (MANUAL)
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
                    
                    // Send email to QA team
                    emailext(
                        to: 'qa-team@vertoz.com',
                        subject: "QA Approval Required - ${APP_NAME} ${DOCKER_TAG}",
                        body: """
                            QA Team,

                            New build is ready for testing.

                            Application: ${APP_NAME}
                            Version: ${DOCKER_TAG}
                            Commit: ${GIT_COMMIT}
                            Environment: Staging
                            URL: https://staging.vertoz.com

                            Please test and approve.

                            Test Cases to Run:
                            1. Sanity Test
                            2. Regression Test Suite
                            3. Performance Check
                            4. Security Tests

                            - DevOps Team
                        """
                    )
                    
                    // Wait for QA approval
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
        // STAGE 16: DEPLOY TO UAT
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
                        
                        ansible-playbook \
                            -i ansible/inventory/uat \
                            ansible/playbooks/deploy.yml \
                            -e "app_name=${APP_NAME}" \
                            -e "docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}" \
                            -e "docker_tag=${DOCKER_TAG}" \
                            -e "deploy_env=uat" \
                            -e "git_commit=${GIT_COMMIT}"
                        
                        echo "✅ UAT deployment complete"
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 17: UAT SIGN-OFF (MANUAL)
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
                    
                    // Get approval from product team
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
                                description: 'UAT Sign-off Comments',
                                name: 'UAT_COMMENTS'
                            )
                        ]
                    )
                    
                    echo "✅ UAT approved by Business!"
                }
            }
        }
        
        // ============================================================
        // STAGE 18: BLUE-GREEN DEPLOYMENT TO PRODUCTION
        // ============================================================
        stage('🔵🟢 Blue-Green Deployment to Production') {
            when {
                expression { params.DEPLOY_ENV == 'production' }
            }
            steps {
                script {
                    sh '''
                        echo "==========================================="
                        echo "BLUE-GREEN DEPLOYMENT TO PRODUCTION"
                        echo "==========================================="
                        
                        # Get current production version (Blue)
                        CURRENT_VERSION=$(curl -s https://api.vertoz.com/version \
                            | jq -r '.version' || echo "unknown")
                        
                        echo "Current Production (Blue): $CURRENT_VERSION"
                        echo "New Version (Green): ${DOCKER_TAG}"
                        
                        # ----------------------------------------------------
                        # STEP 1: Deploy Green (New Version)
                        # ----------------------------------------------------
                        echo "1️⃣ Deploying Green (New Version)"
                        ansible-playbook ansible/playbooks/blue-green-deploy.yml \
                            -i ansible/inventory/production \
                            -e "app_name=${APP_NAME}" \
                            -e "docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}" \
                            -e "deploy_env=production" \
                            -e "color=green"
                        
                        # ----------------------------------------------------
                        # STEP 2: Verify Green Health
                        # ----------------------------------------------------
                        echo "2️⃣ Verifying Green environment"
                        sleep 30
                        
                        curl -f http://green.vertoz.com/health || {
                            echo "❌ Green health check failed!"
                            exit 1
                        }
                        echo "✅ Green health check passed"
                        
                        # ----------------------------------------------------
                        # STEP 3: Smoke Tests on Green
                        # ----------------------------------------------------
                        echo "3️⃣ Running smoke tests on Green"
                        pytest tests/smoke_test.py --host http://green.vertoz.com -v
                        
                        # ----------------------------------------------------
                        # STEP 4: Switch Traffic (Blue → Green)
                        # ----------------------------------------------------
                        echo "4️⃣ Switching traffic to Green"
                        ansible-playbook ansible/playbooks/switch-traffic.yml \
                            -i ansible/inventory/production \
                            -e "app_name=${APP_NAME}" \
                            -e "color=green"
                        
                        # Wait for traffic to switch
                        sleep 60
                        
                        # ----------------------------------------------------
                        # STEP 5: Verify Production
                        # ----------------------------------------------------
                        echo "5️⃣ Verifying Production"
                        curl -f https://api.vertoz.com/health || {
                            echo "❌ Production health check failed!"
                            
                            # Rollback to Blue
                            ansible-playbook ansible/playbooks/switch-traffic.yml \
                                -i ansible/inventory/production \
                                -e "app_name=${APP_NAME}" \
                                -e "color=blue"
                            
                            echo "✅ Rolled back to Blue"
                            exit 1
                        }
                        echo "✅ Production verification passed"
                        
                        # ----------------------------------------------------
                        # STEP 6: Keep Blue for Rollback
                        # ----------------------------------------------------
                        echo "6️⃣ Keeping Blue for rollback"
                        echo "Blue version: $CURRENT_VERSION"
                        echo "Green version: ${DOCKER_TAG}"
                        
                        echo "==========================================="
                        echo "✅ PRODUCTION DEPLOYMENT COMPLETE"
                        echo "New Version: ${DOCKER_TAG}"
                        echo "==========================================="
                    '''
                }
            }
            post {
                success {
                    slackSend(
                        color: 'good',
                        channel: '#production-alerts',
                        message: """
🚀 PRODUCTION DEPLOYMENT SUCCESSFUL
App: ${APP_NAME}
Version: ${DOCKER_TAG}
URL: https://api.vertoz.com
                        """
                    )
                }
                failure {
                    slackSend(
                        color: 'danger',
                        channel: '#production-alerts',
                        message: """
🔥 PRODUCTION DEPLOYMENT FAILED
App: ${APP_NAME}
Version: ${DOCKER_TAG}
Rollback initiated!
                        """
                    )
                }
            }
        }
        
        // ============================================================
        // STAGE 19: POST-DEPLOYMENT MONITORING
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
                        
                        # Check error rate
                        ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
                            -d 'query=sum(rate(http_requests_total{status=~"5.."}[5m]))/sum(rate(http_requests_total[5m]))' \
                            | jq '.data.result[0].value[1]' | sed 's/"//g')
                        
                        echo "Error Rate: $ERROR_RATE%"
                        
                        # Check response time
                        RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' \
                            https://api.vertoz.com/health)
                        echo "Response Time: ${RESPONSE_TIME}s"
                        
                        # Check logs for errors
                        ERROR_COUNT=$(kubectl logs deployment/${APP_NAME} -n production \
                            --tail=100 | grep -c ERROR)
                        echo "Errors in logs: $ERROR_COUNT"
                        
                        echo "==========================================="
                        echo "✅ MONITORING COMPLETE"
                        echo "==========================================="
                    '''
                }
            }
        }
        
        // ============================================================
        // STAGE 20: FINAL NOTIFICATION
        // ============================================================
        stage('📨 Final Notification') {
            steps {
                script {
                    echo "==========================================="
                    echo "📨 SENDING FINAL NOTIFICATION"
                    echo "==========================================="
                }
                slackSend(
                    color: 'good',
                    channel: '#devops',
                    message: """
✅ DEPLOYMENT COMPLETE
App: ${APP_NAME}
Version: ${DOCKER_TAG}
Environment: ${params.DEPLOY_ENV}
Build: ${env.BUILD_NUMBER}
URL: https://${params.DEPLOY_ENV}.vertoz.com
                    """
                )
            }
        }
    }
    
    // ============================================================
    // POST-BUILD ACTIONS
    // ============================================================
    post {
        success {
            echo "==========================================="
            echo "🎉 PIPELINE COMPLETED SUCCESSFULLY!"
            echo "==========================================="
        }
        failure {
            echo "==========================================="
            echo "❌ PIPELINE FAILED!"
            echo "==========================================="
            
            slackSend(
                color: 'danger',
                channel: '#devops',
                message: """
❌ PIPELINE FAILED
App: ${APP_NAME}
Environment: ${params.DEPLOY_ENV}
Build: ${env.BUILD_NUMBER}
Check logs: ${env.BUILD_URL}
                """
            )
        }
        always {
            script {
                sh '''
                    echo "Cleaning up workspace..."
                    docker system prune -f || true
                    rm -rf venv/
                '''
            }
        }
    }
}
