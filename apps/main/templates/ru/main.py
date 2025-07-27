import requests
from datetime import datetime, timedelta

# Твой токен от Todoist
API_TOKEN = "089bfad3df4c8a218d45aa21c68086f64a90e2db"

# Заголовки
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Завтрашняя дата в формате YYYY-MM-DD
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Получаем все задачи
response = requests.get("https://api.todoist.com/rest/v2/tasks", headers=headers)

# Фильтруем задачи на завтра
if response.status_code == 200:
    tasks = response.json()
    print(f"📅 Задачи на {tomorrow}:")
    for task in tasks:
        due = task.get("due")
        if due and due.get("date", "").startswith(tomorrow):
            print(f"- {task['content']}")
else:
    print("Ошибка при запросе:", response.status_code, response.text)
