pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
    }
    stages {
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonae du dépôt Git..."
                git branch: 'develop', url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
            }
        }
        // Contruction des images Docker cast-service et movie-service
        stage('Construire les images Docker') {
            steps {
                script {
                    echo "Construction des images Docker avec docker-compose..."
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_HUB_USER', passwordVariable: 'DOCKER_HUB_PASS')]) {
                        sh '''
                            echo "Connexion à Docker Hub..."
                            docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASS
                            echo "Construction des images..."
                            docker compose up -d
                        '''
                    }
                }
            }
        }
        // Exécuter les tests dans le conteneur movie_service
        stage('Exécuter les tests dans movie_service') {
            steps {
                echo "Exécution des tests dans le conteneur movice_service..."
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

        // Nettoyage des conteneurs
        stage('Nettoyer les conteneurs') {
            echo "Arrêt et suppression des conteneurs..."
            sh '''
                docker compose down
            '''
        }
    }
}