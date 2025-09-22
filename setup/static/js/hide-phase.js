document.addEventListener('DOMContentLoaded', function() {
    const hidePhaseColumn = document.getElementById('hidePhaseColumn');
    if (hidePhaseColumn) {
        const table = document.querySelector('#jogos-tab table');
        if (table) {
            table.classList.add('hide-phase');
        }
    }
})
