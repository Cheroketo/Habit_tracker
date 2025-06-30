import matplotlib.pyplot as plt
from models.feelings import get_feelings_by_user

def generate_mood_graph(user_id: int):
    data = get_feelings_by_user(user_id)
    dates = [d["log_date"] for d in data]
    moods = [d["mood"] for d in data]

    plt.figure()
    plt.plot(dates, moods, marker="o")
    plt.title("Настроение по дням")
    plt.xlabel("Дата")
    plt.ylabel("Настроение")

    filename = f"moodchart_{user_id}.png"
    plt.savefig(filename)
    return filename
