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
                            docker compose build
                        '''
                    }
                }
            }
        }
    }
}