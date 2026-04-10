import os
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserRegisterForm, LoginForm, DatasetUploadForm
from .models import CustomUser, UploadedDataset
from django.conf import settings
from django.http import HttpResponse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# --- Authentication Views ---

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user_home')
    else:
        form = UserRegisterForm()
    return render(request, 'prediction/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_admin:
                return redirect('admin_home')
            else:
                return redirect('user_home')
    else:
        form = LoginForm()
    return render(request, 'prediction/login.html', {'form': form})

def home(request):
    return render(request, 'prediction/home.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def user_home(request):
    return render(request, 'prediction/user_home.html')

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_home(request):
    return render(request, 'prediction/admin_home.html')

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_login(request):
    # Redirect to admin home if already logged in as admin
    return redirect('admin_home')

# --- Admin User Management ---

@login_required
@user_passes_test(lambda u: u.is_admin)
def user_list(request):
    users = CustomUser.objects.filter(is_admin=False)
    return render(request, 'prediction/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect('user_list')

# --- Dataset Upload & Preprocessing ---

@login_required
def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('preprocess_dataset')
    else:
        form = DatasetUploadForm()
    return render(request, 'prediction/upload_dataset.html', {'form': form})

@login_required
def preprocess_dataset(request):
    dataset = UploadedDataset.objects.last()
    if not dataset:
        return HttpResponse("No dataset uploaded.")
    df = pd.read_csv(dataset.file.path)
    before = df.shape[0]
    df = df.drop_duplicates()
    after = df.shape[0]
    # Save preprocessed file for ML steps
    df.to_csv(os.path.join(settings.MEDIA_ROOT, 'datasets', 'preprocessed.csv'), index=False)
    return render(request, 'prediction/preprocess.html', {'before': before, 'after': after})

# --- ML Algorithms ---

@login_required
def ml_algorithms(request):
    # Compute best algorithm from preprocessed dataset
    best_algo = None
    try:
        df = pd.read_csv(os.path.join(settings.MEDIA_ROOT, 'datasets', 'preprocessed.csv'))
        X = df.drop('ev_energy_demand', axis=1)
        y = df['ev_energy_demand']
        for col in X.select_dtypes(include='object').columns:
            X[col] = LabelEncoder().fit_transform(X[col])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        algos = {
            "Logistic Regression": LogisticRegression(max_iter=1000),
            "Random Forest": RandomForestClassifier(),
            "SVM": SVC(probability=True),
            "KNN": KNeighborsClassifier()
        }
        results = {}
        for name, model in algos.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            results[name] = acc
        best_algo = max(results, key=results.get)
    except Exception:
        best_algo = None
    return render(request, 'prediction/ml_algorithms.html', {'best_algo': best_algo})

@login_required
def run_ml(request, algo):
    """
    View to handle running the selected ML algorithm or the best one.
    Redirects to the detail page for the selected algorithm or best.
    """
    algo_map = {
        'Logistic Regression': 'logistic',
        'Random Forest': 'rf',
        'SVM': 'svm',
        'KNN': 'knn',
        'Best': 'best'
    }
    algo_key = algo_map.get(algo, algo.lower().replace(' ', ''))
    return redirect('ml_algorithm_detail', algo=algo_key)

@login_required
def ml_algorithm_detail(request, algo):
    df = pd.read_csv(os.path.join(settings.MEDIA_ROOT, 'datasets', 'preprocessed.csv'))
    X = df.drop('ev_energy_demand', axis=1)
    y = df['ev_energy_demand']
    for col in X.select_dtypes(include='object').columns:
        X[col] = LabelEncoder().fit_transform(X[col])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    algos = {
        "logistic": LogisticRegression(max_iter=1000),
        "rf": RandomForestClassifier(),
        "svm": SVC(probability=True),
        "knn": KNeighborsClassifier(),
    }
    algo_names = {
        "logistic": "Logistic Regression",
        "rf": "Random Forest",
        "svm": "SVM",
        "knn": "KNN",
    }
    results = {}
    for name, model in algos.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results[name] = acc
    # If 'best' is requested, pick the best algorithm
    if algo == 'best':
        best_key = max(results, key=results.get)
        model = algos[best_key]
        algo_name = algo_names[best_key]
    else:
        if algo not in algos:
            return redirect('ml_algorithms')
        model = algos[algo]
        algo_name = algo_names[algo]
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    cr = classification_report(y_test, y_pred)

    # Plot confusion matrix
    fig, ax = plt.subplots()
    ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.7)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(x=j, y=i, s=cm[i, j], va='center', ha='center')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    cm_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return render(request, 'prediction/ml_algorithm_detail.html', {
        'algo': algo_name,
        'acc': acc,
        'cm': cm,
        'cr': cr,
        'cm_img': cm_img,
        'best_algo': max(results, key=results.get),
    })
@login_required
def best_ml_algorithm(request):
    import os
    import pandas as pd
    import io
    import base64
    import matplotlib.pyplot as plt
    from django.conf import settings
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.metrics import accuracy_score

    df = pd.read_csv(os.path.join(settings.MEDIA_ROOT, 'datasets', 'preprocessed.csv'))
    X = df.drop('ev_energy_demand', axis=1)
    y = df['ev_energy_demand']
    for col in X.select_dtypes(include='object').columns:
        X[col] = LabelEncoder().fit_transform(X[col])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    algos = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(),
        "SVM": SVC(probability=True),
        "KNN": KNeighborsClassifier()
    }
    results = {}
    for name, model in algos.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results[name] = acc

    best_algo = max(results, key=results.get)
    confidence = results[best_algo] * 100

    # Bar chart for visualization
    fig, ax = plt.subplots()
    ax.bar(results.keys(), [v*100 for v in results.values()], color=['#4f8cff', '#22c55e', '#f59e42', '#e34f4f'])
    plt.ylabel('Accuracy (%)')
    plt.title('Algorithm Confidence Levels')
    plt.ylim(0, 100)
    for i, v in enumerate(results.values()):
        ax.text(i, v*100 + 2, f"{v*100:.1f}%", ha='center', color='#2d3a4b')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    map_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return render(request, 'prediction/best_ml_algorithm.html', {
        'best_algo': best_algo,
        'confidence': f"{confidence:.2f}",
        'map_img': map_img,
        'results': results
    })

# --- Prediction ---

@login_required
def predict_view(request):
    prediction = None
    if request.method == 'POST':
        try:
            # Collect input values from form
            battery = float(request.POST['Battery_Capacity_kWh'])
            speed = float(request.POST['Current_Speed_kmph'])
            distance = float(request.POST['Distance_Driven_km'])
            temp = float(request.POST['Ambient_Temperature'])
            soc = float(request.POST['State_of_Charge_%'])
            battery_type = request.POST['Battery_Type']
            vehicle_type = request.POST['Vehicle_Type']
            energy_consumed = float(request.POST['Energy_Consumed_kWh'])
            vehicle_id = request.POST['Vehicle_ID']

            # Prepare input for model (order and names must match training data)
            X_input = pd.DataFrame([{
                'Vehicle_ID': vehicle_id,
                'Battery_Type': battery_type,
                'Vehicle_Type': vehicle_type,
                'Ambient_Temperature': temp,
                'Distance_Driven_km': distance,
                'State_of_Charge_%': soc,
                'Battery_Capacity_kWh': battery,
                'Current_Speed_kmph': speed,
                'Energy_Consumed_kWh': energy_consumed
            }])

            # Encode categorical columns as in training
            for col in X_input.select_dtypes(include='object').columns:
                X_input[col] = LabelEncoder().fit_transform(X_input[col])

            # Load preprocessed data and train model
            df = pd.read_csv(os.path.join(settings.MEDIA_ROOT, 'datasets', 'preprocessed.csv'))
            X = df.drop('ev_energy_demand', axis=1)
            y = df['ev_energy_demand']
            for col in X.select_dtypes(include='object').columns:
                X[col] = LabelEncoder().fit_transform(X[col])
            model = RandomForestClassifier()
            model.fit(X, y)
            prediction = model.predict(X_input)[0]
        except Exception as e:
            prediction = f"Error: {e}"
    return render(request, 'prediction/predict.html', {'prediction': prediction})