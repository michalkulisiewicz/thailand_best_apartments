import json

initial_cache = {
    "Patong, Kathu, Phuket": [7.9039, 98.2970],
    "Rawai, Muang Phuket, Phuket": [7.7781, 98.3307],
    "Chalong, Muang Phuket, Phuket": [7.8484, 98.3319],
    "Kathu, Phuket": [7.9191, 98.3332],
    "Ratsada, Muang Phuket, Phuket": [7.8805, 98.4007],
    "Mai Khao, Thalang, Phuket": [8.1797, 98.3031],
    "Kammala, Kathu, Phuket": [7.9705, 98.2834],
    "Choeng Thale, Thalang, Phuket": [7.9862, 98.2978],
    "Wichit, Muang Phuket, Phuket": [7.8766, 98.3858],
    "Karon, Muang Phuket, Phuket": [7.8429, 98.2947],
    "Sa Khu, Thalang, Phuket": [8.0891, 98.3069],
    "Pa Khlok, Thalang, Phuket": [8.0606, 98.4139],
    "Thep Krasattri, Thalang, Phuket": [8.0224, 98.3492]
}

with open('location_cache.json', 'w', encoding='utf-8') as f:
    json.dump(initial_cache, f, ensure_ascii=False, indent=2) 
