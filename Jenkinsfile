pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
        DOCKER_TAG = "v${GIT_COMMIT}" // Définir le tag de l'image Docker basé sur le commit Git
        KUBE_NAMESPACE = "" // Namespace dynamique (sera défini en fonction de la branche)
    }
    stages {
        // Étape 1 : Clonage du dépôt Git
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: "${BRANCH_NAME}", url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
                
                script {
                    // Définition du namespace Kubernetes en fonction de la branche
                    def KUBE_NAMESPACE = [
                        'develop': 'dev',
                        'AQ': 'qa',
                        'staging': 'staging',
                        'main': 'prod'
                    ]
                    // Assignation dynamique de KUBE_NAMESPACE depuis la map
                    if (KUBE_NAMESPACE.containsKey(env.BRANCH_NAME)) {
                        env.KUBE_NAMESPACE = KUBE_NAMESPACE[env.BRANCH_NAME]
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

        // Étape 3 : Exécution des tests dans le conteneur movie_service
        stage('Exécuter les tests dans movie_service') {
            steps {
                echo "Exécution des tests dans le conteneur movie_service..."
                sh '''
                    docker compose up -d
                    # Attendre quelques secondes pour s'assurer que les conteneurs sont bien démarrés
                    sleep 10
                    docker compose exec movie_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_movies.py --junitxml=/app/test-results-movie.xml"
                    docker compose exec cast_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_casts.py --junitxml=/app/test-results-cast.xml"
                '''
            }
            post {
                always {
                    // Récupérer le fichier de résultats des tests
                    sh '''
                        docker compose cp movie_service:/app/test-results-movie.xml ./test-results-movie.xml
                        docker compose cp cast_service:/app/test-results-cast.xml ./test-results-cast.xml
                    '''
                    // Publier les résultats des tests dans Jenkins
                    junit '**/test-results*.xml'  // Publier les résultats des tests
                }
                failure {
                    error "Les tests ont échoué. Le pipeline est arrêté."
                }
            }
        }

        // Étape 4 : Exécution des tests pour l'accès au endpoint
        stage('Exécuter les tests accès au endpoint') {
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
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } // Exécuter uniquement si les étapes précédentes ont réussi
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

        // Étape 7 : Déploiement dans Kubernetes
        stage('Deploiement dans Kubernetes') {
            environment {
                KUBECONFIG = credentials("config") // Utilisation des credentials pour le fichier kubeconfig
            }
            when {
                expression { env.BRANCH_NAME == 'develop' || env.BRANCH_NAME == 'AQ' || env.BRANCH_NAME == 'staging' }
            }
            steps {
                script {
                    echo "Déploiement dans le namespace : ${env.KUBE_NAMESPACE}"
                    sh '''
                        echo "KUBE_NAMESPACE=${KUBE_NAMESPACE}"
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n ${KUBE_NAMESPACE} 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n ${KUBE_NAMESPACE} 
                    '''
                }
            }
        }

        // Étape 8 : Déploiement en production (manuel)
        stage('Déploiement en Production') {
            environment {
                KUBECONFIG = credentials("config") // Utilisation des credentials pour le fichier kubeconfig
            }
            when {
                branch 'main'
            }
            steps {
                // Demande de confirmation manuelle avant de déployer en production
                input message: 'Déployer en production ?', ok: 'Oui'

                script {
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config

                        # Déploiement du cast-service                        
                        helm upgrade --install cast-service helm/cast-chart/ -n prod 

                        # Déploiement du movie-service           
                        helm upgrade --install movie-service helm/movie-chart/ -n prod 
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
        }
    }
}
