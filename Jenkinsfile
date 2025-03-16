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

        // Étape 3 : Exécution des tests dans le conteneur movie_service
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

        // Étape 4 : Exécution des tests pour l'accès au endpoint
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

        // Étape 5 : Push des images Docker vers Docker Hub (uniquement si les tests réussissent)
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

        // Étape 6 : Nettoyage des conteneurs
        stage('Nettoyer les conteneurs') {
            steps {
                echo "Arrêt et suppression des conteneurs..."
                sh '''
                    docker compose down --volumes --remove-orphans
                '''
            }
        }

        // Étape 7 : Déploiement dans Kubernetes (par environnement)
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

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n dev 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n dev 

                        # Validation du déploiement
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

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n qa 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n qa 

                        # Validation du déploiement
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

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n staging 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n staging 

                        # Validation du déploiement
                        kubectl rollout status deployment/cast-service -n staging --timeout=2m
                        kubectl rollout status deployment/movie-service -n staging --timeout=2m
                    '''
                }
            }
        }

        // Étape 8 : Dpipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
        DOCKER_TAG = "v${GIT_COMMIT}" // Définir le tag de l'image Docker basé sur le commit Git
        KUBECONFIG = credentials("config") // Utilisation des credentials pour le fichier kubeconfig
    }
    stages {
        // Étape 1 : Clonage du dépôt Git
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: "${BRANCH_NAME}", url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
            }
        }

        // Étape 2 : Construction des images Docker
        stage('Construction des images Docker') {
            steps {
                script {
                    echo "Construction des images Docker avec docker-compose..."
     éploiement en production (manuel)
        stage('Déploiement en Production') {
            when {
                branch 'main'
            }
            steps {
                // Demande de confirmation manuelle avant de déployer en production
                input message: 'Déployer en production ?', ok: 'Oui'

                script {
                    echo "Déploiement dans le namespace : prod"
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n prod 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n prod 

                        # Validation du déploiement
                        kubectl rollout status deployment/cast-service -n prod --timeout=2m
                        kubectl rollout status deployment/movie-service -n prod --timeout=2m
                    '''
                }
            }
        }
    }

    // Gestion des échecs
    post {
        failure {
            echo "Les tests ont échoué. Les images Docker ne seront pas poussées vers Docker Hub."
            // Ajouter une notification ici (e-mail, Slack, etc.)
            slackSend channel: '#devops', message: "Le pipeline a échoué : ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}"
        }
        success {
            echo "Pipeline exécuté avec succès !"
        }
    }
}
