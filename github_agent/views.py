from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import joblib
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Function to process user input
def process_input(input_text):
    doc = nlp(input_text)
    keywords = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    return keywords

def search_github_projects(keywords):
    query = " ".join(keywords)
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'items' in data:
            projects = data['items']
            return projects
        else:
            return []
    except requests.exceptions.RequestException as e:
        return []

def train_recommendation_model(projects):
    descriptions = [project['description'] if project['description'] else "" for project in projects]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    return tfidf_matrix, vectorizer

def get_top_n_similar_projects(user_input, projects, tfidf_matrix, vectorizer, n=10):
    user_input_tfidf = vectorizer.transform([user_input])
    cosine_similarities = cosine_similarity(user_input_tfidf, tfidf_matrix).flatten()
    top_n_indices = cosine_similarities.argsort()[-n:][::-1]
    top_n_projects = [projects[i] for i in top_n_indices]
    return top_n_projects

@csrf_exempt
def get_recommendations(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        if user_input:
            keywords = process_input(user_input)
            projects = search_github_projects(keywords)

            if not projects:
                return JsonResponse({'error': 'No projects found.'}, status=404)

            tfidf_matrix, vectorizer = train_recommendation_model(projects)
            top_projects = get_top_n_similar_projects(user_input, projects, tfidf_matrix, vectorizer, n=10)

            joblib.dump(tfidf_matrix, os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'tfidf_matrix.pkl'))
            joblib.dump(vectorizer, os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'vectorizer.pkl'))
            joblib.dump(top_projects, os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'projects.pkl'))

            recommended_projects = [
                {
                    'name': project['name'],
                    'full_name': project['full_name'],
                    'description': project['description'],
                    'html_url': project['html_url'],
                    'stargazers_count': project['stargazers_count']
                }
                for project in top_projects
            ]

            return JsonResponse({'projects': recommended_projects})
        else:
            return JsonResponse({'error': 'No input provided.'}, status=400)
    return render(request, 'index.html')

