pipeline {
    agent any
    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-creds') // Utilisation de l'ID du credential créé
        DOCKER_TAG = "v${GIT_COMMIT}" // Tag basé sur le commit Git
        // Map des branches vers les namespaces Kubernetes
        KUBE_NAMESPACES = [
            'develop': 'dev',
            'AQ': 'qa',
            'staging': 'staging',
            'main': 'prod'
        ]
        KUBE_NAMESPACE = "" // Sera défini dynamiquement
    }
    stages {
        // Étape 1 : Clonage du dépôt Git
        stage('Cloner le dépôt Git') {
            steps {
                echo "Clonage du dépôt Git..."
                git branch: "${BRANCH_NAME}", url: 'https://github.com/josuekabangu/DATASCIENTEST-JENKINS-EXAMEN.git'
                
                script {
                    // Assignation dynamique de KUBE_NAMESPACE depuis la map
                    if (KUBE_NAMESPACES.containsKey(env.BRANCH_NAME)) {
                        env.KUBE_NAMESPACE = KUBE_NAMESPACES[env.BRANCH_NAME]
                    } else {
                        error("Branche non supportée : ${BRANCH_NAME}")
                    }
                    echo "Namespace Kubernetes détecté : ${env.KUBE_NAMESPACE}"
                }
            }
        }

        // Étape 2 : Construction et push des images Docker
        stage('Construction et Push des images Docker') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_HUB_USER', passwordVariable: 'DOCKER_HUB_PASS')]) {
                        sh '''
                            echo "Connexion à Docker Hub..."
                            docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASS
                            echo "Construction des images..."
                            docker compose build
                            echo "Pousser les images..."
                            docker compose push
                        '''
                    }
                }
            }
        }

        // Étape 3 : Exécution des tests dans les conteneurs
        stage('Exécuter les tests dans movie_service et cast_service') {
            steps {
                echo "Exécution des tests dans les conteneurs..."
                sh '''
                    docker compose up -d
                    sleep 10
                    docker compose exec movie_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_movies.py --junitxml=/app/test-results-movie.xml" || { echo "Tests movie_service échoués"; exit 1; }
                    docker compose exec cast_service bash -c "PYTHONPATH=/app pytest /app/app/tests/test_casts.py --junitxml=/app/test-results-cast.xml" || { echo "Tests cast_service échoués"; exit 1; }
                '''
            }
            post {
                always {
                    sh '''
                        docker compose cp movie_service:/app/test-results-movie.xml ./test-results-movie.xml || echo "Aucun résultat de test pour movie_service"
                        docker compose cp cast_service:/app/test-results-cast.xml ./test-results-cast.xml || echo "Aucun résultat de test pour cast_service"
                    '''
                    junit '**/test-results*.xml' // Publier les résultats des tests
                }
            }
        }

        // Étape 4 : Tests d'accès aux endpoints
        stage('Exécuter les tests accès au endpoint') {
            steps {
                script {
                    sh '''
                        curl --fail http://localhost:31631/api/v1/casts/docs || { echo "Erreur lors de l'accès à cast_service"; exit 1; }
                        curl --fail http://localhost:31023/api/v1/movies/docs || { echo "Erreur lors de l'accès à movie_service"; exit 1; }
                    '''
                }
            }
        }

        // Étape 5 : Nettoyage des conteneurs
        stage('Nettoyer les conteneurs') {
            steps {
                echo "Arrêt et suppression des conteneurs..."
                sh '''
                    docker compose down --volumes --remove-orphans
                '''
            }
        }

        // Fonction réutilisable pour le déploiement Kubernetes
        script {
            def deployToKubernetes = { String namespace ->
                withEnv(["KUBE_NAMESPACE=${namespace}"]) {
                    sh '''
                        rm -rf .kube
                        mkdir .kube
                        cat $KUBECONFIG > .kube/config
                        helm upgrade --install cast-service helm/cast-chart/ -n ${KUBE_NAMESPACE}
                        helm upgrade --install movie-service helm/movie-chart/ -n ${KUBE_NAMESPACE}
                    '''
                }
            }

            // Étape 6 : Déploiement dans Kubernetes (non-prod)
            stage('Déploiement dans Kubernetes') {
                environment {
                    KUBECONFIG = credentials("config")
                }
                when {
                    expression { env.BRANCH_NAME == 'develop' || env.BRANCH_NAME == 'AQ' || env.BRANCH_NAME == 'staging' }
                }
                steps {
                    script {
                        if (!env.KUBE_NAMESPACE) {
                            error("La variable KUBE_NAMESPACE est vide. Le déploiement ne peut pas continuer.")
                        }
                        echo "Déploiement dans le namespace : ${env.KUBE_NAMESPACE}"
                        deployToKubernetes(env.KUBE_NAMESPACE)
                    }
                }
            }

            // Étape 7 : Déploiement en production (manuel)
            stage('Déploiement en Production') {
                environment {
                    KUBECONFIG = credentials("config")
                }
                when {
                    branch 'main'
                }
                steps {
                    input message: 'Déployer en production ?', ok: 'Oui'
                    script {
                        echo "Déploiement dans le namespace : prod"
                        deployToKubernetes('prod')
                    }
                }
            }
        }
    }

    // Gestion des échecs
    post {
        failure {
            echo "Le pipeline a échoué. Vérifiez les logs pour plus de détails."
        }
        always {
            echo "Pipeline terminé."
        }
    }
}
