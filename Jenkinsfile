pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Credentials DockerHub
        DOCKER_TAG = "v${GIT_COMMIT}" // Tag de l'image basé sur le commit Git
        KUBE_NAMESPACE = "" // Namespace Kubernetes (défini dynamiquement)
    }
    stages {
        // Étape 1 : Clonage du dépôt Git
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: "${BRANCH_NAME}", url: 'https://github.com/votre-utilisateur/DATASCIENTEST-JENKINS-EXAMEN.git'
                script {
                    // Définir le namespace Kubernetes en fonction de la branche
                    if (env.BRANCH_NAME == 'develop') {
                        env.KUBE_NAMESPACE = 'dev'
                    } else if (env.BRANCH_NAME == 'AQ') {
                        env.KUBE_NAMESPACE = 'qa'
                    } else if (env.BRANCH_NAME == 'staging') {
                        env.KUBE_NAMESPACE = 'staging'
                    } else if (env.BRANCH_NAME == 'main') {
                        env.KUBE_NAMESPACE = 'prod'
                    } else {
                        error("Branche non supportée : ${BRANCH_NAME}")
                    }
                    echo "Namespace Kubernetes détecté : ${env.KUBE_NAMESPACE}"
                }
            }
        }

        // Étape 2 : Construction des images Docker
        stage('Construction des images Docker') {
            steps {
                script {
                    echo "Construction des images Docker avec docker-compose..."
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

        // Étape 3 : Exécution des tests
        stage('Exécution des tests') {
            steps {
                echo "Exécution des tests..."
                sh '''
                    docker compose up -d
                    docker compose exec movie_service pytest /app/app/tests/test_movies.py --junitxml=/app/test-results-movie.xml
                    docker compose exec cast_service pytest /app/app/tests/test_casts.py --junitxml=/app/test-results-cast.xml
                '''
                junit '**/test-results-*.xml' // Publier les résultats des tests
            }
        }

        // Étape 4 : Pousser les images Docker (uniquement si les tests réussissent)
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

        // Étape 5 : Déploiement dans Kubernetes
        stage('Déploiement dans Kubernetes') {
            when {
                expression { env.BRANCH_NAME == 'develop' || env.BRANCH_NAME == 'AQ' || env.BRANCH_NAME == 'staging' }
            }
            environment {
                KUBECONFIG = credentials("config") // Credentials Kubernetes
            }
            steps {
                script {
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        # Déploiement du cast-service
                        helm upgrade --install cast-service helm/cast-chart/ -n ${KUBE_NAMESPACE} --set image.tag=${DOCKER_TAG}

                        # Déploiement du movie-service
                        helm upgrade --install movie-service helm/movie-chart/ -n ${KUBE_NAMESPACE} --set image.tag=${DOCKER_TAG}
                    '''
                }
            }
        }

        // Étape 6 : Déploiement en production (manuel)
        stage('Déploiement en Production') {
            when {
                branch 'main'
                input message: 'Déployer en production ?', ok: 'Oui'
            }
            environment {
                KUBECONFIG = credentials("config")
            }
            steps {
                script {
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        # Déploiement du cast-service
                        helm upgrade --install cast-service helm/cast-chart/ -n prod --set image.tag=${DOCKER_TAG}

                        # Déploiement du movie-service
                        helm upgrade --install movie-service helm/movie-chart/ -n prod --set image.tag=${DOCKER_TAG}
                    '''
                }
            }
        }
    }

    // Gestion des échecs
    post {
        failure {
            echo "Les tests ont échoué. Les images Docker ne seront pas poussées vers Docker Hub."
        }
        success {
            echo "Pipeline exécuté avec succès !"
        }
    }
}