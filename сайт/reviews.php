<?php
header('Content-Type: application/json; charset=utf-8');
$file = 'reviews.json';

// Если файл еще не создан, создаем пустой список
if (!file_exists($file)) {
    file_put_contents($file, '[]');
}

// Если пришел новый отзыв (POST-запрос) — сохраняем его в файл
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if ($input) {
        $reviews = json_decode(file_get_contents($file), true);
        // Добавляем новый отзыв в начало списка (с защитой от вредоносного кода)
        array_unshift($reviews, [
            'author'  => htmlspecialchars($input['author']),
            'bouquet' => htmlspecialchars($input['bouquet']),
            'rating'  => htmlspecialchars($input['rating']),
            'text'    => htmlspecialchars($input['text'])
        ]);
        // Записываем обратно в файл красивым текстом
        file_put_contents($file, json_encode($reviews, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
    echo json_encode(['status' => 'ok']);
    exit;
}

// Если сайт просто запрашивает список отзывов (GET-запрос) — отдаем содержимое файла
echo file_get_contents($file);
?>
