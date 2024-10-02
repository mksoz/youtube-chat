import os 
import yaml
import matplotlib.pyplot as plt
import requests
import datetime

# Obtener la ruta del directorio donde se encuentra el archivo Python actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construir la ruta completa al archivo config.yaml
config_path = os.path.join(current_dir, "config.yaml")

def load_config():
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

def plot_sentiment_pie(sentiment_scores):
    labels = ['Positive', 'Neutral', 'Negative']
    sizes = [sentiment_scores['positive'], sentiment_scores['neutral'], sentiment_scores['negative']]
    colors = ['green', 'gray', 'red']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Para que el gráfico sea un círculo en vez de un óvalo

    # Cambiar el color de las etiquetas
    plt.setp(ax.texts, color='white')
    
    fig.patch.set_alpha(0)  # Hacer el fondo del gráfico transparente

    return fig

def get_avatar(sender_type):
    if sender_type == "human":
        return config['user_path']
    else:
       return config['bot_path']

def format_duration(duration_in_seconds):
    if isinstance(duration_in_seconds, (int, float)):
        hours, remainder = divmod(int(duration_in_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return str(duration_in_seconds)