pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
        DOCKER_TAG = "v${GIT_COMMIT}" // Définir le tag de l'image Docker basé sur le commit Git
        KUBECONFIG = credentials("config") // Utilisation des credentials pour le fichier kubeconfig
    }

    stages {
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: "${BRANCH_NAME}", url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
            }
        }

        stage('Construire les images Docker') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_HUB_USER', passwordVariable: 'DOCKER_HUB_PASS')]) {
                        sh '''
                            echo "Connexion à Docker Hub..."
                            docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASS
                            echo "Construction des images..."
                            docker compose build
                        '''
                    }
                }
            }
        }

        stage('Exécuter les tests') {
            parallel {
                stage('Tests movie_service') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            sh '''
                                docker compose up -d movie_service
                                sleep 10
                                docker compose exec movie_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_movies.py --junitxml=/app/test-results-movie.xml"
                            '''
                        }
                    }
                    post {
                        always {
                            sh 'docker compose cp movie_service:/app/test-results-movie.xml ./test-results-movie.xml'
                            junit 'test-results-movie.xml'
                        }
                    }
                }

                stage('Tests cast_service') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            sh '''
                                docker compose up -d cast_service
                                sleep 10
                                docker compose exec cast_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_casts.py --junitxml=/app/test-results-cast.xml"
                            '''
                        }
                    }
                    post {
                        always {
                            sh 'docker compose cp cast_service:/app/test-results-cast.xml ./test-results-cast.xml'
                            junit 'test-results-cast.xml'
                        }
                    }
                }
            }
            post {
                failure {
                    echo "Certains tests ont échoué. Vérifiez les rapports."
                }
            }
        }

        stage('Tests accès au endpoint') {
            steps {
                script {
                    sh '''
                        curl http://localhost:8002/api/v1/casts/docs
                        curl http://localhost:8001/api/v1/movies/docs
                    '''
                }
            }
        }

        stage('Pousser les images Docker') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo "Les tests ont réussi. Pousser les images Docker vers Docker Hub..."
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_HUB_USER', passwordVariable: 'DOCKER_HUB_PASS')]) {
                        sh '''
                            echo "Connexion à Docker Hub..."
                            docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASS
                            echo "Pousser les images Docker..."
                            docker compose push
                        '''
                    }
                }
            }
        }

        stage('Nettoyer les conteneurs') {
            steps {
                echo "Arrêt et suppression des conteneurs..."
                sh '''
                    docker compose down --volumes --remove-orphans
                '''
            }
        }

        stage('Déploiement Dev') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    echo "Déploiement dans le namespace : dev"
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        helm upgrade --install cast-service helm/cast-chart/ -n dev 
                        helm upgrade --install movie-service helm/movie-chart/ -n dev 

                        kubectl rollout status deployment/cast-service -n dev --timeout=2m
                        kubectl rollout status deployment/movie-service -n dev --timeout=2m
                    '''
                }
            }
        }

        stage('Déploiement QA') {
            when {
                branch 'AQ'
            }
            steps {
                script {
                    echo "Déploiement dans le namespace : qa"
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        helm upgrade --install cast-service helm/cast-chart/ -n qa 
                        helm upgrade --install movie-service helm/movie-chart/ -n qa 

                        kubectl rollout status deployment/cast-service -n qa --timeout=2m
                        kubectl rollout status deployment/movie-service -n qa --timeout=2m
                    '''
                }
            }
        }

        stage('Déploiement Staging') {
            when {
                branch 'staging'
            }
            steps {
                script {
                    echo "Déploiement dans le namespace : staging"
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        helm upgrade --install cast-service helm/cast-chart/ -n staging 
                        helm upgrade --install movie-service helm/movie-chart/ -n staging 

                        kubectl rollout status deployment/cast-service -n staging --timeout=2m
                        kubectl rollout status deployment/movie-service -n staging --timeout=2m
                    '''
                }
            }
        }

        stage('Déploiement en Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Déployer en production ?', ok: 'Oui'
                script {
                    echo "Déploiement dans le namespace : prod"
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        helm upgrade --install cast-service helm/cast-chart/ -n prod 
                        helm upgrade --install movie-service helm/movie-chart/ -n prod 

                        kubectl rollout status deployment/cast-service -n prod --timeout=2m
                        kubectl rollout status deployment/movie-service -n prod --timeout=2m
                    '''
                }
            }
        }
    }

    post {
        failure {
            echo "Les tests ont échoué. Les images Docker ne seront pas poussées vers Docker Hub."
            slackSend channel: '#devops', message: "Le pipeline a échoué : ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}"
        }
        success {
            echo "Pipeline exécuté avec succès !"
        }
    }
}
