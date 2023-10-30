import concurrent.futures
import requests
import time
import psutil


def send_request(url):
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    return response, end_time - start_time


if __name__ == '__main__':
    num_requests = 3000
    base_url = 'http://localhost:8000/api/data'  # Замените на URL вашего API

    response_times = []
    cpu_percentages = []
    memory_usages = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(send_request, base_url) for _ in range(num_requests)]

    for future in concurrent.futures.as_completed(futures):
        response, request_time = future.result()
        response_times.append(request_time)

        if response.status_code == 200:
            # Измерение загрузки процессора и использования памяти
            cpu_percent = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            cpu_percentages.append(cpu_percent)
            memory_usages.append(memory_usage)

    average_time = sum(response_times) / num_requests
    average_cpu = sum(cpu_percentages) / num_requests
    peak_cpu = max(cpu_percentages)
    average_memory = sum(memory_usages) / num_requests
    peak_memory = max(memory_usages)

    print(f"Среднее время обработки запроса: {average_time:.4f} секунд")
    print(f"Средняя загрузка процессора: {cpu_percentages}%")
    print(f"Пиковая загрузка процессора: {peak_cpu:.2f}%")
    print(f"Среднее использование оперативной памяти: {average_memory:.2f}%")
    print(f"Пиковое использование оперативной памяти: {peak_memory:.2f}%")
