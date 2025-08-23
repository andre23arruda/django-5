document.addEventListener('DOMContentLoaded', function() {
    const hidePhase = document.getElementById('hidePhase');
    if (hidePhase) {
        const table = document.querySelector('#jogos-tab table');
        if (table) {
            table.classList.add('hide-phase');
        }
    }
})
