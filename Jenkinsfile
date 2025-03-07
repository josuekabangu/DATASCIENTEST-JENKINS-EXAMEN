pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
    }
    stages {
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: 'develop', url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
            }
        }

        // Construction des images Docker
        stage('Construire les images Docker') {
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

        // Démarrer les conteneurs
        stage('Démarrer les conteneurs') {
            steps {
                echo "Démarrage des conteneurs avec docker-compose..."
                sh '''
                    docker compose up -d
                    sleep 10 # Attendre que les services soient prêts
                '''
            }
        }

        // Exécuter les tests dans le conteneur movie_service
        stage('Exécuter les tests dans movie_service') {
            steps {
                echo "Exécution des tests dans le conteneur movie_service..."
                sh '''
                    docker compose exec movie_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_movies.py --junitxml=/app/test-results.xml"
                '''
            }
            post {
                always {
                    // Récupérer le fichier de résultats des tests
                    sh '''
                        docker compose cp movie_service:/app/test-results.xml ./test-results.xml
                    '''
                    // Publier les résultats des tests dans Jenkins
                    junit 'test-results.xml'
                }
            }
        }

        // Exécuter les tests dans le conteneur cast_service
        stage('Exécuter les tests dans cast_service') {
            steps {
                echo "Exécution des tests dans le conteneur cast_service..."
                sh '''
                    docker compose exec cast_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_casts.py --junitxml=/app/test-results.xml"
                '''
            }
            post {
                always {
                    // Récupérer le fichier de résultats des tests
                    sh '''
                        docker compose cp cast_service:/app/test-results.xml ./test-results.xml
                    '''
                    // Publier les résultats des tests dans Jenkins
                    junit 'test-results.xml'
                }
            }
        }

        // Étape de push des images Docker vers Docker Hub (uniquement si les tests réussissent)
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

        // Nettoyage des conteneurs
        stage('Nettoyer les conteneurs') {
            steps {
                echo "Arrêt et suppression des conteneurs..."
                sh '''
                    docker compose down
                '''
            }
        }
    }

    // Gestion des échecs
    post {
        failure {
            echo "Les tests ont échoué. Les images Docker ne seront pas poussées vers Docker Hub."
        }
    }
}