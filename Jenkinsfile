pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
  }

  parameters {
    choice(name: 'SUITE', choices: ['all', 'api', 'ui'], description: '选择测试套件')
    string(name: 'API_BASE_URL', defaultValue: '', description: '覆盖 API base URL (留空用默认)')
    string(name: 'UI_BASE_URL', defaultValue: '', description: '覆盖 UI base URL (留空用默认)')
    booleanParam(name: 'GEN_API', defaultValue: true, description: '是否重新生成 OpenAPI SDK')
    string(name: 'MARKER', defaultValue: '', description: 'pytest -m 表达式')
    string(name: 'KEYWORDS', defaultValue: '', description: 'pytest -k 表达式')
    string(name: 'TASK_RUN_ID', defaultValue: '', description: '平台任务执行 ID,回传结果用')
  }

  environment {
    AUTOTEST_API_BASE_URL = "${params.API_BASE_URL ?: ''}"
    AUTOTEST_UI_BASE_URL  = "${params.UI_BASE_URL ?: ''}"
    AUTOTEST_HEADLESS     = 'true'
    JUNIT_REPORT          = 'target/junit-report.xml'
    PLATFORM_URL          = 'http://127.0.0.1:8000'
  }

  stages {
    stage('Install') {
      steps {
        bat 'python -m pip install --upgrade pip'
        bat 'python -m pip install -e .[dev]'
        bat 'python -m playwright install --with-deps chromium'
      }
    }

    stage('Gen API SDK') {
      when { expression { return params.GEN_API } }
      steps {
        bat 'python scripts/gen_api.py'
      }
    }

    stage('Test') {
      steps {
        script {
          def marker = params.MARKER ? "-m ${params.MARKER}" : (params.SUITE == 'all' ? '' : "-m ${params.SUITE}")
          def kw = params.KEYWORDS ? "-k \"${params.KEYWORDS}\"" : ''
          bat "python -m pytest ${marker} ${kw} --junitxml=${JUNIT_REPORT} --alluredir target/allure-results --clean-alluredir"
        }
      }
    }

    stage('Report to Platform') {
      when { expression { return params.TASK_RUN_ID?.trim() } }
      steps {
        script {
          def xml = readFile(file: env.JUNIT_REPORT, encoding: 'UTF-8')
          def payload = groovy.json.JsonOutput.toJson([
            run_id: params.TASK_RUN_ID.toInteger(),
            junit_xml: xml
          ])
          writeFile(file: 'target/ingest.json', text: payload)

          withCredentials([usernamePassword(credentialsId: 'autotest-platform',
                                            usernameVariable: 'PLAT_USER',
                                            passwordVariable: 'PLAT_PASS')]) {
            bat '''
              curl -s -X POST "%PLATFORM_URL%/api/results/ingest" ^
                -H "Content-Type: application/json" ^
                -u "%PLAT_USER%:%PLAT_PASS%" ^
                --data-binary @target/ingest.json
            '''
          }
        }
      }
    }
  }

  post {
    always {
      allure(results: [[path: 'target/allure-results']])
      archiveArtifacts artifacts: 'target/junit-report.xml,target/allure-results/**', allowEmptyArchive: true
    }
  }
}
