from deepeval import evaluate
from deepeval.metrics import HallucinationMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from app import app, client, User, db, ChatHistory
from flask_login import login_user
import json
import os

def create_test_cdc_file():
    """Crée un fichier cdc.txt de test avec du contenu spécifique"""
    test_content = """# Cahier des Charges Test
## Section 1: Introduction
Ceci est un test de lecture du fichier cdc.txt.

## Section 2: Objectifs
- Vérifier la lecture du fichier
- Tester la compréhension du contenu

## Section 3: Exigences
1. Le système doit lire cdc.txt
2. Le système doit comprendre le format
3. Le système doit extraire les informations"""
    
    with open('cdc.txt', 'w', encoding='utf-8') as f:
        f.write(test_content)
    return test_content

def run_test_case(test_case, client, test_user):
    # Faire la requête au chatbot
    response = client.post('/api/chat', 
        json={
            'messages': [
                {"role": "system", "content": "Vous êtes un assistant spécialisé dans la création de cahiers des charges. Commencez TOUJOURS vos réponses par 'Je suis spécialisé dans la création de cahiers des charges.' Donnez des réponses concises et précises, sans poser de questions supplémentaires. Concentrez-vous sur la réponse directe à la question posée. Ne donnez que les informations essentielles."},
                {"role": "user", "content": test_case.input}
            ]
        }
    )
    
    if response.status_code == 200:
        data = json.loads(response.data)
        test_case.actual_output = data.get('response', '')
        print(f"\nTest: {test_case.input}")
        print(f"Réponse du chatbot : {test_case.actual_output}")
    else:
        print(f"Erreur : {response.status_code} - {response.data}")

def test_chatbot_responses():
    # Créer le fichier cdc.txt de test
    test_content = create_test_cdc_file()
    
    # Créer les cas de test
    test_cases = [
        LLMTestCase(
            input="Qu'est-ce qu'un cahier des charges ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Un document qui décrit les spécifications et exigences d'un projet",
            context=[
                "Le chatbot est spécialisé dans la création de cahiers des charges",
                "Un cahier des charges est un document formel qui décrit les besoins et exigences d'un projet",
                "Il sert de référence pour toutes les parties prenantes du projet",
                "Le chatbot doit donner une définition concise et précise",
                "La réponse doit être directe sans questions supplémentaires",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        ),
        LLMTestCase(
            input="Quelles sont les sections principales d'un cahier des charges ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Les sections principales incluent : contexte, objectifs, exigences fonctionnelles et techniques, contraintes, planning et budget",
            context=[
                "Un cahier des charges doit être structuré",
                "Il doit contenir des sections claires et organisées",
                "Les sections principales sont standardisées",
                "Le chatbot doit lister les sections essentielles",
                "La réponse doit être concise et structurée",
                "Pas de questions supplémentaires",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        ),
        LLMTestCase(
            input="Comment rédiger les exigences fonctionnelles ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Les exigences fonctionnelles doivent être claires, mesurables et testables, en utilisant des verbes d'action",
            context=[
                "Les exigences fonctionnelles sont cruciales",
                "Elles doivent être bien formulées",
                "Le chatbot doit expliquer la méthodologie",
                "La formulation doit être précise",
                "La réponse doit inclure des exemples concrets",
                "Réponse directe sans questions",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        ),
        LLMTestCase(
            input="Quelle est la différence entre exigences fonctionnelles et techniques ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Les exigences fonctionnelles décrivent ce que le système doit faire, tandis que les exigences techniques définissent comment le système doit le faire",
            context=[
                "Il existe deux types d'exigences",
                "La distinction est importante",
                "Le chatbot doit expliquer clairement la différence",
                "Les exemples sont utiles",
                "La réponse doit être concise et claire",
                "Pas de questions supplémentaires",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        ),
        LLMTestCase(
            input="Comment structurer un cahier des charges ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Un cahier des charges doit suivre une structure logique : introduction, contexte, objectifs, exigences, contraintes, planning et budget",
            context=[
                "La structure est essentielle",
                "Le document doit être facile à suivre",
                "Le chatbot doit expliquer la logique",
                "La réponse doit être méthodique",
                "La structure doit être progressive",
                "Réponse directe sans questions",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        ),
        # Test pour vérifier la lecture de cdc.txt
        LLMTestCase(
            input="Quelles sont les exigences listées dans le cahier des charges ?",
            actual_output="",
            expected_output="Je suis spécialisé dans la création de cahiers des charges. Les exigences sont : 1. Le système doit lire cdc.txt, 2. Le système doit comprendre le format, 3. Le système doit extraire les informations",
            context=[
                "Le fichier cdc.txt contient des exigences spécifiques",
                "Le chatbot doit lire et comprendre le contenu du fichier",
                "La réponse doit mentionner les exigences exactes du fichier",
                "La réponse doit être précise et complète",
                "Pas de questions supplémentaires",
                "La réponse doit commencer par 'Je suis spécialisé dans la création de cahiers des charges'",
                "La réponse doit être courte et aller droit au but"
            ]
        )
    ]

    def create_test_user():
        user = User(login="test_user", name="Test User", is_active=True)
        user.set_password("test_password")
        db.session.add(user)
        db.session.commit()
        return user

    with app.app_context():
        # Créer un utilisateur de test
        test_user = create_test_user()

        # Simuler une requête au chatbot avec une session authentifiée
        with app.test_client() as client:
            # Simuler la connexion
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
                session['_fresh'] = True

            # Exécuter tous les tests
            for test_case in test_cases:
                run_test_case(test_case, client, test_user)

        # Nettoyer la base de données
        try:
            # Supprimer d'abord l'historique du chat
            ChatHistory.query.filter_by(user_id=test_user.id).delete()
            db.session.commit()
            
            # Puis supprimer l'utilisateur
            db.session.delete(test_user)
            db.session.commit()
        except Exception as e:
            print(f"Erreur lors du nettoyage : {e}")
            db.session.rollback()

    # Nettoyer le fichier cdc.txt de test
    try:
        if os.path.exists('cdc.txt'):
            os.remove('cdc.txt')
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier cdc.txt : {e}")

    # Définir les métriques
    metrics = [
        HallucinationMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7)
    ]

    # Évaluer tous les tests
    results = evaluate(test_cases, metrics)
    
    print("\nRésultats de l'évaluation :")
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case.input}")
        print(f"Réponse attendue : {test_case.expected_output}")
        print(f"Réponse obtenue : {test_case.actual_output}")
        
        # Calculer les scores moyens pour ce test
        hallucination_scores = []
        relevancy_scores = []
        
        for result in results:
            if isinstance(result, dict) and 'metrics' in result:
                for metric in result['metrics']:
                    if metric['name'] == 'Hallucination':
                        hallucination_scores.append(metric['score'])
                    elif metric['name'] == 'Answer Relevancy':
                        relevancy_scores.append(metric['score'])
        
        if hallucination_scores:
            print(f"Score Hallucination moyen : {sum(hallucination_scores)/len(hallucination_scores):.2f}")
        if relevancy_scores:
            print(f"Score Pertinence moyen : {sum(relevancy_scores)/len(relevancy_scores):.2f}")

if __name__ == "__main__":
    test_chatbot_responses() 