// Функция прокрутки к текущему ученику в рейтинге
function scrollToMyPosition() {
    const currentRow = document.querySelector('.current-student');
    if (currentRow) {
        currentRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Добавляем эффект мигания
        currentRow.style.animation = 'highlight 1s ease-in-out';
        setTimeout(() => {
            currentRow.style.animation = '';
        }, 1000);
    }
}

